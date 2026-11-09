from model import repositorio as repositorio_model
from services.permissoes import exigir_papel


# Listar membros (qualquer membro vê)
def execute(usuario_id, repositorio_id):
    exigir_papel(usuario_id, repositorio_id, "leitor")

    return [
        {"usuario_id": usuario.id, "nome": usuario.nome, "email": usuario.email, "papel": papel}
        for usuario, papel in repositorio_model.listar_membros(repositorio_id)
    ]
