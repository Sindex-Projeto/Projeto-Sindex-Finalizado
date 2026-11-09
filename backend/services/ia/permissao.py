from model.usuario import buscar_por_id
from services.erros import ErroServico
from services.ia import config


# Confere se o usuário ligou a IA e se o servidor tem a chave
def exigir_ia(usuario_id):
    usuario = buscar_por_id(usuario_id)

    if usuario is None or not usuario.ia_ativa:
        raise ErroServico("A IA está desativada nas suas configurações.", 403)

    if not config.configurada():
        raise ErroServico("A IA não está configurada no servidor.", 503)
