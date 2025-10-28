# app/financas/routes_lancamentos.py

import uuid
from dateutil.relativedelta import relativedelta
from flask import render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from datetime import datetime

# 1. Importa o Blueprint do __init__.py desta pasta
from . import financas_bp

# 2. Importa os modelos e o db subindo um nível
from ..models import db, User, Lancamento, FechamentoMensal

# --- ROTA PARA ADICIONAR GASTO ---
@financas_bp.route('/adicionar_gasto', methods=['GET', 'POST'])
@login_required
def adicionar_gasto():
    # --- DEFINIÇÕES INICIAIS ---
    categorias_validas = ['Mercado', 'Contas', 'Lazer', 'Manutenção', 'Parcelado', 'Outros']
    usuarios_moradores = []
    if current_user.is_gerenciador():
        usuarios_moradores = User.query.filter(User.cargo != 'admin').order_by(User.username).all()

    # --- DEBUG: Ver método ---
    print(f"Método da Requisição: {request.method}")
    # --- TESTE FLASH ---
    # flash("TESTE: Flash está funcionando!", "info") # Pode remover ou comentar depois de testar

    # --- INÍCIO DA LÓGICA DO POST ---
    if request.method == 'POST':
        # --- DEBUG: Ver dados recebidos ---
        print("Dados recebidos do formulário:")
        print(request.form)

        # Pega os dados do formulário
        descricao = request.form.get('descricao')
        valor_total_str = request.form.get('valor')
        categoria = request.form.get('categoria', 'Outros')
        num_parcelas_str = request.form.get('num_parcelas', '1')
        pagador_selecionado = request.form.get('pagador', 'casa')

        # Validação: Descrição e Valor
        if not descricao or not valor_total_str:
            print("!!! Erro de Validação: Descrição ou Valor ausentes.")
            flash('Descrição e Valor são obrigatórios.', 'danger')
            return render_template('adicionar_gasto.html', categorias=categorias_validas, usuarios_moradores=usuarios_moradores, descricao=descricao, valor=valor_total_str, num_parcelas=num_parcelas_str, pagador_selecionado=pagador_selecionado)

        # Validação: Conversão de Valor e Parcelas
        try:
            valor_total = float(valor_total_str.replace(',', '.'))
            num_parcelas = int(num_parcelas_str) if num_parcelas_str else 1
            if valor_total <= 0:
                  print("!!! Erro de Validação: Valor não positivo.")
                  flash('O valor do gasto deve ser positivo.', 'danger')
                  return render_template('adicionar_gasto.html', categorias=categorias_validas, usuarios_moradores=usuarios_moradores, descricao=descricao, valor=valor_total_str, num_parcelas=num_parcelas_str, pagador_selecionado=pagador_selecionado)
            if num_parcelas < 1:
                  num_parcelas = 1 # Corrige se for menor que 1
        except ValueError:
            print("!!! Erro de Validação: ValueError ao converter valor/parcelas.")
            flash('Valor ou Número de Parcelas inválido.', 'danger')
            return render_template('adicionar_gasto.html', categorias=categorias_validas, usuarios_moradores=usuarios_moradores, descricao=descricao, valor=valor_total_str, num_parcelas=num_parcelas_str, pagador_selecionado=pagador_selecionado)

        # Lógica do Pagador (quem recebe o crédito)
        lancamento_user_id = None
        if current_user.is_gerenciador():
            if pagador_selecionado == 'casa':
                lancamento_user_id = None
            else:
                try:
                    lancamento_user_id = int(pagador_selecionado)
                    user_destino = User.query.get(lancamento_user_id)
                    if not user_destino or user_destino.cargo == 'admin':
                        print("!!! Erro de Validação: Pagador selecionado inválido (não encontrado ou admin).")
                        flash('Pagador selecionado é inválido.', 'danger')
                        return render_template('adicionar_gasto.html', categorias=categorias_validas, usuarios_moradores=usuarios_moradores, descricao=descricao, valor=valor_total_str, num_parcelas=num_parcelas_str, pagador_selecionado=pagador_selecionado)
                except ValueError:
                    print("!!! Erro de Validação: ValueError ao converter ID do pagador.")
                    flash('Seleção de pagador inválida.', 'danger')
                    return render_template('adicionar_gasto.html', categorias=categorias_validas, usuarios_moradores=usuarios_moradores, descricao=descricao, valor=valor_total_str, num_parcelas=num_parcelas_str, pagador_selecionado=pagador_selecionado)
        else: # Usuário normal só lança em nome próprio
            lancamento_user_id = current_user.id

        # Lógica de Parcelamento e Criação dos Lançamentos
        hoje = datetime.utcnow()
        valor_parcela_base = round(valor_total / num_parcelas, 2)
        diferenca_total = round(valor_total - (valor_parcela_base * num_parcelas), 2)
        parcelamento_uuid = str(uuid.uuid4()) if num_parcelas > 1 else None
        lancamentos_a_criar = []

        try:
            for i in range(num_parcelas):
                parcela_num = i + 1
                data_referencia = hoje + relativedelta(months=i)
                valor_desta_parcela = valor_parcela_base
                # Ajusta a última parcela para compensar arredondamento
                if parcela_num == num_parcelas:
                    valor_desta_parcela = round(valor_parcela_base + diferenca_total, 2)

                desc_parcela = descricao
                if num_parcelas > 1:
                    desc_parcela = f"{descricao} ({parcela_num}/{num_parcelas})"

                novo_lancamento = Lancamento(
                    descricao=desc_parcela,
                    valor=valor_desta_parcela,
                    categoria=categoria,
                    data=hoje,
                    mes_referencia=data_referencia.month,
                    ano_referencia=data_referencia.year,
                    user_id=lancamento_user_id, # ID do pagador
                    parcelamento_id=parcelamento_uuid,
                    parcela_atual=parcela_num if num_parcelas > 1 else None,
                    parcela_total=num_parcelas if num_parcelas > 1 else None,
                    valor_total_compra=valor_total if num_parcelas > 1 else None
                )
                lancamentos_a_criar.append(novo_lancamento)

            # Salva no Banco de Dados
            print("--- Preparando para salvar no banco ---")
            db.session.add_all(lancamentos_a_criar)
            db.session.commit()
            print("--- Salvo no banco com sucesso! ---")
            flash(f'Gasto {"parcelado " if num_parcelas > 1 else ""}adicionado com sucesso!', 'success')

        except Exception as e:
            db.session.rollback()
            print(f"!!! Erro ao salvar no banco: {e}")
            flash(f'Erro ao adicionar gasto: {e}', 'danger')
            # Redireciona mesmo em caso de erro no DB para não travar
            if current_user.is_gerenciador():
                return redirect(url_for('financas.dashboard_tesoureiro'))
            else:
                return redirect(url_for('financas.dashboard_usuario'))


        # Redireciona para o dashboard correto APÓS SUCESSO
        print("--- Redirecionando para o dashboard ---")
        if current_user.is_gerenciador():
            return redirect(url_for('financas.dashboard_tesoureiro'))
        else:
            return redirect(url_for('financas.dashboard_usuario'))
    # --- FIM DA LÓGICA DO POST ---


    # --- Lógica do GET ---
    # Só chega aqui se request.method != 'POST'
    return render_template('adicionar_gasto.html',
                           categorias=categorias_validas,
                           usuarios_moradores=usuarios_moradores)
