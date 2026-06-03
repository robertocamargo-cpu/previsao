import re

with open('automacao_previsao.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update sheet targeting
content = content.replace('"13 05 2026"', '"14 05 2026"')
content = content.replace('datetime(2026, 5, 13)', 'datetime(2026, 5, 14)')
content = content.replace('Aba 13 05 2026', 'Aba 14 05 2026')

# Update F
content = content.replace("mask_f = (df_f['ttr_data_vencimento'] == pd.Timestamp('2026-05-14'))", "mask_f = (df_f['ttr_data_vencimento'] == pd.Timestamp('2026-05-15'))")
content = content.replace("Receber 13/05", "Receber 14/05")
content = content.replace("Receber 14/05 (sem ajuste)", "Receber 15/05 (sem ajuste)")
content = content.replace("14/05 Receber", "15/05 Receber")

# Update G
content = content.replace("mask_g = (df_g['ttp_data_vencimento'] == pd.Timestamp('2026-05-15'))", "mask_g = (df_g['ttp_data_vencimento'].isin([pd.Timestamp('2026-05-16'), pd.Timestamp('2026-05-17'), pd.Timestamp('2026-05-18')]))")
content = content.replace("Pagar 14/05", "Pagar 15/05")
content = content.replace("Pagar 15/05 (sem ajuste)", "Pagar 16+17+18/05 (soma)")
content = content.replace("15/05 Pagar", "16+17+18/05 Pagar")

# Update J
content = content.replace("mask_j = (df_j['ttr_data_vencimento'] == pd.Timestamp('2026-05-15'))", "mask_j = (df_j['ttr_data_vencimento'] == pd.Timestamp('2026-05-18'))")
content = content.replace("Receber 15/05", "Receber 18/05")
content = content.replace("15/05 Receber", "18/05 Receber")

# Update K
content = content.replace("datas = [pd.Timestamp('2026-05-16'), pd.Timestamp('2026-05-17'), pd.Timestamp('2026-05-18')]", "datas = [pd.Timestamp('2026-05-19')]")
content = content.replace("Soma de 16, 17 e 18/05", "Soma de 19/05")
content = content.replace("Pagar 16+17+18/05", "Pagar 19/05")
content = content.replace("16+17+18/05 Pagar", "19/05 Pagar")

# Update C
content = content.replace("mask_c = (df_c['ttp_data_vencimento'] == pd.Timestamp('2026-05-14'))", "mask_c = (df_c['ttp_data_vencimento'] == pd.Timestamp('2026-05-15'))")
content = content.replace("Pagar 14/05", "Pagar 15/05")
content = content.replace("14/05 Pagar", "15/05 Pagar")

# Update M
content = content.replace("mask = (df['ttr_data_vencimento'] == pd.Timestamp('2026-05-13'))", "mask = (df['ttr_data_vencimento'] == pd.Timestamp('2026-05-14'))")
# Receber 13/05 -> Receber 14/05 already handled above, but let's be careful.
content = content.replace("Valores para M (13/05 Receber)", "Valores para M (14/05 Receber)")

with open('automacao_previsao.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated automacao_previsao.py")
