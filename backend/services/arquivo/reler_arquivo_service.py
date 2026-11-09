from model.arquivo import buscar_por_id
from services.erros import ErroServico
from services.extracao.executar import processar
from services.permissoes import exigir_papel


# Ler o conteúdo de novo (quando a leitura falhou)
def execute(usuario_id, arquivo_id, pasta_base):
    arquivo = buscar_por_id(arquivo_id)

    if arquivo is None:
        raise ErroServico("Arquivo não encontrado.", 404)

    exigir_papel(usuario_id, arquivo.repositorio_id, "editor")

    return processar(arquivo, pasta_base)
