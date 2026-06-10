import os
import zipfile
import pandas as pd
from datetime import datetime, timedelta
from automacao_previsao import is_dia_util, clean_currency

BASE_DIR = r"c:\Users\finan\OneDrive\Área de Trabalho\Previsao"

def get_valores(file_path, date_col, value_col, saldo_col, filial_col, data_obj):
    df_list = []
    with zipfile.ZipFile(file_path, 'r') as z:
        for filename in z.namelist():
            if filename.endswith('.csv'):
                with z.open(filename) as f:
                    df_part = pd.read_csv(f, sep=';', encoding='latin-1', on_bad_lines='skip')
                    df_list.append(df_part)
    df = pd.concat(df_list, ignore_index=True)
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df[value_col] = df[value_col].apply(clean_currency).fillna(0)
    df[saldo_col] = df[saldo_col].apply(clean_currency).fillna(0)
    df = df[df[saldo_col] > 0]
    mask = (df[date_col] == pd.Timestamp(data_obj))
    df_filtered = df[mask].copy()
    return df_filtered.groupby(filial_col)[value_col].sum().to_dict()

FILIAIS_USADAS = ["302", "429", "551", "601", "Nevine"]

if __name__ == '__main__':
    hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Hoje + próximos 3 dias úteis
    dias = [hoje]
    curr = hoje
    while len(dias) < 4:
        curr += timedelta(days=1)
        if is_dia_util(curr):
            dias.append(curr)
    
    file_receber = os.path.join(BASE_DIR, "titulos a receber.zip")
    file_pagar = os.path.join(BASE_DIR, "titulos a pagar.zip")
    
    for d in dias:
        d_str = d.strftime('%d/%m/%Y')
        receber_raw = get_valores(file_receber, 'ttr_data_vencimento', 'ttr_valor_titulo', 'ttr_saldo', 'fil_descricao', d)
        pagar_raw = get_valores(file_pagar, 'ttp_data_vencimento', 'ttp_valor_titulo', 'ttp_saldo', 'fil_descricao', d)
        receber = {k: v for k, v in receber_raw.items() if k in FILIAIS_USADAS}
        pagar = {k: v for k, v in pagar_raw.items() if k in FILIAIS_USADAS}
        
        label = "(HOJE)" if d == hoje else ""
        print(f"\nData: {d_str} {label}")
        print("  Receber:")
        if receber:
            for filial, valor in sorted(receber.items()):
                print(f"    {filial}: R$ {valor:,.2f}")
        else:
            print("    (nenhum)")
        print("  Pagar:")
        if pagar:
            for filial, valor in sorted(pagar.items()):
                print(f"    {filial}: R$ {valor:,.2f}")
        else:
            print("    (nenhum)")
