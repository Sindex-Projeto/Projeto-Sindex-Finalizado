from database import db
from model import repositorio as repositorio_model
from services.erros import ErroServico
from services.permissoes import exigir_papel


# Remover membro (só o dono; o dono não sai)
def execute(usuario_id, repositorio_id, alvo_id):
    exigir_papel(usuario_id, repositorio_id, "dono")

    repositorio = repositorio_model.buscar_por_id(repositorio_id)

    if alvo_id == repositorio.dono_id:
        raise ErroServico("O dono do repositório não pode ser removido.")

    membro = repositorio_model.buscar_membro(alvo_id, repositorio_id)

    if membro is None:
        raise ErroServico("Esse usuário não é membro do repositório.", 404)

    db.session.delete(membro)
    db.session.commit()