# --- ROTAS EDITAR/DELETAR LANCAMENTOS (ADICIONADAS) ---

@financas_bp.route('/lancamento/editar/<int:lancamento_id>', methods=['GET', 'POST'])
@login_required
def editar_lancamento(lancamento_id):
    categorias_validas = ['Mercado', 'Contas', 'Lazer', 'Manutenção', 'Parcelado', 'Outros']
    
    lancamento = Lancamento.query.get_or_404(lancamento_id)
    usuarios_moradores = []

    if not current_user.is_gerenciador() and lancamento.user_id != current_user.id:
        flash('Você não tem permissão para editar este lançamento.', 'danger')
        abort(403) 

    fechamento = FechamentoMensal.query.filter_by(
        mes=lancamento.mes_referencia, ano=lancamento.ano_referencia, status='fechado'
    ).first()
    if fechamento:
        flash('Não é possível editar lançamentos de um mês já fechado.', 'warning')
        return redirect(url_for('financas.ver_relatorio', fechamento_id=fechamento.id))

    if current_user.is_gerenciador():
        usuarios_moradores = User.query.filter(User.cargo != 'admin').order_by(User.username).all()

    if request.method == 'POST':
        if lancamento.is_parcelado():
              flash('Edição limitada para parcelas. Apenas descrição, valor desta parcela, categoria e pagador podem ser alterados.', 'info')

        try:
            valor_str = request.form.get('valor')
            valor_parcela = float(valor_str.replace(',', '.'))
            if valor_parcela <= 0:
                flash('O valor da parcela deve ser positivo.', 'danger')
                return render_template('editar_lancamento.html',
                                       lancamento=lancamento,
                                       categorias=categorias_validas,
                                       usuarios_moradores=usuarios_moradores)

            lancamento.descricao = request.form.get('descricao')
            lancamento.valor = valor_parcela
            lancamento.categoria = request.form.get('categoria')

            if current_user.is_gerenciador():
                pagador_selecionado = request.form.get('pagador', 'casa') 
                if pagador_selecionado == 'casa':
                    lancamento.user_id = None 
                else:
                    try:
                        user_id_int = int(pagador_selecionado)
                        user_destino = User.query.get(user_id_int)
                        if user_destino and user_destino.cargo != 'admin':
                             lancamento.user_id = user_id_int 
                        else:
                             raise ValueError("Usuário inválido")
                    except ValueError:
                        flash('Pagador selecionado é inválido.', 'danger')
                        return render_template('editar_lancamento.html',
                                               lancamento=lancamento,
                                               categorias=categorias_validas,
                                               usuarios_moradores=usuarios_moradores)
            
            db.session.commit()
            flash('Lançamento atualizado com sucesso!', 'success')
            if current_user.is_gerenciador():
                   return redirect(url_for('financas.dashboard_tesoureiro'))
            else:
                   return redirect(url_for('financas.dashboard_usuario'))

        except ValueError:
             flash('Valor inválido.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar: {e}', 'danger')

    return render_template('editar_lancamento.html',
                           lancamento=lancamento,
                           categorias=categorias_validas,
                           usuarios_moradores=usuarios_moradores)


