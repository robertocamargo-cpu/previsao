import os, zipfile, pandas as pd

BASE_DIR = r'C:\Users\finan\OneDrive\Área de Trabalho\Previsao'

def clean_currency(v):
    if isinstance(v, str):
        v = v.replace('.', '').replace(',', '.')
    try:
        return float(v)
    except Exception:
        return 0.0

file_receber = os.path.join(BASE_DIR, 'titulos a receber.zip')

df_list = []
with zipfile.ZipFile(file_receber, 'r') as z:
    for fn in z.namelist():
        if fn.lower().endswith('.csv'):
            with z.open(fn) as f:
                df_part = pd.read_csv(f, sep=';', encoding='latin-1', on_bad_lines='skip')
                df_list.append(df_part)

df = pd.concat(df_list, ignore_index=True)

df['ttr_data_vencimento'] = pd.to_datetime(df['ttr_data_vencimento'], dayfirst=True, errors='coerce')

df['ttr_valor_titulo'] = df['ttr_valor_titulo'].apply(clean_currency).fillna(0)

df['ttr_saldo'] = df['ttr_saldo'].apply(clean_currency).fillna(0)
# keep only positive saldo
df = df[df['ttr_saldo'] > 0]

today = pd.Timestamp('2026-05-21')
mask = df['ttr_data_vencimento'] == today
vals = df[mask].groupby('fil_descricao')['ttr_valor_titulo'].sum().to_dict()
print('Valores M (recebíveis 21/05):', vals)
