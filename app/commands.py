# Arquivo: app/commands.py  <-- CÓDIGO CORRIGIDO

import click
from flask.cli import with_appcontext

# REMOVEMOS AS IMPORTAÇÕES DE 'db', 'models' e 'TAREFAS' DAQUI
# Elas serão movidas para dentro da função abaixo

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Limpa os dados existentes e cria novas tabelas com dados padrão."""
    
    # --- MUDANÇA AQUI ---
    # As importações agora estão DENTRO da função
    from . import db
    from .models import User, Tarefa
    from . import TAREFAS_RECORRENTES
    # --- FIM DA MUDANÇA ---

    # 1. Cria todas as tabelas (ele já verifica se existem)
    db.create_all()
    click.echo('Tabelas criadas com sucesso!')

    # 2. Popula a tabela de Tarefas se estiver vazia
    if Tarefa.query.first() is None:
        for desc in TAREFAS_RECORRENTES:
            nova_tarefa = Tarefa(descricao=desc, recorrente=True)
            db.session.add(nova_tarefa)
        click.echo('Tarefas recorrentes padrão criadas com sucesso!')

    # 3. Cria o usuário admin padrão se NENHUM usuário existir
    if User.query.first() is None:
        admin_user = User(username='aldeia', cargo='admin')
        admin_user.set_password('aldeia#2014')
        db.session.add(admin_user)
        click.echo("Usuário 'admin' padrão ('aldeia') criado com sucesso!")

    # 4. Lista de usuários padrão da república
    default_users = [
        "duposto", "jubileu", "vigarista", "peçarrara", "karcaça",
        "macale", "serrote", "6bomba", "falamansa", "parabrisa"
    ]

    # 5. Loop para verificar e criar cada usuário se ele não existir
    for username in default_users:
        if not User.query.filter_by(username=username).first():
            user = User(username=username, cargo='usuario')
            user.set_password('123')
            db.session.add(user)
            click.echo(f"Usuário padrão '{username}' criado com sucesso!")

    # 6. Salva todas as novas criações no banco de dados
    db.session.commit()
    click.echo('Todas as alterações foram salvas no banco de dados.')


def init_app(app):
    """Registra os comandos da CLI na aplicação Flask."""
    app.cli.add_command(init_db_command)