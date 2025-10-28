# app/financas/routes_aluguel.py (VERSÃO CORRIGIDA)

from flask import render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import func

# 1. Importa o Blueprint, constantes e o db
from . import financas_bp, db, CHAVE_ALUGUEL, CHAVE_CAIXINHA
# --- CORREÇÃO AQUI: 'ValorAluguel' foi removido ---
from ..models import User, DespesaFixa 

# --- FUNÇÃO HELPER PARA ATUALIZAR ALUGUEIS ---
def recalcular_e_atualizar_alugueis(aluguel_total, diferenca):
    """
    Calcula e salva o valor do aluguel individual de cada morador
    na tabela DespesaFixa.
    """
    
    moradores = User.query.filter(User.cargo != 'admin').all() 
    
    if not moradores:
        flash('Nenhum morador (não-admin) encontrado para calcular.', 'warning')
        return (None, None)

    Ntotal = len(moradores)
    n1 = User.query.filter(User.cargo != 'admin', User.tipo_quarto == 'individual').count()

    try:
        if Ntotal == 0: 
            raise ZeroDivisionError

        aluguel_compartilhado = (aluguel_total - diferenca * n1) / Ntotal
        aluguel_individual = aluguel_compartilhado + diferenca

        aluguel_compartilhado = round(aluguel_compartilhado, 2)
        aluguel_individual = round(aluguel_individual, 2)

    except ZeroDivisionError:
        flash('Erro: Não há moradores para dividir o aluguel.', 'danger')
        return (None, None)

    for morador in moradores:
        valor_a_pagar = aluguel_individual if morador.tipo_quarto == 'individual' else aluguel_compartilhado
        
        despesa_aluguel_morador = DespesaFixa.query.filter_by(
            descricao=CHAVE_ALUGUEL, 
            morador_id=morador.id
        ).first()

        if despesa_aluguel_morador:
            despesa_aluguel_morador.valor = valor_a_pagar
            despesa_aluguel_morador.ativa = True
        else:
            nova_despesa_aluguel = DespesaFixa(
                descricao=CHAVE_ALUGUEL,
                valor=valor_a_pagar,
                morador_id=morador.id,
                ativa=True
            )
            db.session.add(nova_despesa_aluguel)

    db.session.commit()
    
    return (aluguel_individual, aluguel_compartilhado)


# --- ROTA GERENCIAR ALUGUEL ---
@financas_bp.route('/gerenciar_aluguel', methods=['GET', 'POST'])
@login_required
def gerenciar_aluguel():
    if not current_user.is_gerenciador():
        abort(403)

    aluguel_master = DespesaFixa.query.filter_by(descricao=CHAVE_ALUGUEL, morador_id=None).first()

    if not aluguel_master:
        aluguel_master = DespesaFixa(descricao=CHAVE_ALUGUEL, valor=0.0, diferenca_individual=0.0, ativa=False)
        db.session.add(aluguel_master)
        db.session.commit() 

    if request.method == 'POST':
        aluguel_total_form = request.form.get('aluguel_total', type=float)
        diferenca_form = request.form.get('diferenca_individual', type=float)

        aluguel_master.valor = aluguel_total_form
        aluguel_master.diferenca_individual = diferenca_form
        db.session.commit()

        recalcular_e_atualizar_alugueis(aluguel_total_form, diferenca_form)
        
        flash('Valores do aluguel salvos e despesas individuais atualizadas!', 'success')
        return redirect(url_for('financas.gerenciar_aluguel'))

    moradores = User.query.filter(User.cargo != 'admin').all()
    valor_individual_calc = None
    valor_compartilhado_calc = None
    n1 = 0
    Ntotal = 0
    
    if moradores:
        Ntotal = len(moradores)
        n1 = User.query.filter(User.cargo != 'admin', User.tipo_quarto == 'individual').count()
        
        if Ntotal > 0:
            try:
                valor_compartilhado_calc = (aluguel_master.valor - aluguel_master.diferenca_individual * n1) / Ntotal
                valor_individual_calc = valor_compartilhado_calc + aluguel_master.diferenca_individual
            except (ZeroDivisionError, TypeError): # Adicionado TypeError para caso os valores sejam None
                pass 

    return render_template('gerenciar_alugueis.html', 
                           config_aluguel=aluguel_master,
                           valor_individual=valor_individual_calc,
                           valor_compartilhado=valor_compartilhado_calc,
                           n_individuais=n1,
                           n_compartilhados=Ntotal - n1
                           )

# --- ROTAS GERENCIAR FIXAS (CORRIGIDA) ---
@financas_bp.route('/gerenciar_fixas')
@login_required
def gerenciar_despesas_fixas():
    if not current_user.is_gerenciador(): abort(403)
    
    # Simplesmente pegamos todas as despesas.
    despesas = DespesaFixa.query.order_by(DespesaFixa.ativa.desc(), DespesaFixa.descricao).all()
    
    # --- LÓGICA VIRTUAL REMOVIDA ---

    return render_template(
        'gerenciar_fixas.html',
        despesas=despesas,
        CHAVE_ALUGUEL=CHAVE_ALUGUEL,
        CHAVE_CAIXINHA=CHAVE_CAIXINHA
    )

