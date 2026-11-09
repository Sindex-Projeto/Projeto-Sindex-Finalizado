from database import db
from model import repositorio as repositorio_model
from services.erros import ErroServico


# Criar repositório corporativo (quem cria vira o dono)
def execute(usuario_id, nome):
    if not isinstance(nome, str) or not nome.strip():
        raise ErroServico("Informe o nome do repositório.")

    nome = nome.strip()

    if len(nome) > 100:
        raise ErroServico("O nome pode ter no máximo 100 caracteres.")

    repositorio = repositorio_model.novo(nome, "corporativo", usuario_id)
    db.session.commit()

    return repositorio.to_dict("dono")
