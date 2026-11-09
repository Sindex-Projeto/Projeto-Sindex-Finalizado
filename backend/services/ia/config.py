import os

# Leitura das configurações da IA (.env), feita na hora do uso
MODELO_PADRAO = "gemini-3.5-flash-lite"
EMBEDDING_PADRAO = "gemini-embedding-001"
URL_PADRAO = "https://generativelanguage.googleapis.com/v1beta"


def chave():
    return (os.getenv("GEMINI_API_KEY") or "").strip()


def configurada():
    return bool(chave())


def modelo():
    return (os.getenv("GEMINI_MODELO") or MODELO_PADRAO).strip()


def modelo_embedding():
    return (os.getenv("GEMINI_MODELO_EMBEDDING") or EMBEDDING_PADRAO).strip()


def url_base():
    return (os.getenv("GEMINI_URL_BASE") or URL_PADRAO).strip().rstrip("/")


def _inteiro(nome, padrao):
    try:
        return int(os.getenv(nome) or padrao)
    except ValueError:
        return padrao


def dimensoes():
    return _inteiro("GEMINI_DIMENSOES", 768)


def tempo_limite():
    return _inteiro("GEMINI_TIMEOUT", 30)


def pontuacao_minima():
    try:
        return float(os.getenv("BUSCA_SEMANTICA_MINIMO") or 0.45)
    except ValueError:
        return 0.45
