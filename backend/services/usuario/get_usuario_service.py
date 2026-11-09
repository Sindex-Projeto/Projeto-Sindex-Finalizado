from model.usuario import buscar_por_id
from services.erros import ErroServico


# Buscar usuário pelo id
def execute(id):
    usuario = buscar_por_id(id)

    if usuario is None:
        raise ErroServico("Usuário não encontrado.", 404)

    return usuario
