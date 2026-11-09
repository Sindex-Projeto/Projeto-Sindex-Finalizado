from model import repositorio as repositorio_model
from services.erros import ErroServico


# Listar repositórios do usuário (pessoal ou corporativo)
def execute(usuario_id, tipo=None):
    if tipo and tipo not in repositorio_model.TIPOS:
        raise ErroServico("Tipo de repositório inválido.")

    repositorios = repositorio_model.listar_do_usuario(usuario_id, tipo)

    return [repo.to_dict(papel) for repo, papel in repositorios]
