import os
import zipfile
import pandas as pd
from datetime import datetime

BASE_DIR = r"C:\\Users\\finan\\OneDrive\\Área de Trabalho\\Previsao"

def clean_currency(x):
    if isinstance(x, str):
        return float(x.replace('.', '').replace(',', '.'))
    return x

def get_valores_receber(data_obj):
    file_receber = os.path.join(BASE_DIR, "titulos a receber.zip")
    df_list = []
    with zipfile.ZipFile(file_receber, 'r') as z:
        for filename in z.namelist():
            if filename.endswith('.csv'):
                with z.open(filename) as f:
                    df_part = pd.read_csv(f, sep=';', encoding='latin-1', on_bad_lines='skip')
                    df_list.append(df_part)
    df = pd.concat(df_list, ignore_index=True)
    df['ttr_data_vencimento'] = pd.to_datetime(df['ttr_data_vencimento'], dayfirst=True, errors='coerce')
    df['ttr_valor_titulo'] = df['ttr_valor_titulo'].apply(clean_currency).fillna(0)
    df['ttr_saldo'] = df['ttr_saldo'].apply(clean_currency).fillna(0)
    df = df[df['ttr_saldo'] > 0]
    mask = (df['ttr_data_vencimento'] == pd.Timestamp(data_obj))
    df_filtered = df[mask].copy()
    return df_filtered.groupby('fil_descricao')['ttr_valor_titulo'].sum().to_dict()

def get_valores_pagar(data_obj):
    file_pagar = os.path.join(BASE_DIR, "titulos a pagar.zip")
    df_list = []
    with zipfile.ZipFile(file_pagar, 'r') as z:
        for filename in z.namelist():
            if filename.endswith('.csv'):
                with z.open(filename) as f:
                    df_part = pd.read_csv(f, sep=';', encoding='latin-1', on_bad_lines='skip')
                    df_list.append(df_part)
    df = pd.concat(df_list, ignore_index=True)
    df['ttp_data_vencimento'] = pd.to_datetime(df['ttp_data_vencimento'], dayfirst=True, errors='coerce')
    df['ttp_valor_titulo'] = df['ttp_valor_titulo'].apply(clean_currency).fillna(0)
    df['ttp_saldo'] = df['ttp_saldo'].apply(clean_currency).fillna(0)
    df = df[df['ttp_saldo'] > 0]
    mask = (df['ttp_data_vencimento'] == pd.Timestamp(data_obj))
    df_filtered = df[mask].copy()
    return df_filtered.groupby('fil_descricao')['ttp_valor_titulo'].sum().to_dict()

if __name__ == '__main__':
    hoje = datetime.now().date()
    receber = get_valores_receber(hoje)
    pagar = get_valores_pagar(hoje)
    print(f"Previsão para {hoje.strftime('%d/%m/%Y')}")
    print('Receber:', receber)
    print('Pagar:', pagar)
