import re

with open('automacao_previsao.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update J to sum 16, 17, and 18
content = content.replace(
    "mask_j = (df_j['ttr_data_vencimento'] == pd.Timestamp('2026-05-18'))", 
    "mask_j = (df_j['ttr_data_vencimento'].isin([pd.Timestamp('2026-05-16'), pd.Timestamp('2026-05-17'), pd.Timestamp('2026-05-18')]))"
)
content = content.replace("Valores para J (18/05 Receber)", "Valores para J (16+17+18/05 Receber)")

with open('automacao_previsao.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated J in automacao_previsao.py")
