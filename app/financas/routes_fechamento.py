# app/financas/routes_fechamento.py (VERSÃO CORRIGIDA FINAL)

from flask import render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime

# 1. Importa o Blueprint, constantes e o db
from . import financas_bp, db, CHAVE_ALUGUEL, CHAVE_CAIXINHA
# --- CORREÇÃO AQUI: REMOVIDO 'ValorAluguel' ---
from ..models import (User, Lancamento, DespesaFixa, FechamentoMensal,
                    SaldoMensal, CaixinhaMovimentacao)


# --- ROTA DE FECHAMENTO (CORRIGIDA) ---
@financas_bp.route('/fechar_mes', methods=['POST'])
@login_required
def fechar_mes():
    if not current_user.is_gerenciador():
        abort(403)

    hoje = datetime.utcnow()
    mes = hoje.month
    ano = hoje.year

    if FechamentoMensal.query.filter_by(mes=mes, ano=ano, status='fechado').first():
        flash('Este mês já foi fechado.', 'warning')
        return redirect(url_for('financas.dashboard'))

    # --- LÓGICA DE ALUGUEL BASEADA EM 'ValorAluguel' REMOVIDA ---

    despesas_fixas_query = DespesaFixa.query.filter_by(ativa=True).all()

    # Soma das despesas fixas 'Aluguel' individuais (com morador_id)
    total_aluguel_fixo_mes = sum(d.valor for d in despesas_fixas_query
                                 if d.descricao == CHAVE_ALUGUEL
                                 and d.morador_id is not None)

    # Soma da contribuição geral do Caixinha (sem morador_id)
    valor_caixinha_mes = sum(d.valor for d in despesas_fixas_query
                             if d.descricao == CHAVE_CAIXINHA
                             and d.morador_id is None)

    # Soma das outras despesas gerais (sem morador_id e não-Aluguel/Caixinha)
    total_fixo_outros = sum(d.valor for d in despesas_fixas_query
                            if d.descricao != CHAVE_ALUGUEL
                            and d.descricao != CHAVE_CAIXINHA
                            and d.morador_id is None)

    # Lançamentos variáveis são todos da "casa"
    total_variavel_casa = db.session.query(func.sum(Lancamento.valor)).filter(
        Lancamento.mes_referencia == mes,
        Lancamento.ano_referencia == ano
    ).scalar() or 0.0

    total_outras_despesas_gerais = total_fixo_outros + total_variavel_casa + valor_caixinha_mes

    moradores = User.query.filter(User.cargo != 'admin').all()
    if not moradores:
        flash('Nenhum morador (usuário ou gerenciador) encontrado para dividir.', 'danger')
        return redirect(url_for('financas.dashboard'))

    num_moradores = len(moradores)
    cota_outras_despesas = total_outras_despesas_gerais / num_moradores if num_moradores > 0 else 0

    try:
        novo_fechamento = FechamentoMensal(
            mes=mes,
            ano=ano,
            total_fixo=total_fixo_outros,
            total_variavel=total_variavel_casa,
            total_aluguel_mes=total_aluguel_fixo_mes,
            valor_caixinha_arrecadado=valor_caixinha_mes,
            status='fechado'
        )
        db.session.add(novo_fechamento)
        db.session.flush()

        if valor_caixinha_mes > 0:
            entrada_caixinha = CaixinhaMovimentacao(
                data=hoje,
                descricao=f"Depósito do fechamento {mes}/{ano}",
                valor=valor_caixinha_mes,
                user_id=None
            )
            db.session.add(entrada_caixinha)

        for morador in moradores:
            # --- NOVA LÓGICA DE ALUGUEL ---
            # Busca a despesa de aluguel específica daquele morador
            despesa_aluguel_morador = DespesaFixa.query.filter_by(
                descricao=CHAVE_ALUGUEL,
                morador_id=morador.id,
                ativa=True # Considera apenas se a despesa individual está ativa
            ).first()

            if not despesa_aluguel_morador:
                # Se não achar, lança um erro
                raise ValueError(f"Morador '{morador.username}' não possui despesa de aluguel ativa. Por favor, atualize os valores em 'Gerenciar Aluguel'.")

            valor_aluguel_morador = despesa_aluguel_morador.valor
            # --- FIM DA NOVA LÓGICA ---

            gastos_pessoais_devidos = 0.0 # Mantido como 0
            valor_devido_user = valor_aluguel_morador + cota_outras_despesas

            total_gasto_lancado_user = db.session.query(func.sum(Lancamento.valor)).filter_by(
                mes_referencia=mes, ano_referencia=ano, user_id=morador.id
            ).scalar() or 0.0

            saldo_final = total_gasto_lancado_user - valor_devido_user

            novo_saldo = SaldoMensal(
                fechamento_id=novo_fechamento.id,
                user_id=morador.id,
                total_gasto=total_gasto_lancado_user,
                valor_devido=valor_devido_user,
                valor_devido_aluguel=valor_aluguel_morador,
                valor_devido_outros=cota_outras_despesas,
                valor_devido_pessoais=gastos_pessoais_devidos,
                saldo_final=saldo_final,
                status_pagamento='pendente'
            )
            db.session.add(novo_saldo)

        db.session.commit()
        flash(f'Mês {mes}/{ano} fechado com sucesso!', 'success')
        return redirect(url_for('financas.ver_relatorio', fechamento_id=novo_fechamento.id))

    except ValueError as ve:
        db.session.rollback()
        flash(f'Erro ao fechar o mês: {ve}', 'danger')
        if 'Gerenciar Aluguel' in str(ve):
             return redirect(url_for('financas.gerenciar_aluguel'))
        else:
             return redirect(url_for('financas.dashboard'))
    except Exception as e:
        db.session.rollback()
        # Logar o erro completo pode ser útil para debug
        # current_app.logger.error(f'Erro inesperado ao fechar o mês: {e}', exc_info=True)
        flash(f'Erro inesperado ao fechar o mês. Verifique os logs.', 'danger')
        return redirect(url_for('financas.dashboard'))


