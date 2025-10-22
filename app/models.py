from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    # Cargos: "admin", "gerenciador", "usuario"
    cargo = db.Column(db.String(20), nullable=False, default='usuario')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.cargo == 'admin'

    def is_gerenciador(self):
        return self.cargo in ['admin', 'gerenciador']

class EscalaSemanal(db.Model):
    __tablename__ = 'escala_semanal'
    
    id = db.Column(db.Integer, primary_key=True)
    semana = db.Column(db.Integer, nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    tarefa = db.Column(db.String(200), nullable=False)
    responsavel = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pendente')
    tipo = db.Column(db.String(20), nullable=False, default='recorrente')
# --- TABELA PARA TAREFAS EDITÁVEIS ---
class Tarefa(db.Model):
    __tablename__ = 'tarefas'
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    # Define se a tarefa é recorrente (parte da escala) ou avulsa
    recorrente = db.Column(db.Boolean, default=True)

