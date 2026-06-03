import zipfile
import pandas as pd

def clean_currency(x):
    if isinstance(x, str):
        return float(x.replace('.', '').replace(',', '.'))
    return x

file_receber = r'C:\Users\finan\OneDrive\Área de Trabalho\Previsao\titulos a receber.zip'

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

# 12/05 sem ajuste
mask = (df['ttr_data_vencimento'] == pd.Timestamp('2026-05-12')) & (df['ttr_saldo'] > 0)
df_filtered = df[mask].copy()

print('=== REGISTROS DE 12/05 (SEM AJUSTE) ===')
for idx, row in df_filtered.iterrows():
    print(f"Filial: {row['fil_descricao']} | Valor: {row['ttr_valor_titulo']:.2f}")

print()
print('=== TOTAL POR FILIAL ===')
totals = df_filtered.groupby('fil_descricao')['ttr_valor_titulo'].sum().to_dict()
for k, v in totals.items():
    print(f'{k}: {v:.2f}')