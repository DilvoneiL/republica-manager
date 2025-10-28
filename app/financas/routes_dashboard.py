# app/financas/routes_dashboard.py

from flask import render_template, redirect, url_for, abort, flash, request # <-- ADDED request HERE
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import func

# 1. Importa o Blueprint, helpers e constantes do __init__.py desta pasta
from . import financas_bp, get_dados_caixinha, CHAVE_ALUGUEL, CHAVE_CAIXINHA

# 2. Importa os modelos e o db subindo um nível (de 'app/financas' para 'app')
from ..models import db, User, Lancamento, DespesaFixa, FechamentoMensal, CaixinhaMovimentacao

# --- DASHBOARDS ---
@financas_bp.route('/')
@financas_bp.route('/dashboard')
@login_required
def dashboard():
    hoje = datetime.utcnow()
    mes_atual = hoje.month
    ano_atual = hoje.year
    fechamento = FechamentoMensal.query.filter_by(mes=mes_atual, ano=ano_atual, status='fechado').first()
    if fechamento:
        return redirect(url_for('financas.ver_relatorio', fechamento_id=fechamento.id))
    if current_user.is_gerenciador():
        return redirect(url_for('financas.dashboard_tesoureiro'))
    else:
        return redirect(url_for('financas.dashboard_usuario'))

@financas_bp.route('/dashboard_usuario')
@login_required
def dashboard_usuario():
    hoje = datetime.utcnow()
    mes_atual = hoje.month
    ano_atual = hoje.year
    fechamento = FechamentoMensal.query.filter_by(mes=mes_atual, ano=ano_atual, status='fechado').first()
    if fechamento:
        return redirect(url_for('financas.ver_relatorio', fechamento_id=fechamento.id))
    # Mostra gastos LANÇADOS pelo usuário logado
    meus_gastos = Lancamento.query.filter_by(
        user_id=current_user.id, # Filtra por quem pagou (user_id)
        mes_referencia=mes_atual,
        ano_referencia=ano_atual
    ).order_by(Lancamento.data.desc()).all()
    total_gasto = sum(g.valor for g in meus_gastos)
    dados_caixinha = get_dados_caixinha()
    return render_template('dashboard_usuario.html',  # Caminho relativo ao 'template_folder'
                           meus_gastos=meus_gastos,
                           total_gasto=total_gasto,
                           dados_caixinha=dados_caixinha,
                           mes=mes_atual, ano=ano_atual)


@financas_bp.route('/dashboard_tesoureiro')
@login_required
def dashboard_tesoureiro():
    if not current_user.is_gerenciador(): abort(403)
    hoje = datetime.utcnow()
    mes_atual = hoje.month
    ano_atual = hoje.year
    fechamento = FechamentoMensal.query.filter_by(mes=mes_atual, ano=ano_atual, status='fechado').first()
    if fechamento:
        return redirect(url_for('financas.ver_relatorio', fechamento_id=fechamento.id))

    dados_caixinha = get_dados_caixinha()
    despesas_fixas = DespesaFixa.query.filter_by(ativa=True).all()
    lancamentos_variaveis_mes = Lancamento.query.filter_by(
        mes_referencia=mes_atual,
        ano_referencia=ano_atual
    ).order_by(Lancamento.data.desc()).all()

    # Gastos lançados/pagos POR usuário (crédito)
    gastos_lancados_por_usuario_query = db.session.query(
        User.username, func.sum(Lancamento.valor).label('total')
    ).join(User, Lancamento.user_id == User.id).filter( # Join explícito em user_id (pagador)
        Lancamento.mes_referencia == mes_atual,
        Lancamento.ano_referencia == ano_atual,
        Lancamento.user_id != None # Não inclui gastos da "Casa" (user_id=None)
    ).group_by(User.username).all()

    todos_usuarios_moradores = User.query.filter(User.cargo != 'admin').order_by(User.username).all()
    gastos_dict = {username: total for username, total in gastos_lancados_por_usuario_query}

    gastos_lancados_por_usuario = []
    for user in todos_usuarios_moradores:
        total = gastos_dict.get(user.username, 0.0)
        gastos_lancados_por_usuario.append({'username': user.username, 'total_lancado': total, 'tipo_quarto': user.tipo_quarto})

    # ATUALIZADO: Calcula totais PARA EXIBIÇÃO RÁPIDA (baseado em morador_id)
    total_fixo_outros_exib = sum(d.valor for d in despesas_fixas 
                                  if CHAVE_ALUGUEL not in d.descricao 
                                  and CHAVE_CAIXINHA not in d.descricao 
                                  and d.morador_id is None)
    
    total_variavel_casa_exib = sum(l.valor for l in lancamentos_variaveis_mes) 
    
    # Soma apenas aluguéis individuais (com morador_id)
    total_aluguel_exib = sum(d.valor for d in despesas_fixas 
                              if CHAVE_ALUGUEL in d.descricao 
                              and d.morador_id is not None) 
    
    total_caixinha_exib = dados_caixinha["valor_contribuicao_mensal"]
    total_gasto_geral_exibicao = total_fixo_outros_exib + total_variavel_casa_exib + total_aluguel_exib
    total_a_pagar_exibicao = total_gasto_geral_exibicao + total_caixinha_exib

    return render_template('dashboard_tesoureiro.html', # Caminho relativo
                           despesas_fixas=despesas_fixas,
                           lancamentos_variaveis=lancamentos_variaveis_mes,
                           gastos_por_usuario=gastos_lancados_por_usuario,
                           dados_caixinha=dados_caixinha,
                           total_fixo=total_fixo_outros_exib,
                           total_variavel=total_variavel_casa_exib,
                           total_gasto_geral=total_gasto_geral_exibicao,
                           total_a_pagar=total_a_pagar_exibicao,
                           chave_caixinha=CHAVE_CAIXINHA,
                           chave_aluguel=CHAVE_ALUGUEL,
                           mes=mes_atual, ano=ano_atual)


# --- ROTA RETIRAR CAIXINHA (ADICIONADA) ---
@financas_bp.route('/caixinha/retirar', methods=['POST'])
@login_required 
def retirar_da_caixinha():
    if not current_user.is_gerenciador(): abort(403)
    descricao = request.form.get('descricao_retirada')
    valor_str = request.form.get('valor_retirada')
    if not descricao or not valor_str:
        flash('Descrição e Valor são obrigatórios para a retirada.', 'danger')
        return redirect(url_for('financas.dashboard_tesoureiro'))
    try:
        valor_retirada = float(valor_str.replace(',', '.'))
        if valor_retirada <= 0:
              flash('O valor da retirada deve ser positivo.', 'danger')
              return redirect(url_for('financas.dashboard_tesoureiro'))
    except ValueError:
        flash('Valor inválido.', 'danger')
        return redirect(url_for('financas.dashboard_tesoureiro'))
    
    saldo_atual = db.session.query(func.sum(CaixinhaMovimentacao.valor)).scalar() or 0.0
    if valor_retirada > saldo_atual:
        flash(f'Saldo insuficiente no caixinha (Saldo: R$ {saldo_atual:.2f}).', 'danger')
        return redirect(url_for('financas.dashboard_tesoureiro'))
    
    nova_retirada = CaixinhaMovimentacao(
        descricao=descricao,
        valor=-valor_retirada,
        user_id=current_user.id
    )
    db.session.add(nova_retirada)
    db.session.commit()
    flash('Retirada do caixinha registrada com sucesso.', 'success')
    return redirect(url_for('financas.dashboard_tesoureiro'))