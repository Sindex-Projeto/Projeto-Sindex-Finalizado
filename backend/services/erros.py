# Erro esperado (ex.: "E-mail já cadastrado"); vira {"erro": ...} no app.py
class ErroServico(Exception):
    def __init__(self, mensagem, status=400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status
