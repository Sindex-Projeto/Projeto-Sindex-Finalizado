from database import db
from model.arquivo import buscar_por_id
from model.sugestao import buscar_do_arquivo
from services.erros import ErroServico
from services.permissoes import exigir_papel


# Descarta a sugestão (não muda nada no arquivo)
def execute(usuario_id, arquivo_id):
    arquivo = buscar_por_id(arquivo_id)

    if arquivo is None:
        raise ErroServico("Arquivo não encontrado.", 404)

    exigir_papel(usuario_id, arquivo.repositorio_id, "editor")

    pendente = buscar_do_arquivo(arquivo.id)

    if pendente is not None:
        db.session.delete(pendente)
        db.session.commit()
