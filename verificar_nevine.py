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

# Filtrar Nevine com saldo > 0
mask = (df['fil_descricao'] == 'Nevine') & (df['ttr_saldo'] > 0)
df_nevine = df[mask].copy()

print('=== NEVINE - TODOS OS REGISTROS COM SALDO ===')
print(f"Total registros: {len(df_nevine)}")
print()

# Mostrar datas únicas de vencimento
print("Datas de vencimento únicas:")
for dt in sorted(df_nevine['ttr_data_vencimento'].unique()):
    print(f"  {dt.strftime('%d/%m/%Y')}")

print()
# Verificar registros com vencimento em 13/05
mask_13 = (df_nevine['ttr_data_vencimento'] == pd.Timestamp('2026-05-13'))
print(f"=== NEVINE com vencimento 13/05: {mask_13.sum()} registros ===")
df_13 = df_nevine[mask_13]
for idx, row in df_13.iterrows():
    print(f"  {row['ttr_data_vencimento'].strftime('%d/%m/%Y')} | Valor: {row['ttr_valor_titulo']:.2f}")

print()
# Verificar todos os registros e suas datas
print("=== NEVINE - Primeiros 20 registros ===")
for idx, row in df_nevine.head(20).iterrows():
    print(f"  Venc: {row['ttr_data_vencimento'].strftime('%d/%m/%Y')} | Valor: {row['ttr_valor_titulo']:.2f}")