# --- ROTAS REABRIR, RELATÓRIO, HISTÓRICO, QUITAR (CORRIGIDAS) ---
@financas_bp.route('/reabrir_mes/<int:fechamento_id>', methods=['POST'])
@login_required
def reabrir_mes(fechamento_id):
    if not current_user.is_gerenciador(): abort(403)
    fechamento = FechamentoMensal.query.get_or_404(fechamento_id)
    try:
        # Tenta remover a entrada correspondente no caixinha
        if fechamento.valor_caixinha_arrecadado > 0:
            entrada_caixinha_associada = CaixinhaMovimentacao.query.filter(
                # Condições mais específicas para evitar deletar a errada
                CaixinhaMovimentacao.descricao.like(f"Depósito do fechamento {fechamento.mes}/{fechamento.ano}%"),
                CaixinhaMovimentacao.valor == fechamento.valor_caixinha_arrecadado,
                CaixinhaMovimentacao.user_id == None
            ).order_by(CaixinhaMovimentacao.id.desc()).first()
            if entrada_caixinha_associada:
                db.session.delete(entrada_caixinha_associada)
            else:
                 flash(f'Atenção: Não foi encontrada a entrada automática no caixinha para o fechamento {fechamento.mes}/{fechamento.ano}. Saldo pode precisar de ajuste manual.', 'warning')
        
        # Deleta o fechamento (o cascade="all, delete-orphan" deve deletar os SaldoMensal)
        db.session.delete(fechamento)
        db.session.commit()
        flash(f'Mês {fechamento.mes}/{fechamento.ano} foi reaberto.', 'success')
        return redirect(url_for('financas.dashboard')) # Volta para o dashboard atual
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao reabrir o mês: {e}', 'danger')
        # Volta para o relatório que tentou reabrir
        return redirect(url_for('financas.ver_relatorio', fechamento_id=fechamento_id))


