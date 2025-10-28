# Arquivo: app/__init__.py

import os
from flask import Flask
from .models import db, User 
from flask_login import LoginManager
from dotenv import load_dotenv
import logging
from flask_migrate import Migrate  # <--- 1. ADICIONE ESTA IMPORTAÇÃO

load_dotenv()  

# Lista de tarefas recorrentes...
TAREFAS_RECORRENTES = [
    "Cozinha Cima", "Cozinha baixo + escadas", "Banheiro baixo + salinha",
    "Sala + Entrada", "Banheiro cima", "Organizar área da stella e limpar varanda",
    "Área de baixo + Corredor máquina", "Limpeza da dispensa", "Folga", "Folga"
]

# <--- 2. INICIALIZE O OBJETO MIGRATE AQUI (FORA DA FUNÇÃO)
#    (Se você já tem db = SQLAlchemy() no models.py, 
#     o ideal é ter migrate = Migrate() lá também e importar aqui,
#     mas isso vai funcionar de qualquer forma)
migrate = Migrate()


def create_app():
    app = Flask(__name__, instance_relative_config=True) 

    # Define o caminho base...
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # Define a URI do banco de dados...
    db_uri = os.getenv('DATABASE_URL') or \
             'sqlite:///' + os.path.join(basedir, 'app.db')

    # Configurações do App...
    app.config.update(
        SQLALCHEMY_DATABASE_URI=db_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=os.getenv('SECRET_KEY', 'uma-chave-secreta-padrao-provisoria'), 
    )

    # Inicializa DB
    db.init_app(app)

    # <--- 3. ADICIONE ESTA LINHA PARA CONECTAR O MIGRATE
    migrate.init_app(app, db)
    # ----------------------------------------------------

    # Configura LoginManager
    login_manager = LoginManager()
    login_manager.login_view = 'routes.login' 
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            app.logger.error(f"Erro ao carregar usuário ID {user_id}: {e}")
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
    from . import financas
    app.register_blueprint(financas.financas_bp)

    # Registra comandos CLI
    from . import commands
    commands.init_app(app)

    # Logging...
    if not app.debug:
        # ... seu código de logging ...
        app.logger.info('Aplicação Republica Manager iniciada')

    return app