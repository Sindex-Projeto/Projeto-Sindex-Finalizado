from database import db
from model.usuario import IDIOMAS, TEMAS
from services.erros import ErroServico
from services.usuario.get_usuario_service import execute as obter


# Salvar configurações (só o que veio em "dados")
def execute(usuario_id, dados):
    usuario = obter(usuario_id)

    # IA ligada ou desligada
    if "ia_ativa" in dados:
        if not isinstance(dados["ia_ativa"], bool):
            raise ErroServico("O campo ia_ativa deve ser verdadeiro ou falso.")
        usuario.ia_ativa = dados["ia_ativa"]

    # Tema claro ou escuro
    if "tema" in dados:
        if dados["tema"] not in TEMAS:
            raise ErroServico("Tema inválido.")
        usuario.tema = dados["tema"]

    # Idioma
    if "idioma" in dados:
        if dados["idioma"] not in IDIOMAS:
            raise ErroServico("Idioma inválido.")
        usuario.idioma = dados["idioma"]

    db.session.commit()
    return usuario
