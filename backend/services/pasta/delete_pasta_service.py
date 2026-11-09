from database import db
from model import arquivo as arquivo_model
from model import pasta as pasta_model
from services.erros import ErroServico
from services.pasta import arvore
from services.permissoes import exigir_papel


# Apagar pasta (o conteúdo sobe um nível, nada é excluído)
def execute(usuario_id, pasta_id):
    pasta = pasta_model.buscar_por_id(pasta_id)

    if pasta is None:
        raise ErroServico("Pasta não encontrada.", 404)

    exigir_papel(usuario_id, pasta.repositorio_id, "editor")

    pastas = pasta_model.listar_do_repositorio(pasta.repositorio_id)
    filhos = arvore.filhos_por_pai(pastas)
    destino = pasta.pasta_pai_id

    filhos[destino] = [p for p in filhos.get(destino, []) if p.id != pasta.id]

    # Sobe as subpastas (renomeia se o nome já existir lá em cima)
    for subpasta in sorted(filhos.get(pasta.id, []), key=lambda p: p.nome.lower()):
        subpasta.nome = arvore.nome_livre(filhos, destino, subpasta.nome, ignorar_id=subpasta.id)
        subpasta.pasta_pai_id = destino
        filhos.setdefault(destino, []).append(subpasta)

    # Sobe os arquivos
    arquivo_model.mover_da_pasta(pasta.id, destino)

    db.session.flush()
    db.session.delete(pasta)
    db.session.commit()
