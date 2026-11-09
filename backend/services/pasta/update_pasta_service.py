from database import db
from model import pasta as pasta_model
from services.erros import ErroServico
from services.pasta import arvore
from services.pasta.validar_pasta import validar_destino
from services.permissoes import exigir_papel


# Renomear e/ou mover pasta
def execute(usuario_id, pasta_id, dados):
    pasta = pasta_model.buscar_por_id(pasta_id)

    if pasta is None:
        raise ErroServico("Pasta não encontrada.", 404)

    exigir_papel(usuario_id, pasta.repositorio_id, "editor")

    pastas = pasta_model.listar_do_repositorio(pasta.repositorio_id)
    mapa = arvore.por_id(pastas)
    filhos = arvore.filhos_por_pai(pastas)

    # Nome novo e pasta de destino
    novo_nome = arvore.validar_nome(dados["nome"]) if "nome" in dados else pasta.nome
    novo_pai = pasta.pasta_pai_id

    if "pasta_pai_id" in dados:
        novo_pai = validar_destino(dados["pasta_pai_id"], pasta.repositorio_id)

        if novo_pai is not None:
            # Não pode entrar nela mesma nem numa subpasta dela
            if novo_pai == pasta.id or novo_pai in arvore.ids_descendentes(pasta, filhos):
                raise ErroServico("Não dá para mover uma pasta para dentro dela mesma.")

            # Respeita o limite de níveis
            niveis_depois = arvore.nivel(mapa[novo_pai], mapa) + 1 + arvore.altura(pasta, filhos)

            if niveis_depois > arvore.MAX_NIVEIS:
                raise ErroServico(f"O limite é de {arvore.MAX_NIVEIS} níveis de pastas.")

    # Nome repetido no destino
    if arvore.nome_em_uso(filhos, novo_pai, novo_nome, ignorar_id=pasta.id):
        raise ErroServico("Já existe uma pasta com esse nome no destino.", 409)

    pasta.nome = novo_nome
    pasta.pasta_pai_id = novo_pai
    db.session.commit()

    return pasta
