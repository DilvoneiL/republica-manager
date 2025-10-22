# Arquivo: app/__init__.py

import os
from flask import Flask
from .models import db, User, Tarefa
from flask_login import LoginManager
from dotenv import load_dotenv
import logging

load_dotenv()  # Carrega as variáveis do .env

# Lista de tarefas recorrentes
TAREFAS_RECORRENTES = [
    "Cozinha Cima", "Cozinha baixo + escadas", "Banheiro baixo + salinha",
    "Sala + Entrada", "Banheiro cima", "Organizar área da stella e limpar varanda",
    "Área de baixo + Corredor máquina", "Limpeza da dispensa", "Folga", "Folga"
]

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Configura variáveis de ambiente
    db_uri = os.getenv('DATABASE_URL')
    if not db_uri:
        raise RuntimeError("❌ DATABASE_URL não encontrada! Verifique o .env ou variáveis no Render.")

    # Configurações do SQLAlchemy + Supabase (produção)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=db_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=os.getenv('SECRET_KEY', 'uma-chave-secreta-muito-dificil'),
        SQLALCHEMY_ENGINE_OPTIONS={
            "pool_size": 5,            # conexões simultâneas
            "max_overflow": 2,         # conexões extras além do pool
            "pool_pre_ping": True,     # verifica se a conexão está ativa
            "pool_recycle": 280,       # recicla conexões antigas (~5 min)
            "connect_args": {"sslmode": "require"}  # obrigatório para Supabase
        }
    )

    # Inicializa DB
    db.init_app(app)

    # Configura LoginManager
    login_manager = LoginManager()
    login_manager.login_view = 'routes.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            # Retorna usuário se possível, senão None
            return User.query.get(int(user_id))
        except Exception as e:
            app.logger.error(f"Erro ao carregar usuário: {e}")
            return None

    # Registra Blueprints
    from . import routes
    app.register_blueprint(routes.bp)
    from . import escala
    app.register_blueprint(escala.escala_bp)
    from . import admin
    app.register_blueprint(admin.admin_bp)
    from . import tarefas
    app.register_blueprint(tarefas.tarefas_bp)

    # Registra comandos CLI (ex: flask init-db)
    from . import commands
    commands.init_app(app)

    # Logging detalhado de produção
    if not app.debug:
        import sys
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        )
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)

    return app
