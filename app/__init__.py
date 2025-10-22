# Arquivo: app/__init__.py

import os
from flask import Flask
from .models import db, User, Tarefa
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()  # Carrega as variáveis do .env

# Lista de tarefas recorrentes
TAREFAS_RECORRENTES = [
    "Cozinha Cima", "Cozinha baixo + escadas", "Banheiro baixo + salinha",
    "Sala + Entrada", "Banheiro cima", "Organizar área da stella e limpar varanda",
    "Área de baixo + Corredor máquina", "Limpeza da dispensa", "Folga", "Folga"
]

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    db_uri_from_env = os.getenv('DATABASE_URL')
    if not db_uri_from_env:
        raise ValueError("❌ DATABASE_URL não encontrada! Verifique o .env ou as variáveis de ambiente no Render.")

    # Configurações do SQLAlchemy e pool para evitar SSL connection closed
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri_from_env
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-dificil'
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_size": 5,
        "max_overflow": 2,
        "pool_pre_ping": True,
        "pool_recycle": 280,  # força reciclar conexões antigas (~5 min)
        "connect_args": {"sslmode": "require"}
    }

    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'routes.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Registra as rotas (Blueprints)
    from . import routes
    app.register_blueprint(routes.bp)
    from . import escala
    app.register_blueprint(escala.escala_bp)
    from . import admin
    app.register_blueprint(admin.admin_bp)
    from . import tarefas
    app.register_blueprint(tarefas.tarefas_bp)
    
    # Registra o comando 'flask init-db'
    from . import commands
    commands.init_app(app)
    
    return app