@financas_bp.route('/lancamento/deletar/<int:lancamento_id>', methods=['POST'])
@login_required
def deletar_lancamento(lancamento_id):
    lancamento = Lancamento.query.get_or_404(lancamento_id)

    if not current_user.is_gerenciador() and lancamento.user_id != current_user.id:
        flash('Você não tem permissão para deletar este lançamento.', 'danger')
        abort(403) 

    fechamento = FechamentoMensal.query.filter_by(
        mes=lancamento.mes_referencia, ano=lancamento.ano_referencia, status='fechado'
    ).first()
    if fechamento:
        flash('Não é possível deletar lançamentos de um mês já fechado.', 'warning')
        return redirect(url_for('financas.ver_relatorio', fechamento_id=fechamento.id))

    try:
        parcelamento_id = lancamento.parcelamento_id
        parcela_atual = lancamento.parcela_atual
        parcela_total = lancamento.parcela_total

        db.session.delete(lancamento)
        db.session.commit()

        msg = 'Lançamento removido com sucesso.'
        if parcelamento_id:
              msg = f'Parcela {parcela_atual}/{parcela_total} removida com sucesso. As outras parcelas (se houver) permanecem.'
              flash(msg, 'success')
        else:
            flash(msg, 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao remover: {e}', 'danger')

    if current_user.is_gerenciador():
         return redirect(url_for('financas.dashboard_tesoureiro'))
    else:
         return redirect(url_for('financas.dashboard_usuario'))