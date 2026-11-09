from database import db
from model import pasta as pasta_model
from model.pasta import Pasta
from services.erros import ErroServico
from services.pasta import arvore
from services.pasta.validar_pasta import validar_destino
from services.permissoes import exigir_papel


# Criar pasta
def execute(usuario_id, repositorio_id, nome, pasta_pai_id=None):
    exigir_papel(usuario_id, repositorio_id, "editor")

    nome = arvore.validar_nome(nome)
    pasta_pai_id = validar_destino(pasta_pai_id, repositorio_id)

    # Confere o limite de níveis e nome repetido
    pastas = pasta_model.listar_do_repositorio(repositorio_id)
    mapa = arvore.por_id(pastas)
    filhos = arvore.filhos_por_pai(pastas)

    if pasta_pai_id is not None and arvore.nivel(mapa[pasta_pai_id], mapa) + 1 > arvore.MAX_NIVEIS:
        raise ErroServico(f"O limite é de {arvore.MAX_NIVEIS} níveis de pastas.")

    if arvore.nome_em_uso(filhos, pasta_pai_id, nome):
        raise ErroServico("Já existe uma pasta com esse nome aqui.", 409)

    # Salva
    pasta = Pasta(nome=nome, pasta_pai_id=pasta_pai_id, repositorio_id=repositorio_id)
    db.session.add(pasta)
    db.session.commit()

    return pasta
