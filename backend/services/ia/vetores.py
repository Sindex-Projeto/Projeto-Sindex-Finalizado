import json
import math

# Quanto do texto vai para o vetor
MAX_CARACTERES = 2000


# Texto usado para representar o arquivo na busca
def texto_do_arquivo(nome, texto):
    return f"{nome}\n{(texto or '')[:MAX_CARACTERES]}".strip()


def serializar(vetor):
    return json.dumps([round(float(v), 6) for v in vetor])


def ler(texto):
    try:
        vetor = json.loads(texto)
        return [float(v) for v in vetor]
    except (ValueError, TypeError):
        return None


# Semelhança entre dois vetores (1 = iguais, 0 = nada a ver)
def cosseno(a, b):
    if not a or not b or len(a) != len(b):
        return 0.0

    produto = sum(x * y for x, y in zip(a, b))
    norma = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))

    return produto / norma if norma else 0.0


# Ordena os itens {"id", "vetor"} pela semelhança com a consulta
def ranquear(consulta, itens, minimo, limite):
    pontuados = []

    for item in itens:
        pontos = cosseno(consulta, item["vetor"])
        if pontos >= minimo:
            pontuados.append((item["id"], pontos))

    pontuados.sort(key=lambda p: p[1], reverse=True)
    return pontuados[:limite]
