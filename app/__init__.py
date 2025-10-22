# Arquivo: app/__init__.py

import os
from flask import Flask
# Certifique-se de que seus modelos estão corretos aqui
# Se você tiver db e User em models.py, mantenha:
from .models import db, User # Remova Tarefa se não existir ou ajuste
# Se db e User estiverem definidos aqui mesmo, ajuste conforme necessário
from flask_login import LoginManager
from dotenv import load_dotenv
import logging

load_dotenv()  # Carrega as variáveis do .env (útil para desenvolvimento local)

# Lista de tarefas recorrentes (mantida como estava)
TAREFAS_RECORRENTES = [
    "Cozinha Cima", "Cozinha baixo + escadas", "Banheiro baixo + salinha",
    "Sala + Entrada", "Banheiro cima", "Organizar área da stella e limpar varanda",
    "Área de baixo + Corredor máquina", "Limpeza da dispensa", "Folga", "Folga"
]

def create_app():
    app = Flask(__name__, instance_relative_config=True) # instance_relative_config é opcional aqui

    # --- INÍCIO DAS MODIFICAÇÕES ---

    # Define o caminho base do projeto (um nível acima da pasta 'app')
    # Isso garante que 'app.db' seja criado na pasta raiz 'republica-manager'
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # Define a URI do banco de dados:
    # 1. Tenta usar DATABASE_URL (para Render/Supabase se definido)
    # 2. Se não, usa 'sqlite:///caminho/completo/para/app.db' na raiz do projeto
    db_uri = os.getenv('DATABASE_URL') or \
             'sqlite:///' + os.path.join(basedir, 'app.db')

    # Configurações do App
    app.config.update(
        SQLALCHEMY_DATABASE_URI=db_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=os.getenv('SECRET_KEY', 'uma-chave-secreta-padrao-provisoria'), # Use uma chave padrão segura se SECRET_KEY não estiver no .env
        # REMOVEMOS SQLALCHEMY_ENGINE_OPTIONS pois não são necessárias para SQLite
    )

    # --- FIM DAS MODIFICAÇÕES ---

    # Inicializa DB
    db.init_app(app)

    # Configura LoginManager (mantido como estava)
    login_manager = LoginManager()
    login_manager.login_view = 'routes.login' # Certifique-se que 'routes.login' é o endpoint correto
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            # Retorna usuário se possível, senão None (mantido como estava)
            # Garanta que o modelo User está importado corretamente
            return User.query.get(int(user_id))
        except Exception as e:
            # Mantém o log de erro, importante para depuração
            app.logger.error(f"Erro ao carregar usuário ID {user_id}: {e}")
            return None

    # Registra Blueprints (mantido como estava)
    from . import routes
    app.register_blueprint(routes.bp)
    from . import escala
    app.register_blueprint(escala.escala_bp)
    from . import admin
    app.register_blueprint(admin.admin_bp)
    from . import tarefas
    app.register_blueprint(tarefas.tarefas_bp)

    # Registra comandos CLI (mantido como estava)
    from . import commands
    commands.init_app(app)

    # Logging detalhado de produção (mantido como estava, é uma boa prática)
    if not app.debug:
        import sys
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        )
        handler.setFormatter(formatter)
        # Limpa handlers existentes para evitar duplicação em recargas
        if not app.logger.handlers:
             app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Aplicação Republica Manager iniciada') # Log inicial

    return app