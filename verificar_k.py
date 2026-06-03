import zipfile
import pandas as pd

def clean_currency(x):
    if isinstance(x, str):
        return float(x.replace('.', '').replace(',', '.'))
    return x

file_pagar = r'C:\Users\finan\OneDrive\Área de Trabalho\Previsao\titulos a pagar.zip'

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

mask = (df['ttp_data_vencimento'] == pd.Timestamp('2026-05-15')) & (df['ttp_saldo'] > 0)
df_filtered = df[mask].copy()

print('=== TODOS OS REGISTROS DE 15/05 ===')
for idx, row in df_filtered.iterrows():
    print(f"Filial: {row['fil_descricao']} | Valor: {row['ttp_valor_titulo']:.2f} | Saldo: {row['ttp_saldo']:.2f}")

print()
print('=== TOTAL POR FILIAL ===')
totals = df_filtered.groupby('fil_descricao')['ttp_valor_titulo'].sum().to_dict()
for k, v in totals.items():
    print(f'{k}: {v:.2f}')