import http.client
import ipaddress
import re
import socket
import ssl
import time
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from services.extracao.arquivos import LIMITE_CARACTERES, limpar_texto
from services.extracao.erros import ErroExtracao

# Limites ao abrir links
TEMPO_LIMITE_TOTAL = 20
TEMPO_LIMITE_CONEXAO = 10
LIMITE_BYTES = 2 * 1024 * 1024
MAX_REDIRECIONAMENTOS = 3
PORTAS_PERMITIDAS = {80, 443}
TIPOS_ACEITOS = {"text/html", "application/xhtml+xml", "text/plain"}
USER_AGENT = "Sindex/1.0 (leitor de links)"


# Falha ao ler um link
class ErroLink(ErroExtracao):
    pass


# Só aceita IPs públicos (bloqueia localhost e redes internas)
def _ip_permitido(endereco):
    ip = ipaddress.ip_address(endereco)

    if ip.version == 6:
        if ip.ipv4_mapped is not None:
            ip = ip.ipv4_mapped
        elif ip.sixtofour is not None:
            ip = ip.sixtofour
        elif ip.teredo is not None:
            return False

    return ip.is_global and not ip.is_multicast


# Descobre o IP do site e confere se é permitido
def _resolver(host, porta):
    try:
        resultados = socket.getaddrinfo(host, porta, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise ErroLink("Não foi possível encontrar esse endereço na internet.")

    enderecos = []
    for _familia, _tipo, _proto, _nome, sockaddr in resultados:
        endereco = sockaddr[0].split("%")[0]
        if endereco not in enderecos:
            enderecos.append(endereco)

    if not enderecos:
        raise ErroLink("Não foi possível encontrar esse endereço na internet.")

    if not all(_ip_permitido(endereco) for endereco in enderecos):
        raise ErroLink("Esse endereço não é permitido (aponta para uma rede interna).")

    return enderecos[0]


# Conexões que usam o IP já conferido (evita troca de endereço no meio)
class _ConexaoHTTP(http.client.HTTPConnection):
    def __init__(self, host, porta, ip):
        super().__init__(host, porta, timeout=TEMPO_LIMITE_CONEXAO)
        self._ip = ip

    def connect(self):
        self.sock = socket.create_connection((self._ip, self.port), self.timeout)


class _ConexaoHTTPS(http.client.HTTPSConnection):
    def __init__(self, host, porta, ip):
        super().__init__(
            host, porta, timeout=TEMPO_LIMITE_CONEXAO, context=ssl.create_default_context()
        )
        self._ip = ip

    def connect(self):
        sock = socket.create_connection((self._ip, self.port), self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


# Baixa a página, seguindo poucos redirecionamentos e conferindo cada um
def _baixar(url):
    inicio = time.monotonic()

    for _ in range(MAX_REDIRECIONAMENTOS + 1):
        partes = urlparse(url)

        # Confere o endereço e a porta
        if partes.scheme not in ("http", "https") or not partes.hostname:
            raise ErroLink("O link precisa começar com http:// ou https://.")

        if partes.username or partes.password:
            raise ErroLink("Links com usuário e senha não são permitidos.")

        try:
            porta = partes.port or (443 if partes.scheme == "https" else 80)
        except ValueError:
            raise ErroLink("O link tem uma porta inválida.")

        if porta not in PORTAS_PERMITIDAS:
            raise ErroLink("Só são aceitos links nas portas padrão (80 e 443).")

        host = partes.hostname
        ip = _resolver(host, porta)

        classe = _ConexaoHTTPS if partes.scheme == "https" else _ConexaoHTTP
        conexao = classe(host, porta, ip)

        try:
            caminho = (partes.path or "/") + (f"?{partes.query}" if partes.query else "")
            padrao = 443 if partes.scheme == "https" else 80
            cabecalho_host = host if porta == padrao else f"{host}:{porta}"

            conexao.request("GET", caminho, headers={
                "Host": cabecalho_host,
                "User-Agent": USER_AGENT,
                "Accept": "text/html,text/plain;q=0.9,*/*;q=0.1",
                "Accept-Encoding": "identity",
            })
            resposta = conexao.getresponse()

            if resposta.status in (301, 302, 303, 307, 308):
                destino = resposta.getheader("Location")
                if not destino:
                    raise ErroLink("O site redirecionou sem informar para onde.")
                url = urljoin(url, destino)
                continue

            if resposta.status != 200:
                raise ErroLink(f"O site respondeu com erro {resposta.status}.")

            # Só aceita páginas de texto
            cabecalho_tipo = resposta.getheader("Content-Type", "")
            tipo = cabecalho_tipo.split(";")[0].strip().lower()

            if tipo not in TIPOS_ACEITOS:
                raise ErroLink("Este link não é uma página de texto (pode ser um arquivo, imagem ou vídeo).")

            charset = None
            achou = re.search(r"charset=([\w\-]+)", cabecalho_tipo, re.IGNORECASE)
            if achou:
                charset = achou.group(1)

            # Lê no máximo o tamanho e o tempo permitidos
            dados = bytearray()

            while len(dados) < LIMITE_BYTES:
                if time.monotonic() - inicio > TEMPO_LIMITE_TOTAL:
                    raise ErroLink("O site demorou demais para responder.")

                pedaco = resposta.read(min(65536, LIMITE_BYTES - len(dados)))

                if not pedaco:
                    break

                dados.extend(pedaco)

            return url, tipo, bytes(dados), charset
        except ErroLink:
            raise
        except (OSError, http.client.HTTPException, ssl.SSLError):
            raise ErroLink("Não foi possível acessar o site (sem resposta ou conexão recusada).")
        finally:
            conexao.close()

    raise ErroLink("O link tem redirecionamentos demais.")


# Tira o texto e o título do HTML
class _ExtratorHtml(HTMLParser):
    IGNORAR = {"script", "style", "noscript", "template", "svg", "head", "iframe"}
    QUEBRA = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6",
              "section", "article", "header", "footer", "blockquote", "pre", "table"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.titulo = ""
        self.partes = []
        self._ignorando = 0
        self._no_titulo = False

    def handle_starttag(self, tag, _atributos):
        if tag == "title":
            self._no_titulo = True
        elif tag in self.IGNORAR:
            self._ignorando += 1
        elif tag in self.QUEBRA:
            self.partes.append("\n")

    def handle_endtag(self, tag):
        if tag == "title":
            self._no_titulo = False
        elif tag in self.IGNORAR:
            self._ignorando = max(0, self._ignorando - 1)
        elif tag in self.QUEBRA:
            self.partes.append("\n")

    def handle_data(self, dados):
        if self._no_titulo:
            self.titulo += dados
        elif not self._ignorando:
            self.partes.append(dados)


# Descobre a codificação do texto
def _decodificar(dados, charset_cabecalho):
    candidatos = []

    if charset_cabecalho:
        candidatos.append(charset_cabecalho)

    achou = re.search(rb"<meta[^>]+charset=[\"']?([\w\-]+)", dados[:4096], re.IGNORECASE)
    if achou:
        candidatos.append(achou.group(1).decode("ascii", errors="ignore"))

    candidatos.append("utf-8")

    for nome in candidatos:
        try:
            return dados.decode(nome)
        except (LookupError, UnicodeDecodeError):
            continue

    return dados.decode("utf-8", errors="replace")


# Devolve (título, texto) da página
def extrair_de_link(url):
    _url_final, tipo, dados, charset = _baixar(url)
    conteudo = _decodificar(dados, charset)

    if tipo == "text/plain":
        return "", limpar_texto(conteudo)[:LIMITE_CARACTERES]

    extrator = _ExtratorHtml()

    try:
        extrator.feed(conteudo)
        extrator.close()
    except Exception:
        raise ErroLink("Não foi possível interpretar a página.")

    titulo = re.sub(r"\s+", " ", extrator.titulo).strip()

    linhas = (re.sub(r"[ \t\xa0]+", " ", linha).strip() for linha in "".join(extrator.partes).split("\n"))
    texto = limpar_texto("\n".join(linha for linha in linhas if linha))

    return titulo, texto[:LIMITE_CARACTERES]
