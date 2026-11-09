from services.erros import ErroServico

# Máximo de pastas dentro de pastas
MAX_NIVEIS = 8


# Confere o nome da pasta
def validar_nome(nome):
    if not isinstance(nome, str) or not nome.strip():
        raise ErroServico("Informe o nome da pasta.")

    nome = nome.strip()

    if len(nome) > 100:
        raise ErroServico("O nome da pasta pode ter no máximo 100 caracteres.")

    if "/" in nome or "\\" in nome:
        raise ErroServico("O nome da pasta não pode ter barras (/ ou \\).")

    return nome


# Organiza a lista de pastas em mapas para consulta
def por_id(pastas):
    return {pasta.id: pasta for pasta in pastas}


def filhos_por_pai(pastas):
    filhos = {}
    for pasta in pastas:
        filhos.setdefault(pasta.pasta_pai_id, []).append(pasta)
    return filhos


# Em que nível a pasta está (1 = raiz)
def nivel(pasta, mapa):
    profundidade = 1
    atual = pasta

    while atual.pasta_pai_id is not None and profundidade <= MAX_NIVEIS + 1:
        atual = mapa[atual.pasta_pai_id]
        profundidade += 1

    return profundidade


# Quantos níveis existem abaixo da pasta
def altura(pasta, filhos):
    abaixo = filhos.get(pasta.id, [])
    return 0 if not abaixo else 1 + max(altura(f, filhos) for f in abaixo)


# Todas as subpastas (e as de dentro delas)
def ids_descendentes(pasta, filhos):
    ids = set()
    pilha = [pasta]

    while pilha:
        atual = pilha.pop()
        for filha in filhos.get(atual.id, []):
            ids.add(filha.id)
            pilha.append(filha)

    return ids


# Nomes repetidos na mesma pasta
def nome_em_uso(filhos, pai_id, nome, ignorar_id=None):
    return any(
        irma.id != ignorar_id and irma.nome.lower() == nome.lower()
        for irma in filhos.get(pai_id, [])
    )


def nome_livre(filhos, pai_id, nome, ignorar_id=None):
    if not nome_em_uso(filhos, pai_id, nome, ignorar_id):
        return nome

    contador = 2
    while nome_em_uso(filhos, pai_id, f"{nome} ({contador})", ignorar_id):
        contador += 1

    return f"{nome} ({contador})"
