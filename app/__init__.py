from flask import Flask
from app.estruturas.tabela_hash import TabelaHash
from app.estruturas.fila import Fila

agendamentos_db = TabelaHash(tamanho=200)
fila_atendimento = Fila()

def create_app():
    app = Flask(__name__)

    from app.routes.main import main_bp
    app.register_blueprint(main_bp)

    return app