from model import pasta as pasta_model
from services.erros import ErroServico


# Confere se a pasta existe e é deste repositório (None = raiz)
def validar_destino(pasta_id, repositorio_id):
    if pasta_id is None:
        return None

    if isinstance(pasta_id, bool) or not isinstance(pasta_id, int):
        raise ErroServico("Pasta inválida.")

    pasta = pasta_model.buscar_por_id(pasta_id)

    if pasta is None or pasta.repositorio_id != repositorio_id:
        raise ErroServico("Pasta inválida.")

    return pasta.id
