from database import db
from model import categoria as categoria_model
from model import pasta as pasta_model
from model.arquivo import STATUS_EXTRAIDO, STATUS_PROCESSADO, buscar_por_id
from model.sugestao import SugestaoIA, buscar_do_arquivo
from repository import arquivo_repository
from services.erros import ErroServico
from services.ia import config, gemini, sugestao
from services.ia.permissao import exigir_ia
from services.pasta import arvore
from services.permissoes import exigir_papel


# Caminhos das pastas existentes, como tuplas de nomes
def caminhos_das_pastas(pastas):
    mapa = arvore.por_id(pastas)
    caminhos = []

    for pasta in pastas:
        nomes = [pasta.nome]
        atual = pasta

        while atual.pasta_pai_id is not None and len(nomes) <= arvore.MAX_NIVEIS:
            atual = mapa[atual.pasta_pai_id]
            nomes.insert(0, atual.nome)

        caminhos.append(tuple(nomes))

    return caminhos


# Pede à IA uma organização para o arquivo e guarda a sugestão
def execute(usuario_id, arquivo_id):
    arquivo = buscar_por_id(arquivo_id)

    if arquivo is None:
        raise ErroServico("Arquivo não encontrado.", 404)

    exigir_papel(usuario_id, arquivo.repositorio_id, "editor")
    exigir_ia(usuario_id)

    if arquivo.status not in (STATUS_EXTRAIDO, STATUS_PROCESSADO) or not arquivo.texto_extraido:
        raise ErroServico("Este arquivo não tem texto para a IA analisar.")

    # Contexto: categorias e pastas que já existem
    categorias = [c.nome for c in categoria_model.listar_do_repositorio(arquivo.repositorio_id)]
    caminhos = caminhos_das_pastas(pasta_model.listar_do_repositorio(arquivo.repositorio_id))

    texto = sugestao.montar_texto(
        arquivo.nome, arquivo.tipo, arquivo.texto_extraido, categorias, caminhos
    )
    resposta = gemini.gerar_json(sugestao.INSTRUCAO, texto)

    final = sugestao.interpretar(resposta, categorias, caminhos)

    if final is None:
        raise ErroServico("A IA não conseguiu sugerir uma organização para este arquivo.", 502)

    # Guarda (troca a sugestão anterior, se houver)
    atual = buscar_do_arquivo(arquivo.id)

    if atual is None:
        atual = SugestaoIA(arquivo_id=arquivo.id)
        db.session.add(atual)

    atual.categoria = final["categoria"]
    atual.pasta = final["pasta"]
    atual.motivo = final["motivo"]
    atual.modelo = config.modelo()

    db.session.commit()

    return arquivo_repository.filtrar(arquivo.repositorio_id, ids=[arquivo.id])[0]
