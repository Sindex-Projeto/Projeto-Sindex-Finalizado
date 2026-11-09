from datetime import datetime

from database import db, para_iso
from repository.texto import escapar_like, sem_acento

# Colunas devolvidas (sem o texto extraído, que é grande)
COLUNAS = """
    a.id, a.tipo, a.nome, a.extensao, a.tamanho, a.url, a.status, a.observacao,
    a.repositorio_id, a.usuario_id, a.categoria_id, a.pasta_id, a.criado_em,
    c.nome AS categoria_nome,
    s.categoria AS sugestao_categoria, s.pasta AS sugestao_pasta, s.motivo AS sugestao_motivo
"""


# Monta o SQL e os parâmetros. Os valores nunca entram no texto do SQL, só em :parametros
def montar_consulta(repositorio_id, nome=None, categoria_id=None, sem_categoria=False,
                    pasta_id=None, na_raiz=False, tipo=None, status=None, ids=None):
    sql = f"""
        SELECT {COLUNAS}
        FROM arquivos a
        LEFT JOIN categorias c ON c.id = a.categoria_id
        LEFT JOIN sugestoes_ia s ON s.arquivo_id = a.id
        WHERE a.repositorio_id = :repositorio_id
    """
    parametros = {"repositorio_id": repositorio_id}

    # Filtro 1: pesquisa pelo nome (sem diferenciar maiúsculas nem acentos)
    if nome:
        sql += " AND sem_acento(a.nome) LIKE :nome ESCAPE '\\'"
        parametros["nome"] = "%" + escapar_like(sem_acento(nome)) + "%"

    # Filtro 2: categoria (uma categoria ou "sem categoria")
    if sem_categoria:
        sql += " AND a.categoria_id IS NULL"
    elif categoria_id is not None:
        sql += " AND a.categoria_id = :categoria_id"
        parametros["categoria_id"] = categoria_id

    # Filtro 3: pasta (uma pasta ou a raiz)
    if na_raiz:
        sql += " AND a.pasta_id IS NULL"
    elif pasta_id is not None:
        sql += " AND a.pasta_id = :pasta_id"
        parametros["pasta_id"] = pasta_id

    # Filtro 4: tipo (arquivo ou link)
    if tipo:
        sql += " AND a.tipo = :tipo"
        parametros["tipo"] = tipo

    # Filtro 5: situação da leitura do conteúdo
    if status:
        sql += " AND a.status = :status"
        parametros["status"] = status

    # Filtro 6: só estes arquivos (usado na busca por significado)
    if ids is not None:
        if not ids:
            sql += " AND 1 = 0"
        else:
            nomes = [f":id{i}" for i in range(len(ids))]
            sql += f" AND a.id IN ({', '.join(nomes)})"
            parametros.update({f"id{i}": int(v) for i, v in enumerate(ids)})

    sql += " ORDER BY a.criado_em DESC, a.id DESC"

    return sql, parametros


# Converte a data do SQLite para o formato que o front espera
def _linha_para_dict(linha):
    dados = dict(linha)

    if isinstance(dados["criado_em"], str):
        dados["criado_em"] = datetime.fromisoformat(dados["criado_em"])

    dados["criado_em"] = para_iso(dados["criado_em"])
    return dados


# Lista os arquivos do repositório aplicando os filtros que vierem
def filtrar(repositorio_id, **filtros):
    sql, parametros = montar_consulta(repositorio_id, **filtros)

    linhas = db.session.execute(db.text(sql), parametros).mappings().all()

    return [_linha_para_dict(linha) for linha in linhas]



# Vetores já gerados dos arquivos do repositório (só os do modelo atual)
def vetores_do_repositorio(repositorio_id, modelo):
    sql = """
        SELECT e.arquivo_id, e.vetor
        FROM embeddings_arquivo e
        JOIN arquivos a ON a.id = e.arquivo_id
        WHERE a.repositorio_id = :repositorio_id AND e.modelo = :modelo
    """
    linhas = db.session.execute(
        db.text(sql), {"repositorio_id": repositorio_id, "modelo": modelo}
    ).mappings().all()

    return [{"id": linha["arquivo_id"], "vetor": linha["vetor"]} for linha in linhas]


# Arquivos com texto que ainda não têm vetor do modelo atual
def ids_sem_vetor(repositorio_id, modelo, limite):
    sql = """
        SELECT a.id
        FROM arquivos a
        LEFT JOIN embeddings_arquivo e ON e.arquivo_id = a.id AND e.modelo = :modelo
        WHERE a.repositorio_id = :repositorio_id
          AND a.status IN ('extraido', 'processado')
          AND e.arquivo_id IS NULL
        ORDER BY a.id DESC
        LIMIT :limite
    """
    linhas = db.session.execute(
        db.text(sql), {"repositorio_id": repositorio_id, "modelo": modelo, "limite": limite}
    ).mappings().all()

    return [linha["id"] for linha in linhas]


# Quantos arquivos com texto ainda estão sem vetor
def contar_sem_vetor(repositorio_id, modelo):
    sql = """
        SELECT COUNT(*) AS total
        FROM arquivos a
        LEFT JOIN embeddings_arquivo e ON e.arquivo_id = a.id AND e.modelo = :modelo
        WHERE a.repositorio_id = :repositorio_id
          AND a.status IN ('extraido', 'processado')
          AND e.arquivo_id IS NULL
    """
    return db.session.execute(
        db.text(sql), {"repositorio_id": repositorio_id, "modelo": modelo}
    ).scalar()
