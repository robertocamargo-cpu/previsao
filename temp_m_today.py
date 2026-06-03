import zipfile, pandas as pd, os
BASE_DIR = r'C:\Users\finan\OneDrive\Área de Trabalho\Previsao'

def clean_currency(v):
    if isinstance(v, str):
        v = v.replace('.', '').replace(',', '.')
    try:
        return float(v)
    except:
        return 0.0

file_receber = os.path.join(BASE_DIR, 'titulos a receber.zip')

df_list = []
with zipfile.ZipFile(file_receber, 'r') as z:
    for fn in z.namelist():
        if fn.endswith('.csv'):
            with z.open(fn) as f:
                df_part = pd.read_csv(f, sep=';', encoding='latin-1', on_bad_lines='skip')
                df_list.append(df_part)

df = pd.concat(df_list, ignore_index=True)
# limpeza
if 'ttr_valor_titulo' in df.columns:
    df['ttr_valor_titulo'] = df['ttr_valor_titulo'].apply(clean_currency).fillna(0)
if 'ttr_saldo' in df.columns:
    df['ttr_saldo'] = df['ttr_saldo'].apply(clean_currency).fillna(0)
# filtrar saldo positivo
if 'ttr_saldo' in df.columns:
    df = df[df['ttr_saldo'] > 0]
# data de hoje
import datetime
hoje = datetime.date(2026, 5, 21)
mask = pd.to_datetime(df['ttr_data_vencimento'], dayfirst=True, errors='coerce').dt.date == hoje
vals = df[mask].groupby('fil_descricao')['ttr_valor_titulo'].sum().to_dict()
print('M_VALS_TODAY:', vals)
