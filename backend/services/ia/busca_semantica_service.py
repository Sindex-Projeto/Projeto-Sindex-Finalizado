from model import embedding as embedding_model
from model.arquivo import buscar_por_id
from repository import arquivo_repository
from services.erros import ErroServico
from services.ia import config, gemini, vetores
from services.ia.permissao import exigir_ia
from services.permissoes import exigir_papel

# Quantos arquivos novos são indexados por busca (para não demorar)
LOTE_INDEXACAO = 10
MAX_RESULTADOS = 20
MAX_CONSULTA = 200


# Gera e guarda o vetor de um arquivo
def indexar_arquivo(arquivo):
    texto = vetores.texto_do_arquivo(arquivo.nome, arquivo.texto_extraido)
    vetor = gemini.gerar_embedding(texto, "RETRIEVAL_DOCUMENT")
    embedding_model.salvar(arquivo.id, config.modelo_embedding(), vetores.serializar(vetor))


# Busca por significado: acha arquivos parecidos com a pergunta
def execute(usuario_id, repositorio_id, consulta):
    exigir_papel(usuario_id, repositorio_id, "leitor")
    exigir_ia(usuario_id)

    if not isinstance(consulta, str) or not consulta.strip():
        raise ErroServico("Digite o que você procura.")

    consulta = consulta.strip()

    if len(consulta) > MAX_CONSULTA:
        raise ErroServico(f"A busca pode ter no máximo {MAX_CONSULTA} caracteres.")

    modelo = config.modelo_embedding()

    # Indexa alguns arquivos que ainda não têm vetor
    for arquivo_id in arquivo_repository.ids_sem_vetor(repositorio_id, modelo, LOTE_INDEXACAO):
        arquivo = buscar_por_id(arquivo_id)
        if arquivo is None:
            continue

        try:
            indexar_arquivo(arquivo)
        except ErroServico:
            break

    # Compara a pergunta com os vetores
    vetor_consulta = gemini.gerar_embedding(consulta, "RETRIEVAL_QUERY")

    itens = []
    for linha in arquivo_repository.vetores_do_repositorio(repositorio_id, modelo):
        vetor = vetores.ler(linha["vetor"])
        if vetor:
            itens.append({"id": linha["id"], "vetor": vetor})

    ranking = vetores.ranquear(vetor_consulta, itens, config.pontuacao_minima(), MAX_RESULTADOS)
    pontos = dict(ranking)

    arquivos = arquivo_repository.filtrar(repositorio_id, ids=[i for i, _ in ranking])
    arquivos.sort(key=lambda a: pontos[a["id"]], reverse=True)

    for arquivo in arquivos:
        arquivo["pontuacao"] = round(pontos[arquivo["id"]], 3)

    return {
        "resultados": arquivos,
        "nao_indexados": arquivo_repository.contar_sem_vetor(repositorio_id, modelo),
    }
