from sqlalchemy.exc import IntegrityError

from database import db
from model import categoria as categoria_model
from model import pasta as pasta_model
from model.arquivo import STATUS_PROCESSADO, buscar_por_id
from model.categoria import Categoria
from model.pasta import Pasta
from model.sugestao import buscar_do_arquivo
from repository import arquivo_repository
from repository.texto import sem_acento
from services.erros import ErroServico
from services.ia import sugestao
from services.pasta import arvore
from services.permissoes import exigir_papel


# Procura (sem diferenciar maiúscula/acento) ou cria a categoria
def _resolver_categoria(repositorio_id, nome):
    for existente in categoria_model.listar_do_repositorio(repositorio_id):
        if sem_acento(existente.nome) == sem_acento(nome):
            return existente, False

    nova = Categoria(nome=nome, repositorio_id=repositorio_id)
    db.session.add(nova)
    db.session.flush()
    return nova, True


# Percorre o caminho criando as pastas que faltam
def _resolver_pastas(repositorio_id, niveis):
    filhos = arvore.filhos_por_pai(pasta_model.listar_do_repositorio(repositorio_id))
    pai_id = None
    criadas = []

    for nome in niveis:
        nome = arvore.validar_nome(nome)
        encontrada = next(
            (p for p in filhos.get(pai_id, []) if sem_acento(p.nome) == sem_acento(nome)), None
        )

        if encontrada is None:
            encontrada = Pasta(nome=nome, pasta_pai_id=pai_id, repositorio_id=repositorio_id)
            db.session.add(encontrada)
            db.session.flush()
            filhos.setdefault(pai_id, []).append(encontrada)
            criadas.append(nome)

        pai_id = encontrada.id

    return pai_id, criadas


# Aplica a sugestão: cria categoria/pastas se precisar e move o arquivo
def execute(usuario_id, arquivo_id):
    arquivo = buscar_por_id(arquivo_id)

    if arquivo is None:
        raise ErroServico("Arquivo não encontrado.", 404)

    exigir_papel(usuario_id, arquivo.repositorio_id, "editor")

    pendente = buscar_do_arquivo(arquivo.id)

    if pendente is None:
        raise ErroServico("Não há sugestão para este arquivo.", 404)

    criadas = {"categoria": None, "pastas": []}

    try:
        if pendente.categoria:
            categoria, nova = _resolver_categoria(arquivo.repositorio_id, pendente.categoria)
            arquivo.categoria_id = categoria.id
            criadas["categoria"] = categoria.nome if nova else None

        niveis = sugestao.niveis_da_pasta(pendente.pasta)

        if niveis:
            arquivo.pasta_id, criadas["pastas"] = _resolver_pastas(arquivo.repositorio_id, niveis)

        arquivo.status = STATUS_PROCESSADO
        db.session.delete(pendente)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ErroServico("Não foi possível aplicar: já existe um item com esse nome.", 409)
    except ErroServico:
        db.session.rollback()
        raise

    return {
        "arquivo": arquivo_repository.filtrar(arquivo.repositorio_id, ids=[arquivo.id])[0],
        "criadas": criadas,
    }
