import json
import re
import urllib.error
import urllib.request

from services.erros import ErroServico
from services.ia import config

# Resposta quando a IA não consegue analisar o conteúdo
FALHA_ANALISE = "A IA não conseguiu analisar este arquivo."


# Envia uma requisição ao Gemini e devolve o JSON da resposta
def _chamar(caminho, corpo):
    if not config.configurada():
        raise ErroServico("A IA não está configurada no servidor.", 503)

    requisicao = urllib.request.Request(
        f"{config.url_base()}/{caminho}",
        data=json.dumps(corpo).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": config.chave(),
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(requisicao, timeout=config.tempo_limite()) as resposta:
            return json.loads(resposta.read().decode("utf-8"))
    except urllib.error.HTTPError as erro:
        raise _erro_http(erro.code)
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ErroServico("Não foi possível falar com a IA. Tente de novo.", 502)
    except ValueError:
        raise ErroServico("A IA devolveu uma resposta inválida.", 502)


# Traduz o erro do Google em uma mensagem simples (sem vazar a chave)
def _erro_http(codigo):
    if codigo in (401, 403):
        return ErroServico("A chave da IA é inválida ou sem permissão.", 502)
    if codigo == 404:
        return ErroServico("Modelo de IA não encontrado. Ajuste GEMINI_MODELO.", 502)
    if codigo == 429:
        return ErroServico("O limite gratuito da IA foi atingido. Tente mais tarde.", 429)
    return ErroServico("A IA está indisponível no momento. Tente de novo.", 502)


# Pede uma resposta em JSON ao modelo
def gerar_json(instrucao, texto):
    corpo = {
        "systemInstruction": {"parts": [{"text": instrucao}]},
        "contents": [{"role": "user", "parts": [{"text": texto}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
    }

    dados = _chamar(f"models/{config.modelo()}:generateContent", corpo)

    try:
        partes = dados["candidates"][0]["content"]["parts"]
        bruto = "".join(p.get("text", "") for p in partes)
    except (KeyError, IndexError, TypeError):
        raise ErroServico(FALHA_ANALISE, 502)

    resultado = _ler_json(bruto)

    if not isinstance(resultado, dict):
        raise ErroServico(FALHA_ANALISE, 502)

    return resultado


# Aceita JSON puro ou dentro de ``` ```
def _ler_json(bruto):
    bruto = (bruto or "").strip()
    bruto = re.sub(r"^```(?:json)?\s*|\s*```$", "", bruto, flags=re.IGNORECASE)

    try:
        return json.loads(bruto)
    except ValueError:
        pass

    inicio, fim = bruto.find("{"), bruto.rfind("}")

    if inicio != -1 and fim > inicio:
        try:
            return json.loads(bruto[inicio:fim + 1])
        except ValueError:
            return None

    return None


# Gera o vetor de significado de um texto
# tarefa: "RETRIEVAL_DOCUMENT" (arquivos) ou "RETRIEVAL_QUERY" (busca)
def gerar_embedding(texto, tarefa):
    modelo = config.modelo_embedding()

    corpo = {
        "model": f"models/{modelo}",
        "content": {"parts": [{"text": texto}]},
        "taskType": tarefa,
        "outputDimensionality": config.dimensoes(),
    }

    dados = _chamar(f"models/{modelo}:embedContent", corpo)

    try:
        valores = [float(v) for v in dados["embedding"]["values"]]
    except (KeyError, TypeError, ValueError):
        raise ErroServico("A IA devolveu uma resposta inválida.", 502)

    if not valores:
        raise ErroServico("A IA devolveu uma resposta inválida.", 502)

    return valores
