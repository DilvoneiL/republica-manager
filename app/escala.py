from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from datetime import date, timedelta, datetime
from .models import db, User, Tarefa, EscalaSemanal
import itertools

escala_bp = Blueprint('escala', __name__)


# Listas de responsáveis para o cálculo da escala
responsaveis_invertido = [
    "falamansa", "parabrisa", "duposto", "jubileu", 
    "vigarista", "peçarrara", "karcaça", "macale", "serrote", "6bomba"
]
responsaveis_original = [
    "parabrisa", "falamansa", "jubileu", "duposto", 
    "peçarrara", "vigarista", "macale", "karcaça" ,"6bomba", "serrote"
]
tarefas = [
    "Cozinha Cima", "Cozinha baixo + escadas", "Banheiro baixo + salinha",
    "Sala + Entrada", "Banheiro cima", "Organizar área da stella e limpar varanda",
    "Área de baixo + Corredor máquina", "Limpeza da dispensa", "Folga", "Folga"
]

def get_total_weeks(ano, semana):
    return (ano - 2024) * 52 + semana

@escala_bp.route('/escala')
@escala_bp.route('/escala/<int:ano>/<int:semana>')
@login_required
def ver_escala(ano=None, semana=None):
    if ano is None or semana is None:
        hoje = date.today()
        data_ajustada = hoje - timedelta(days=2)
        semana = data_ajustada.isocalendar()[1]
        ano = data_ajustada.isocalendar()[0]

    data_referencia = datetime.fromisocalendar(ano, semana, 1)
    data_anterior = data_referencia - timedelta(days=7)
    data_proxima = data_referencia + timedelta(days=7)
    semana_anterior = {'ano': data_anterior.isocalendar()[0], 'semana': data_anterior.isocalendar()[1]}
    semana_proxima = {'ano': data_proxima.isocalendar()[0], 'semana': data_proxima.isocalendar()[1]}

    tabela_db = EscalaSemanal.query.filter_by(semana=semana, ano=ano).order_by(EscalaSemanal.id).all()

    if not tabela_db:
        tarefas_recorrentes_db = Tarefa.query.filter_by(recorrente=True).order_by(Tarefa.id).all()
        tarefas_desc = [t.descricao for t in tarefas_recorrentes_db]

        total_weeks = get_total_weeks(ano, semana)
        cycle_number = (total_weeks - 1) // 5

        base_a_usar = responsaveis_original if cycle_number % 2 == 0 else responsaveis_invertido
        
        rotacao = (semana * -2) % len(base_a_usar)
        responsaveis_final = base_a_usar[rotacao:] + base_a_usar[:rotacao]
        
        responsaveis_ajustados = (responsaveis_final * (len(tarefas_desc) // len(responsaveis_final) + 1))[:len(tarefas_desc)]

        for tarefa_desc, responsavel_nome in zip(tarefas_desc, responsaveis_ajustados):
            nova_tarefa_db = EscalaSemanal(semana=semana, ano=ano, tarefa=tarefa_desc, responsavel=responsavel_nome, tipo='recorrente')
            db.session.add(nova_tarefa_db)
        
        db.session.commit()
        tabela_db = EscalaSemanal.query.filter_by(semana=semana, ano=ano).order_by(EscalaSemanal.id).all()

    return render_template('escala.html', tabela=tabela_db, semana=semana, ano=ano,
                           semana_anterior=semana_anterior, semana_proxima=semana_proxima)

@escala_bp.route('/escala/adicionar-avulsa/<int:ano>/<int:semana>', methods=['GET', 'POST'])
@login_required
def adicionar_tarefa_avulsa(ano, semana):
    if not current_user.is_gerenciador():
        flash('Acesso negado.', 'danger')
        return redirect(url_for('escala.ver_escala', ano=ano, semana=semana))
    
    if request.method == 'POST':
        descricao = request.form.get('descricao', '').strip()
        responsavel_username = request.form.get('responsavel')

        if not descricao or not responsavel_username:
            flash('Ambos os campos, descrição e responsável, são obrigatórios.', 'warning')
        else:
            tarefa_avulsa = EscalaSemanal(semana=semana, ano=ano, tarefa=descricao, responsavel=responsavel_username, tipo='avulsa')
            db.session.add(tarefa_avulsa)
            db.session.commit()
            flash('Tarefa avulsa adicionada com sucesso!', 'success')
            return redirect(url_for('escala.ver_escala', ano=ano, semana=semana))

    usuarios = User.query.filter(User.cargo != 'admin').order_by(User.username).all()
    return render_template('adicionar_tarefa_avulsa.html', ano=ano, semana=semana, usuarios=usuarios)

# --- ROTAS QUE ESTAVAM EM FALTA ---
@escala_bp.route('/escala/editar/<int:id_tarefa>', methods=['GET', 'POST'])
@login_required
def edit_tarefa_semanal(id_tarefa):
    if not current_user.is_gerenciador():
        abort(403)
    
    tarefa = EscalaSemanal.query.get_or_404(id_tarefa)
    
    if request.method == 'POST':
        tarefa.tarefa = request.form.get('descricao', '').strip()
        tarefa.responsavel = request.form.get('responsavel')
        db.session.commit()
        flash('Tarefa da semana atualizada com sucesso!', 'success')
        return redirect(url_for('escala.ver_escala', ano=tarefa.ano, semana=tarefa.semana))

    usuarios = User.query.order_by(User.username).all()
    return render_template('editar_tarefa_semanal.html', tarefa=tarefa, usuarios=usuarios)

@escala_bp.route('/escala/deletar/<int:id_tarefa>', methods=['POST'])
@login_required
def deletar_tarefa_semanal(id_tarefa):
    if not current_user.is_gerenciador():
        abort(403)
        
    tarefa = EscalaSemanal.query.get_or_404(id_tarefa)
    
    if tarefa.tipo == 'recorrente':
        flash('Não é possível remover uma tarefa da escala automática.', 'danger')
    else:
        db.session.delete(tarefa)
        db.session.commit()
        flash('Tarefa avulsa removida com sucesso!', 'success')
        
    return redirect(url_for('escala.ver_escala', ano=tarefa.ano, semana=tarefa.semana))
# --- FIM DAS ROTAS EM FALTA ---

@escala_bp.route('/escala/fazer/<int:id_tarefa>')
@login_required
def fazer(id_tarefa):
    tarefa = EscalaSemanal.query.get_or_404(id_tarefa)
    if current_user.username == tarefa.responsavel or current_user.is_gerenciador():
        tarefa.status = 'feita'
        db.session.commit()
    else:
        flash('Você não tem permissão para marcar esta tarefa como feita.', 'danger')
    return redirect(url_for('escala.ver_escala', ano=tarefa.ano, semana=tarefa.semana))

@escala_bp.route('/escala/historico')
@login_required
def historico_escala():
    todas_as_tarefas = EscalaSemanal.query.order_by(EscalaSemanal.ano.desc(), EscalaSemanal.semana.desc()).all()
    dados_agrupados = []
    for chave, grupo in itertools.groupby(todas_as_tarefas, key=lambda x: (x.ano, x.semana)):
        dados_agrupados.append({'chave': chave, 'tarefas': list(grupo)})
    return render_template('historico.html', dados_agrupados=dados_agrupados)

