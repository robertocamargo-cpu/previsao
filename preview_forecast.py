import os
import pandas as pd
from datetime import datetime, timedelta

# Ajuste de data já está definido em automacao_previsao.py
from automacao_previsao import processar_csvs, ajustar_data_receber, ajustar_data_pagar

BASE_DIR = r"C:\\Users\\finan\\OneDrive\\Área de Trabalho\\Previsao"

# Função auxiliar para obter os próximos N dias úteis a partir de hoje
def proximos_dias_uteis(n: int):
    from automacao_previsao import is_dia_util
    hoje = datetime.now().date()
    # No automacao_previsao.py, lidamos com objetos datetime, vamos instanciar assim
    cur = datetime(hoje.year, hoje.month, hoje.day)
    dias = []
    while len(dias) < n:
        cur += timedelta(days=1)
        if is_dia_util(cur):
            dias.append(cur)
    return dias

# Calcula intervalo para ler os CSVs (inclui o dia de hoje)
hoje = datetime.now().date()
fim = hoje + timedelta(days=10)  # margem suficiente

# Processa os CSVs e obtém o dicionário organizado
dados, _ = processar_csvs(hoje, fim)

# Obtém os próximos três dias úteis
dias_alvo = proximos_dias_uteis(3)

print("Previsão para os próximos 3 dias úteis:")
for d in dias_alvo:
    d_str = d.strftime('%d/%m/%Y')
    receber = dados.get(d_str, {}).get('receber', {})
    pagar = dados.get(d_str, {}).get('pagar', {})
    print(f"\nData: {d_str}")
    print("  Receber:")
    for filial, valor in receber.items():
        print(f"    {filial}: R$ {valor:,.2f}")
    print("  Pagar:")
    for filial, valor in pagar.items():
        print(f"    {filial}: R$ {valor:,.2f}")