@financas_bp.route('/gerenciar_fixas/adicionar', methods=['POST'])
@login_required
def adicionar_despesa_fixa():
    if not current_user.is_gerenciador(): abort(403)
    descricao = request.form.get('descricao')
    valor_str = request.form.get('valor')
    if not descricao or not valor_str:
         flash('Descrição e valor são obrigatórios.', 'danger')
         return redirect(url_for('financas.gerenciar_despesas_fixas'))
    try:
        valor = float(valor_str.replace(',', '.'))
        if valor < 0:
             flash('O valor da despesa fixa não pode ser negativo.', 'danger')
             return redirect(url_for('financas.gerenciar_despesas_fixas'))
        existe = DespesaFixa.query.filter(func.lower(DespesaFixa.descricao) == func.lower(descricao)).first()
        if existe:
            flash(f'Já existe uma despesa fixa chamada "{descricao}".', 'warning')
            return redirect(url_for('financas.gerenciar_despesas_fixas'))
        nova_despesa = DespesaFixa(descricao=descricao, valor=valor, ativa=True)
        db.session.add(nova_despesa)
        db.session.commit()
        flash('Despesa fixa adicionada.', 'success')
    except ValueError:
        flash('Valor inválido.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao adicionar despesa: {e}', 'danger')
    return redirect(url_for('financas.gerenciar_despesas_fixas'))

@financas_bp.route('/gerenciar_fixas/editar/<int:despesa_id>', methods=['POST'])
@login_required
def editar_despesa_fixa(despesa_id):
    # --- CORREÇÃO AQUI: 4G03 -> 403 ---
    if not current_user.is_gerenciador(): abort(403)
    # --- FIM DA CORREÇÃO ---
    
    despesa = DespesaFixa.query.get_or_404(despesa_id)
    nova_descricao = request.form.get(f'descricao-{despesa.id}')
    novo_valor_str = request.form.get(f'valor-{despesa.id}')
    if not nova_descricao or not novo_valor_str:
         flash('Descrição e valor não podem ficar em branco.', 'danger')
         return redirect(url_for('financas.gerenciar_despesas_fixas'))
    
    # Impede renomear PARA 'Aluguel' ou editar aluguel individual aqui
    if CHAVE_ALUGUEL.lower() in nova_descricao.lower() or CHAVE_ALUGUEL.lower() in despesa.descricao.lower():
         flash(f"A despesa '{CHAVE_ALUGUEL}' é gerenciada na página 'Gerenciar Aluguel'. Não edite por aqui.", 'warning')
         return redirect(url_for('financas.gerenciar_despesas_fixas'))

    try:
        novo_valor = float(novo_valor_str.replace(',', '.'))
        if novo_valor < 0:
             flash('O valor da despesa fixa não pode ser negativo.', 'danger')
             return redirect(url_for('financas.gerenciar_despesas_fixas'))

        # Verifica duplicidade apenas entre despesas GERAIS
        existe_outra = DespesaFixa.query.filter(
            func.lower(DespesaFixa.descricao) == func.lower(nova_descricao),
            DespesaFixa.id != despesa_id,
            DespesaFixa.morador_id == None # Só compara com outras gerais
        ).first()
        if existe_outra and despesa.morador_id is None: # Só barra se a atual também for geral
            flash(f'Já existe outra despesa fixa geral chamada "{nova_descricao}".', 'warning')
            return redirect(url_for('financas.gerenciar_despesas_fixas'))

        despesa.descricao = nova_descricao
        despesa.valor = novo_valor
        db.session.commit()
        flash(f'Despesa "{despesa.descricao}" atualizada!', 'success')
    except ValueError:
        flash('Valor inválido.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar despesa: {e}', 'danger')
    return redirect(url_for('financas.gerenciar_despesas_fixas'))

@financas_bp.route('/gerenciar_fixas/alternar_status/<int:despesa_id>', methods=['POST'])
@login_required
def alternar_status_despesa_fixa(despesa_id):
    if not current_user.is_gerenciador(): abort(403)
    despesa = DespesaFixa.query.get_or_404(despesa_id)
    try:
        despesa.ativa = not despesa.ativa
        db.session.commit()
        status = "reativada" if despesa.ativa else "desativada"
        flash(f'Despesa "{despesa.descricao}" foi {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao alterar status da despesa: {e}', 'danger')
    return redirect(url_for('financas.gerenciar_despesas_fixas'))

@financas_bp.route('/gerenciar_fixas/deletar_permanente/<int:despesa_id>', methods=['POST'])
@login_required
def deletar_despesa_fixa_permanente(despesa_id):
    if not current_user.is_admin(): # Somente Admin
        abort(403) 
    despesa = DespesaFixa.query.get_or_404(despesa_id)
    try:
        if (CHAVE_ALUGUEL in despesa.descricao or CHAVE_CAIXINHA in despesa.descricao) and despesa.morador_id is None:
             flash(f'Despesas essenciais/mestre como "{despesa.descricao}" não podem ser deletadas permanentemente.', 'warning')
             return redirect(url_for('financas.gerenciar_despesas_fixas'))
        desc_temp = despesa.descricao
        db.session.delete(despesa)
        db.session.commit()
        flash(f'Despesa "{desc_temp}" DELETADA PERMANENTEMENTE.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar despesa: {e}', 'danger')
    return redirect(url_for('financas.gerenciar_despesas_fixas'))