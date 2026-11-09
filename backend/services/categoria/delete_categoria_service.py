from database import db
from model import arquivo as arquivo_model
from model import categoria as categoria_model
from services.erros import ErroServico
from services.permissoes import exigir_papel


# Apagar categoria (os arquivos ficam sem categoria)
def execute(usuario_id, categoria_id):
    categoria = categoria_model.buscar_por_id(categoria_id)

    if categoria is None:
        raise ErroServico("Categoria não encontrada.", 404)

    exigir_papel(usuario_id, categoria.repositorio_id, "editor")

    arquivo_model.desvincular_categoria(categoria.id)
    db.session.delete(categoria)
    db.session.commit()
