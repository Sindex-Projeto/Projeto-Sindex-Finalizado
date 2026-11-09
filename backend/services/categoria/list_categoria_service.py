from model import categoria as categoria_model
from services.permissoes import exigir_papel


# Listar categorias do repositório
def execute(usuario_id, repositorio_id):
    exigir_papel(usuario_id, repositorio_id, "leitor")

    return categoria_model.listar_do_repositorio(repositorio_id)
