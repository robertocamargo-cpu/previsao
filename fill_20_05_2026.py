import asyncio
import os
import zipfile
import pandas as pd
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

BASE_DIR = r"C:\Users\finan\OneDrive\Área de Trabalho\Previsao"
PLANILHA_URL = "https://docs.google.com/spreadsheets/d/1OHMAcfxKIS2UTntlB5J7Y8krmCK7JHT9miEHmbbmLE8/edit"
GOOGLE_USER = "financeiro@nevine.com.br"
GOOGLE_PASS = "FN{25}Nevin3@"

DATA_ALVO = "20/05/2026"
DATA_ALVO_OBJ = datetime(2026, 5, 20)

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
    valores = df_filtered.groupby('fil_descricao')['ttr_valor_titulo'].sum().to_dict()
    return valores

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
    valores = df_filtered.groupby('fil_descricao')['ttp_valor_titulo'].sum().to_dict()
    return valores

async def preencher_celula(page, celula, valor):
    await page.keyboard.press("F5")
    await asyncio.sleep(0.5)
    await page.keyboard.type(celula)
    await page.keyboard.press("Enter")
    await asyncio.sleep(0.5)
    if valor > 0:
        await page.keyboard.type(str(valor).replace('.', ','))
    else:
        await page.keyboard.type("0")
    await page.keyboard.press("Enter")
    await asyncio.sleep(0.3)

async def main():
    print("Extraindo dados do ERP para 20/05/2026...")
    
    valores_receber = get_valores_receber(DATA_ALVO_OBJ)
    valores_pagar = get_valores_pagar(DATA_ALVO_OBJ)
    
    print(f"Receber: {valores_receber}")
    print(f"Pagar: {valores_pagar}")
    
    map_filiais = {
        "302": 16,
        "429": 17,
        "551": 18,
        "601": 19,
        "Nevine": 20
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        page.on('dialog', lambda dialog: dialog.accept())
        
        print("Acessando planilha...")
        await page.goto(PLANILHA_URL, timeout=60000)
        await asyncio.sleep(10)
        
        if 'accounts.google.com' in page.url:
            print("Fazendo login...")
            await page.fill('input[type="email"]', GOOGLE_USER)
            await page.click('#identifierNext')
            await asyncio.sleep(3)
            await page.fill('input[type="password"]', GOOGLE_PASS)
            await page.click('#passwordNext')
            await asyncio.sleep(5)
        
        await asyncio.sleep(5)
        
        print("Procurando aba '20 05 2026'...")
        tabs = await page.query_selector_all('.docs-sheet-tab')
        aba_encontrada = False
        for tab in tabs:
            nome = await tab.inner_text()
            if '20 05 2026' in nome:
                print(f"Aba '{nome}' encontrada!")
                await tab.click()
                await asyncio.sleep(2)
                aba_encontrada = True
                break
        
        if not aba_encontrada:
            print("Aba '20 05 2026' não encontrada!")
            await browser.close()
            return
        
        print("Preenchendo dados...")
        
        for filial, linha in map_filiais.items():
            val_rec = valores_receber.get(filial, 0)
            if val_rec == 0:
                try:
                    val_rec = valores_receber.get(float(filial), 0)
                except:
                    val_rec = 0
            
            val_pag = valores_pagar.get(filial, 0)
            if val_pag == 0:
                try:
                    val_pag = valores_pagar.get(float(filial), 0)
                except:
                    val_pag = 0
            
            print(f"  {filial} (linha {linha}): Receber={val_rec:.2f}, Pagar={val_pag:.2f}")
            
            await preencher_celula(page, f"F{linha}", val_rec)
            await preencher_celula(page, f"C{linha}", val_pag)
        
        print("Preenchimento concluído!")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
