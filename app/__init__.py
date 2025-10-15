from flask import Flask
from .models import db, User, Tarefa
from flask_login import LoginManager

# A lista de tarefas original agora fica aqui
TAREFAS_RECORRENTES = [
    "Cozinha Cima", "Cozinha baixo + escadas", "Banheiro baixo + salinha",
    "Sala + Entrada", "Banheiro cima", "Organizar área da stella e limpar varanda",
    "Área de baixo + Corredor máquina", "Limpeza da dispensa", "Folga", "Folga"
]

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-dificil'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'routes.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Registra as rotas
    from . import routes
    app.register_blueprint(routes.bp)
    from . import escala
    app.register_blueprint(escala.escala_bp)
    from . import admin
    app.register_blueprint(admin.admin_bp)
    from . import tarefas
    app.register_blueprint(tarefas.tarefas_bp)
    
    with app.app_context():
        db.create_all()

        # Popula a tabela de Tarefas com as tarefas da escala se estiver vazia
        if Tarefa.query.first() is None:
            for desc in TAREFAS_RECORRENTES:
                nova_tarefa = Tarefa(descricao=desc, recorrente=True)
                db.session.add(nova_tarefa)
            print("Tarefas recorrentes padrão criadas com sucesso!")

        # Cria o usuário admin padrão se NENHUM usuário existir
        if User.query.first() is None:
            admin_user = User(username='aldeia', cargo='admin')
            admin_user.set_password('aldeia#2014')
            db.session.add(admin_user)
            print("Usuário 'admin' padrão ('aldeia') criado com sucesso!")
    
        # Lista de usuários padrão da república
        default_users = [
            "duposto", "jubileu", "vigarista", "peçarrara", "karcaça",
            "macale", "serrote", "6bomba", "falamansa", "parabrisa"
        ]

        # Loop para verificar e criar cada usuário se ele não existir
        for username in default_users:
            if not User.query.filter_by(username=username).first():
                user = User(username=username, cargo='usuario')
                user.set_password('123')
                db.session.add(user)
                print(f"Usuário padrão '{username}' criado com sucesso!")

        # Salva todas as novas criações no banco de dados
        db.session.commit()

    return app

