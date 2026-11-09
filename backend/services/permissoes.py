from model.repositorio import PAPEIS, buscar_membro
from services.erros import ErroServico


# Confere se o usuário tem o papel mínimo no repositório
def exigir_papel(usuario_id, repositorio_id, minimo="leitor"):
    membro = buscar_membro(usuario_id, repositorio_id)

    # Quem não é membro recebe "não encontrado"
    if membro is None:
        raise ErroServico("Repositório não encontrado.", 404)

    if PAPEIS[membro.papel] < PAPEIS[minimo]:
        raise ErroServico("Você não tem permissão para esta ação.", 403)

    return membro
