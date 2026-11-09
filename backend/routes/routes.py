from controllers.arquivo_controller import arquivo_bp
from controllers.categoria_controller import categoria_bp
from controllers.ia_controller import ia_bp
from controllers.pasta_controller import pasta_bp
from controllers.repositorio_controller import repositorio_bp
from controllers.usuario_controller import usuario_bp


# Liga todas as rotas ao app
def registrar_rotas(app):
    app.register_blueprint(usuario_bp, url_prefix="/api")
    app.register_blueprint(repositorio_bp, url_prefix="/api")
    app.register_blueprint(categoria_bp, url_prefix="/api")
    app.register_blueprint(pasta_bp, url_prefix="/api")
    app.register_blueprint(arquivo_bp, url_prefix="/api")
    app.register_blueprint(ia_bp, url_prefix="/api")
