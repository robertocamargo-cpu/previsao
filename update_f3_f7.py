import re

with open('automacao_previsao.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_code = """
    # Preencher F3:F7 com Pagamentos 14/05
    print(f"  -> Preenchendo F3:F7 com Pagar 14/05...")
    
    file_pagar_f3 = os.path.join(BASE_DIR, "titulos a pagar.zip")
    
    df_list_f3 = []
    with zipfile.ZipFile(file_pagar_f3, 'r') as z:
        for filename in z.namelist():
            if filename.endswith('.csv'):
                with z.open(filename) as f:
                    df_part = pd.read_csv(f, sep=';', encoding='latin-1', on_bad_lines='skip')
                    df_list_f3.append(df_part)
    df_f3 = pd.concat(df_list_f3, ignore_index=True)
    df_f3['ttp_data_vencimento'] = pd.to_datetime(df_f3['ttp_data_vencimento'], dayfirst=True, errors='coerce')
    df_f3['ttp_valor_titulo'] = df_f3['ttp_valor_titulo'].apply(clean_currency).fillna(0)
    df_f3['ttp_saldo'] = df_f3['ttp_saldo'].apply(clean_currency).fillna(0)
    df_f3 = df_f3[df_f3['ttp_saldo'] > 0]
    
    mask_f3 = (df_f3['ttp_data_vencimento'] == pd.Timestamp('2026-05-14'))
    df_filtered_f3 = df_f3[mask_f3].copy()
    valores_f3 = df_filtered_f3.groupby('fil_descricao')['ttp_valor_titulo'].sum().to_dict()
    
    print(f"Valores para F3:F7 (14/05 Pagar): {valores_f3}")
    
    map_filiais_f3 = {
        "302": 3,
        "429": 4,
        "551": 5,
        "601": 6,
        "Nevine": 7
    }
    
    for filial, linha in map_filiais_f3.items():
        filial_key = str(filial)
        val = valores_f3.get(filial_key, 0)
        if val == 0:
            try:
                val = valores_f3.get(float(filial_key), 0)
            except:
                val = 0
        
        celula = f"F{linha}"
        await page.keyboard.press("F5")
        await asyncio.sleep(1)
        await page.keyboard.type(celula)
        await page.keyboard.press("Enter")
        await asyncio.sleep(1)
        if val > 0:
            await page.keyboard.type(str(val).replace('.', ','))
        else:
            await page.keyboard.type("0")
        await page.keyboard.press("Enter")
        await asyncio.sleep(0.5)
        print(f"    {filial} {celula}: {val:.2f}")

    print("Preenchimento concluído.")
"""

content = content.replace('print("Preenchimento concluído.")', new_code)

with open('automacao_previsao.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated F3:F7 logic in automacao_previsao.py")
