from database import db
from model import categoria as categoria_model
from model.arquivo import buscar_por_id
from services.erros import ErroServico
from services.pasta.validar_pasta import validar_destino
from services.permissoes import exigir_papel


# Editar arquivo: só muda o que veio em "dados"
def execute(usuario_id, arquivo_id, dados):
    arquivo = buscar_por_id(arquivo_id)

    if arquivo is None:
        raise ErroServico("Arquivo não encontrado.", 404)

    exigir_papel(usuario_id, arquivo.repositorio_id, "editor")

    # Nome
    if "nome" in dados:
        nome = dados["nome"]

        if not isinstance(nome, str) or not nome.strip():
            raise ErroServico("Nome inválido.")

        arquivo.nome = nome.strip()[:255]

    # Categoria (tem que ser do mesmo repositório)
    if "categoria_id" in dados:
        categoria_id = dados["categoria_id"]

        if categoria_id is None:
            arquivo.categoria_id = None
        else:
            if isinstance(categoria_id, bool) or not isinstance(categoria_id, int):
                raise ErroServico("Categoria inválida.")

            categoria = categoria_model.buscar_por_id(categoria_id)

            if categoria is None or categoria.repositorio_id != arquivo.repositorio_id:
                raise ErroServico("Categoria inválida.")

            arquivo.categoria_id = categoria.id

    # Pasta
    if "pasta_id" in dados:
        arquivo.pasta_id = validar_destino(dados["pasta_id"], arquivo.repositorio_id)

    db.session.commit()

    return arquivo