@financas_bp.route('/relatorio/<int:fechamento_id>')
@login_required
def ver_relatorio(fechamento_id):
    fechamento = FechamentoMensal.query.get_or_404(fechamento_id)
    saldos = SaldoMensal.query.filter_by(fechamento_id=fechamento.id).join(User).order_by(User.username).all()

    # Não precisamos mais do 'ValorAluguel' aqui

    return render_template('relatorio.html',
                           fechamento=fechamento,
                           saldos=saldos,
                           # Passando None ou um dict vazio, já que o template antigo pode esperar
                           valores_aluguel=None)


@financas_bp.route('/historico')
@login_required
def historico_financeiro():
    fechamentos = FechamentoMensal.query.filter_by(status='fechado') \
                                 .order_by(FechamentoMensal.ano.desc(), FechamentoMensal.mes.desc()).all()
    return render_template('historico_financeiro.html', fechamentos=fechamentos)

@financas_bp.route('/quitar_saldo/<int:saldo_id>', methods=['POST'])
@login_required
def quitar_saldo(saldo_id):
    if not current_user.is_gerenciador(): abort(403)
    saldo = SaldoMensal.query.get_or_404(saldo_id)
    try:
        if saldo.status_pagamento == 'pendente':
            saldo.status_pagamento = 'quitado'
            flash(f'Saldo de {saldo.usuario.username} marcado como quitado!', 'success')
        else:
            saldo.status_pagamento = 'pendente'
            flash(f'Saldo de {saldo.usuario.username} marcado como pendente!', 'warning')
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar status do saldo: {e}', 'danger')
    return redirect(url_for('financas.ver_relatorio', fechamento_id=saldo.fechamento_id))

# --- ROTAS DE GRÁFICOS ---
@financas_bp.route('/graficos')
@login_required
def dashboard_graficos():
    hoje = datetime.utcnow()
    # Pega mês/ano do request ou usa o atual
    mes_filtro = request.args.get('mes', default=hoje.month, type=int)
    ano_filtro = request.args.get('ano', default=hoje.year, type=int)

    # Gráfico de Pizza: Gastos Variáveis por Categoria no mês filtrado
    gastos_variaveis_categoria = db.session.query(
        Lancamento.categoria, func.sum(Lancamento.valor)
    ).filter(
        Lancamento.mes_referencia == mes_filtro,
        Lancamento.ano_referencia == ano_filtro,
    ).group_by(Lancamento.categoria).all()

    dados_categoria_variavel = {
        'labels': [c[0] if c[0] else 'Sem Categoria' for c in gastos_variaveis_categoria],
        'data': [float(c[1]) if c[1] else 0.0 for c in gastos_variaveis_categoria]
    }

    # Gráfico de Barras: Gasto Total Real (Fixo Outros + Variável Casa + Aluguel Pago) por Mês (Histórico)
    gasto_total_real_mes = db.session.query(
        FechamentoMensal.ano, FechamentoMensal.mes,
        (FechamentoMensal.total_fixo + FechamentoMensal.total_variavel + FechamentoMensal.total_aluguel_mes).label('gasto_real')
    ).filter_by(status='fechado').order_by(FechamentoMensal.ano, FechamentoMensal.mes).all()

    dados_historico_total = {
        'labels': [f"{m[1]:02d}/{m[0]}" for m in gasto_total_real_mes],
        'data': [float(m[2]) if m[2] else 0.0 for m in gasto_total_real_mes]
    }

    # Pega meses/anos que têm dados fechados para o dropdown do filtro
    meses_com_dados_fechados = db.session.query(
        FechamentoMensal.ano, FechamentoMensal.mes
    ).filter_by(status='fechado').distinct().order_by(FechamentoMensal.ano.desc(), FechamentoMensal.mes.desc()).all()

    return render_template('dashboard_graficos.html',
                           dados_categoria=dados_categoria_variavel,
                           dados_historico=dados_historico_total,
                           mes_filtro=mes_filtro,
                           ano_filtro=ano_filtro,
                           meses_com_dados=meses_com_dados_fechados)