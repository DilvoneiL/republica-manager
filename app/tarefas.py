from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from .models import db, Tarefa
from .admin import manager_required # Reutilizamos o decorator de permissão

tarefas_bp = Blueprint('tarefas', __name__, url_prefix='/tarefas')

@tarefas_bp.route('/')
@login_required
@manager_required
def lista_tarefas():
    """Mostra todas as tarefas que podem ser gerenciadas."""
    tarefas = Tarefa.query.order_by(Tarefa.id).all()
    return render_template('tarefas.html', tarefas=tarefas)

@tarefas_bp.route('/criar', methods=['GET', 'POST'])
@login_required
@manager_required
def criar_tarefa():
    """Página com formulário para adicionar uma nova tarefa."""
    if request.method == 'POST':
        descricao = request.form.get('descricao', '').strip()
        
        if not descricao:
            flash('A descrição da tarefa é obrigatória.', 'warning')
            return render_template('criar_tarefa.html')

        if Tarefa.query.filter_by(descricao=descricao).first():
            flash('Uma tarefa com essa descrição já existe.', 'danger')
            return render_template('criar_tarefa.html')

        # Tarefas criadas manualmente não são recorrentes por padrão
        nova_tarefa = Tarefa(descricao=descricao, recorrente=False)
        db.session.add(nova_tarefa)
        db.session.commit()
        
        flash(f'Tarefa "{descricao}" criada com sucesso!', 'success')
        return redirect(url_for('tarefas.lista_tarefas'))

    return render_template('criar_tarefa.html')

@tarefas_bp.route('/editar/<int:tarefa_id>', methods=['GET', 'POST'])
@login_required
@manager_required
def edit_tarefa(tarefa_id):
    """Página para editar uma tarefa existente."""
    tarefa = Tarefa.query.get_or_404(tarefa_id)

    if request.method == 'POST':
        nova_descricao = request.form.get('descricao', '').strip()

        if not nova_descricao:
            flash('A descrição não pode ficar em branco.', 'warning')
            return render_template('criar_tarefa.html', tarefa_alvo=tarefa)
        
        tarefa.descricao = nova_descricao
        db.session.commit()
        flash(f'Tarefa atualizada com sucesso!', 'success')
        return redirect(url_for('tarefas.lista_tarefas'))

    return render_template('criar_tarefa.html', tarefa_alvo=tarefa)

@tarefas_bp.route('/deletar/<int:tarefa_id>', methods=['POST'])
@login_required
@manager_required
def deletar_tarefa(tarefa_id):
    """Rota para apagar uma tarefa."""
    tarefa = Tarefa.query.get_or_404(tarefa_id)
    
    # Regra: Não permitir apagar tarefas recorrentes da escala original
    if tarefa.recorrente:
        flash('Não é possível remover tarefas da escala automática. Você pode editá-las.', 'danger')
        return redirect(url_for('tarefas.lista_tarefas'))

    db.session.delete(tarefa)
    db.session.commit()
    flash('Tarefa avulsa removida com sucesso.', 'success')
    return redirect(url_for('tarefas.lista_tarefas'))
