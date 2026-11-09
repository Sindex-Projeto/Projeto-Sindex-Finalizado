from model import pasta as pasta_model
from services.permissoes import exigir_papel


# Listar pastas do repositório
def execute(usuario_id, repositorio_id):
    exigir_papel(usuario_id, repositorio_id, "leitor")

    return pasta_model.listar_do_repositorio(repositorio_id)
