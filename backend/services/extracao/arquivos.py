import re
import zipfile

from services.extracao.erros import ErroExtracao, TipoSemSuporte

# Limites de leitura
LIMITE_CARACTERES = 500_000
LIMITE_BYTES_TEXTO = LIMITE_CARACTERES * 4
LIMITE_PAGINAS_PDF = 300
LIMITE_DESCOMPACTADO_DOCX = 100 * 1024 * 1024

# Tipos que sabemos ler
EXTENSOES_DE_TEXTO = {"txt", "md", "csv"}
EXTENSOES_SUPORTADAS = EXTENSOES_DE_TEXTO | {"pdf", "docx"}


# Lê o texto de um arquivo conforme o tipo
def extrair(caminho, extensao):
    extensao = (extensao or "").lower()

    if extensao in EXTENSOES_DE_TEXTO:
        texto = _ler_texto_simples(caminho)
    elif extensao == "pdf":
        texto = _ler_pdf(caminho)
    elif extensao == "docx":
        texto = _ler_docx(caminho)
    else:
        raise TipoSemSuporte("Este tipo de arquivo ainda não tem leitura de texto.")

    return limpar_texto(texto)[:LIMITE_CARACTERES]


# Arruma quebras de linha e espaços
def limpar_texto(texto):
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    texto = texto.replace("\x00", "")
    texto = re.sub(r"[ \t]+\n", "\n", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


# TXT, MD e CSV
def _ler_texto_simples(caminho):
    try:
        with open(caminho, "rb") as arquivo:
            dados = arquivo.read(LIMITE_BYTES_TEXTO)
    except OSError:
        raise ErroExtracao("Não foi possível abrir o arquivo.")

    try:
        return dados.decode("utf-8-sig")
    except UnicodeDecodeError as erro:
        if erro.start >= len(dados) - 3:
            return dados[: erro.start].decode("utf-8-sig", errors="ignore")

        return dados.decode("cp1252", errors="replace")


# PDF
def _ler_pdf(caminho):
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ErroExtracao("A biblioteca pypdf não está instalada no servidor.")

    try:
        leitor = PdfReader(caminho)

        if leitor.is_encrypted and not leitor.decrypt(""):
            raise ErroExtracao("PDF protegido por senha.")

        partes = []
        total = 0

        for pagina in leitor.pages[:LIMITE_PAGINAS_PDF]:
            texto = pagina.extract_text() or ""
            partes.append(texto)
            total += len(texto)

            if total >= LIMITE_CARACTERES:
                break

        return "\n\n".join(partes)
    except ErroExtracao:
        raise
    except Exception:
        raise ErroExtracao("Não foi possível ler o PDF (arquivo corrompido ou em formato inesperado).")


# DOCX (parágrafos e tabelas)
def _ler_docx(caminho):
    try:
        from docx import Document
        from docx.table import Table
        from docx.text.paragraph import Paragraph
    except ImportError:
        raise ErroExtracao("A biblioteca python-docx não está instalada no servidor.")

    try:
        # Recusa arquivos que "explodem" ao abrir (zip bomb)
        with zipfile.ZipFile(caminho) as pacote:
            if sum(item.file_size for item in pacote.infolist()) > LIMITE_DESCOMPACTADO_DOCX:
                raise ErroExtracao("O documento é grande demais para ser lido.")

        documento = Document(caminho)
        linhas = []

        for bloco in documento.iter_inner_content():
            if isinstance(bloco, Paragraph):
                linhas.append(bloco.text)
            elif isinstance(bloco, Table):
                for linha in bloco.rows:
                    linhas.append(" | ".join(celula.text.strip() for celula in linha.cells))

        return "\n".join(linhas)
    except ErroExtracao:
        raise
    except Exception:
        raise ErroExtracao("Não foi possível ler o documento (arquivo corrompido ou em formato inesperado).")
