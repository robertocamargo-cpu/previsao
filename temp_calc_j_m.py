import zipfile, pandas as pd, os
BASE_DIR = r'C:\Users\finan\OneDrive\Área de Trabalho\Previsao'

def clean_currency(v):
    if isinstance(v, str):
        v = v.replace('.', '').replace(',', '.')
    try:
        return float(v)
    except:
        return 0.0

# Load recebíveis
receber_zip = os.path.join(BASE_DIR, 'titulos a receber.zip')
receber_frames = []
with zipfile.ZipFile(receber_zip, 'r') as z:
    for fn in z.namelist():
        if fn.endswith('.csv'):
            with z.open(fn) as f:
                df = pd.read_csv(f, sep=';', encoding='latin-1', on_bad_lines='skip')
                receber_frames.append(df)
receber = pd.concat(receber_frames, ignore_index=True)
receber['ttr_data_vencimento'] = pd.to_datetime(receber['ttr_data_vencimento'], dayfirst=True, errors='coerce')
receber['ttr_valor_titulo'] = receber['ttr_valor_titulo'].apply(clean_currency).fillna(0)
receber['ttr_saldo'] = receber['ttr_saldo'].apply(clean_currency).fillna(0)
receber = receber[receber['ttr_saldo'] > 0]

# Load pagar
pagar_zip = os.path.join(BASE_DIR, 'titulos a pagar.zip')
pagar_frames = []
with zipfile.ZipFile(pagar_zip, 'r') as z:
    for fn in z.namelist():
        if fn.endswith('.csv'):
            with z.open(fn) as f:
                df = pd.read_csv(f, sep=';', encoding='latin-1', on_bad_lines='skip')
                pagar_frames.append(df)
pagar = pd.concat(pagar_frames, ignore_index=True)
pagar['ttp_data_vencimento'] = pd.to_datetime(pagar['ttp_data_vencimento'], dayfirst=True, errors='coerce')
# columns may have different names but we only need values for M (receber de ontem) which uses receber

# Dates of interest
import datetime
j_dates = [datetime.date(2026,5,23), datetime.date(2026,5,24), datetime.date(2026,5,25)]
m_date = datetime.date(2026,5,20)

# Compute J sum per filial across the three dates
j_vals = {}
for d in j_dates:
    mask = receber['ttr_data_vencimento'].dt.date == d
    df_sel = receber[mask]
    for filial, valor in df_sel.groupby('fil_descricao')['ttr_valor_titulo'].sum().items():
        j_vals[filial] = j_vals.get(filial, 0) + valor

# Compute M (receber de ontem) for that date
m_vals = {}
mask_m = receber['ttr_data_vencimento'].dt.date == m_date
for filial, valor in receber[mask_m].groupby('fil_descricao')['ttr_valor_titulo'].sum().items():
    m_vals[filial] = valor

print('J_SUM:', j_vals)
print('M_VALS:', m_vals)
