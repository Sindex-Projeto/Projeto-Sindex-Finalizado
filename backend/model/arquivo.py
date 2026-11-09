from database import db, agora, para_iso

# Situações possíveis de um arquivo
STATUS_PENDENTE = "pendente"
STATUS_EXTRAIDO = "extraido"
STATUS_SEM_TEXTO = "sem_texto"
STATUS_FALHOU = "falhou"
STATUS_PROCESSADO = "processado"


# Tabela de arquivos e links
class Arquivo(db.Model):
    __tablename__ = "arquivos"

    id = db.Column(db.Integer, primary_key=True)

    # "arquivo" ou "link"
    tipo = db.Column(db.String(20), nullable=False, default="arquivo")

    nome = db.Column(db.String(255), nullable=False)

    # Dados do arquivo enviado
    nome_armazenado = db.Column(db.String(255))
    extensao = db.Column(db.String(10))
    tamanho = db.Column(db.Integer)

    # Endereço (só para links)
    url = db.Column(db.String(2048))

    # Texto lido do conteúdo
    texto_extraido = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default=STATUS_PENDENTE)

    # Motivo da situação (ex.: PDF com senha)
    observacao = db.Column(db.String(255))

    # Ligações com repositório, usuário, categoria e pasta
    repositorio_id = db.Column(
        db.Integer, db.ForeignKey("repositorios.id"), nullable=False, index=True
    )
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"))
    pasta_id = db.Column(db.Integer, db.ForeignKey("pastas.id"))
    criado_em = db.Column(db.DateTime, default=agora, nullable=False)

    # Dados enviados ao front
    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "nome": self.nome,
            "extensao": self.extensao,
            "tamanho": self.tamanho,
            "url": self.url,
            "status": self.status,
            "observacao": self.observacao,
            "repositorio_id": self.repositorio_id,
            "usuario_id": self.usuario_id,
            "categoria_id": self.categoria_id,
            "pasta_id": self.pasta_id,
            "criado_em": para_iso(self.criado_em),
        }


# Consultas
def buscar_por_id(id):
    return db.session.get(Arquivo, id)


# Tira a categoria dos arquivos (quando ela é apagada)
def desvincular_categoria(categoria_id):
    consulta = db.select(Arquivo).where(Arquivo.categoria_id == categoria_id)
    for arquivo in db.session.execute(consulta).scalars():
        arquivo.categoria_id = None


# Move os arquivos de uma pasta para outra
def mover_da_pasta(pasta_id, novo_pasta_id):
    consulta = db.select(Arquivo).where(Arquivo.pasta_id == pasta_id)
    for arquivo in db.session.execute(consulta).scalars():
        arquivo.pasta_id = novo_pasta_id
