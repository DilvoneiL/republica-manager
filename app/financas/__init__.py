# app/financas/__init__.py

from flask import Blueprint
from sqlalchemy import func

# Importa os modelos do nível acima (app/models.py)
# Precisamos do db e dos modelos que a função 'get_dados_caixinha' usa.
# Adicionado 'db' para ser importado pelos outros módulos
from ..models import db, DespesaFixa, CaixinhaMovimentacao 

# --- 1. CONSTANTES GLOBAIS ---
CHAVE_CAIXINHA = 'Caixinha'
CHAVE_ALUGUEL = 'Aluguel'

# --- 2. DEFINIÇÃO DO BLUEPRINT ---
financas_bp = Blueprint('financas', 
                        __name__, 
                        url_prefix='/financas',
                        template_folder='../templates/financas') 

# --- 3. FUNÇÕES HELPER GLOBAIS ---
def get_dados_caixinha():
    """Busca o saldo atual, projeção e movimentações do caixinha."""
    saldo_inicial_de_teste = 0
    # --- FIM DO VALOR DE TESTE ---
    
    # Busca o saldo real que está salvo no banco de dados
    saldo_do_banco = db.session.query(func.sum(CaixinhaMovimentacao.valor)).scalar() or 0.0
    
    # O saldo atual agora é o valor de teste + o que estiver no banco
    saldo_atual = saldo_inicial_de_teste + saldo_do_banco
    valor_arrecadacao_mes = db.session.query(func.sum(DespesaFixa.valor)).filter(
        DespesaFixa.ativa == True,
        DespesaFixa.descricao.like(f'%{CHAVE_CAIXINHA}%'),
        DespesaFixa.morador_id == None 
    ).scalar() or 0.0
    
    movimentacoes = CaixinhaMovimentacao.query.order_by(CaixinhaMovimentacao.data.desc()).limit(10).all()
    return {
        "saldo_atual": saldo_atual,
        "projecao_proximo_mes": saldo_atual + valor_arrecadacao_mes,
        "valor_contribuicao_mensal": valor_arrecadacao_mes,
        "movimentacoes": movimentacoes
    }


# --- 4. IMPORTAÇÃO DAS ROTAS (ATUALIZADO) ---
# Importamos os módulos de rotas NO FINAL do arquivo.
from . import routes_dashboard
from . import routes_lancamentos
from . import routes_aluguel      # <-- ADICIONADO
from . import routes_fechamento   # <-- ADICIONADO