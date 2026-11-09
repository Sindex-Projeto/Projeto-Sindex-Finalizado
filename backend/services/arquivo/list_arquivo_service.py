from model import arquivo as arquivo_model
from repository import arquivo_repository
from services.erros import ErroServico
from services.permissoes import exigir_papel

TIPOS = ("arquivo", "link")
STATUS = (
    arquivo_model.STATUS_PENDENTE,
    arquivo_model.STATUS_EXTRAIDO,
    arquivo_model.STATUS_SEM_TEXTO,
    arquivo_model.STATUS_FALHOU,
    arquivo_model.STATUS_PROCESSADO,
)


# Aceita "" (sem filtro), "palavra_especial" ou um número inteiro
def _numero_ou_palavra(valor, palavra, mensagem):
    valor = (valor or "").strip()

    if valor == "":
        return None, False

    if valor == palavra:
        return None, True

    if not valor.isdigit():
        raise ErroServico(mensagem)

    return int(valor), False


# Listar arquivos do repositório (com filtros opcionais)
def execute(usuario_id, repositorio_id, filtros=None):
    exigir_papel(usuario_id, repositorio_id, "leitor")

    filtros = filtros or {}

    # Valida o que veio na URL
    nome = (filtros.get("q") or "").strip()
    if len(nome) > 100:
        raise ErroServico("A busca pode ter no máximo 100 caracteres.")

    categoria_id, sem_categoria = _numero_ou_palavra(filtros.get("categoria"), "sem", "Categoria inválida.")
    pasta_id, na_raiz = _numero_ou_palavra(filtros.get("pasta"), "raiz", "Pasta inválida.")

    tipo = (filtros.get("tipo") or "").strip()
    if tipo and tipo not in TIPOS:
        raise ErroServico("Tipo inválido.")

    status = (filtros.get("status") or "").strip()
    if status and status not in STATUS:
        raise ErroServico("Situação inválida.")

    # A busca em si é feita em SQL, na camada Repository
    return arquivo_repository.filtrar(
        repositorio_id,
        nome=nome or None,
        categoria_id=categoria_id,
        sem_categoria=sem_categoria,
        pasta_id=pasta_id,
        na_raiz=na_raiz,
        tipo=tipo or None,
        status=status or None,
    )
