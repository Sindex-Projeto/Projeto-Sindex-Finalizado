import os

from database import db
from model.arquivo import buscar_por_id
from services.erros import ErroServico
from services.permissoes import exigir_papel


# Excluir arquivo
def execute(usuario_id, arquivo_id, pasta_base):
    arquivo = buscar_por_id(arquivo_id)

    if arquivo is None:
        raise ErroServico("Arquivo não encontrado.", 404)

    # Só editor ou dono exclui
    exigir_papel(usuario_id, arquivo.repositorio_id, "editor")

    caminho = None
    if arquivo.tipo == "arquivo" and arquivo.nome_armazenado:
        caminho = os.path.join(pasta_base, str(arquivo.repositorio_id), arquivo.nome_armazenado)

    # Apaga do banco e depois do disco
    db.session.delete(arquivo)
    db.session.commit()

    if caminho:
        try:
            os.remove(caminho)
        except OSError:
            pass
