from database import db, agora, para_iso

# Opções de configuração
TEMAS = ("escuro", "claro")
IDIOMAS = ("pt-BR", "en")


# Tabela de usuários
class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    criado_em = db.Column(db.DateTime, default=agora, nullable=False)

    # Configurações da conta
    ia_ativa = db.Column(db.Boolean, default=True, nullable=False)
    tema = db.Column(db.String(10), default="escuro", nullable=False)
    idioma = db.Column(db.String(10), default="pt-BR", nullable=False)

    # Dados enviados ao front (nunca a senha)
    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "criado_em": para_iso(self.criado_em),
            "config": self.config(),
        }

    def config(self):
        return {"ia_ativa": self.ia_ativa, "tema": self.tema, "idioma": self.idioma}


# Consultas
def buscar_por_id(id):
    return db.session.get(Usuario, id)


def buscar_por_email(email):
    consulta = db.select(Usuario).where(Usuario.email == email)
    return db.session.execute(consulta).scalar_one_or_none()


# Cria o usuário
def criar(nome, email, senha_hash):
    novo = Usuario(nome=nome, email=email, senha_hash=senha_hash)
    db.session.add(novo)
    db.session.flush()
    return novo
