from database import db
from model import repositorio as repositorio_model
from model import usuario as usuario_model
from services.erros import ErroServico
from services.permissoes import exigir_papel

# Papéis que o dono pode dar
PAPEIS_CONVIDADOS = ("editor", "leitor")


# Convidar membro ou mudar o papel dele (só o dono)
def execute(usuario_id, repositorio_id, email, papel):
    exigir_papel(usuario_id, repositorio_id, "dono")

    repositorio = repositorio_model.buscar_por_id(repositorio_id)

    if repositorio.tipo != "corporativo":
        raise ErroServico("Repositórios pessoais não têm outros membros.")

    if papel not in PAPEIS_CONVIDADOS:
        raise ErroServico("O papel deve ser 'editor' ou 'leitor'.")

    if not isinstance(email, str) or not email.strip():
        raise ErroServico("Informe o e-mail do membro.")

    # Quem é convidado precisa já ter conta
    alvo = usuario_model.buscar_por_email(email.strip().lower())

    if alvo is None:
        raise ErroServico("Nenhum usuário encontrado com esse e-mail.", 404)

    if alvo.id == repositorio.dono_id:
        raise ErroServico("O dono do repositório não pode ter o papel alterado.")

    repositorio_model.definir_membro(alvo.id, repositorio_id, papel)
    db.session.commit()

    return {"usuario": alvo.to_dict(), "papel": papel}
