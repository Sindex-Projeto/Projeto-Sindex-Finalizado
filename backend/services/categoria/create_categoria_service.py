from sqlalchemy.exc import IntegrityError

from database import db
from model import categoria as categoria_model
from model.categoria import Categoria
from services.erros import ErroServico
from services.permissoes import exigir_papel


# Criar categoria
def execute(usuario_id, repositorio_id, nome, descricao=None):
    exigir_papel(usuario_id, repositorio_id, "editor")

    # Valida nome e descrição
    if not isinstance(nome, str) or not nome.strip():
        raise ErroServico("Informe o nome da categoria.")

    nome = nome.strip()

    if len(nome) > 100:
        raise ErroServico("O nome pode ter no máximo 100 caracteres.")

    if descricao is not None and not isinstance(descricao, str):
        raise ErroServico("Descrição inválida.")

    if categoria_model.buscar_por_nome(repositorio_id, nome):
        raise ErroServico("Já existe uma categoria com esse nome.", 409)

    # Salva (o banco também impede nomes repetidos)
    categoria = Categoria(
        nome=nome, descricao=(descricao or "").strip() or None, repositorio_id=repositorio_id
    )

    try:
        db.session.add(categoria)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ErroServico("Já existe uma categoria com esse nome.", 409)

    return categoria
