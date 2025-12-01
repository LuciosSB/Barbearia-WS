from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Agendamento(db.Model):
    __tablename__ = 'agendamentos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    data = db.Column(db.Date, nullable=False)
    horario = db.Column(db.String(5), nullable=False)
    status = db.Column(db.String(20), default='agendado')

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "telefone": self.telefone,
            "data": str(self.data),
            "horario": self.horario,
            "status": self.status
        }

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))

    def set_senha(self, senha):
        self.password_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.password_hash, senha)

class Produto(db.Model):
    __tablename__ = 'produtos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.String(20), nullable=False)
    imagem = db.Column(db.String(200), nullable=False)