import os

from model.arquivo import buscar_por_id
from services.erros import ErroServico
from services.permissoes import exigir_papel


# Prepara o download de um arquivo
def execute(usuario_id, arquivo_id, pasta_base):
    arquivo = buscar_por_id(arquivo_id)

    if arquivo is None:
        raise ErroServico("Arquivo não encontrado.", 404)

    # Qualquer membro pode baixar
    exigir_papel(usuario_id, arquivo.repositorio_id, "leitor")

    if arquivo.tipo != "arquivo":
        raise ErroServico("Links não têm arquivo para baixar.")

    pasta = os.path.join(pasta_base, str(arquivo.repositorio_id))

    if not os.path.exists(os.path.join(pasta, arquivo.nome_armazenado)):
        raise ErroServico("O arquivo não está mais disponível no servidor.", 404)

    return arquivo, pasta
