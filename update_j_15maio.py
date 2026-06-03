import asyncio
import os
import zipfile
import pandas as pd
from playwright.async_api import async_playwright

BASE_DIR = r"c:\Users\finan\OneDrive\Área de Trabalho\Previsao"
PLANILHA_URL = "https://docs.google.com/spreadsheets/d/1OHMAcfxKIS2UTntlB5J7Y8krmCK7JHT9miEHmbbmLE8/edit#gid=993064263"

map_filiais = {"302": 16, "429": 17, "551": 18, "601": 19, "Nevine": 20}

def clean_currency(x):
    if isinstance(x, str):
        return float(x.replace('.', '').replace(',', '.'))
    return x

async def main():
    local_app_data = os.getenv("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
    user_data_dir = os.path.join(local_app_data, "Automacao_Previsao", "sessao_nova")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir, headless=False,
            viewport={"width": 1366, "height": 768},
            args=["--start-maximized"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        page.on("dialog", lambda dialog: dialog.accept())

        print("Abrindo planilha...")
        try:
            await page.goto(PLANILHA_URL, timeout=60000, wait_until="domcontentloaded")
        except:
            pass
        await asyncio.sleep(8)

        # Ativar aba 15 05 2026
        tabs = await page.query_selector_all(".docs-sheet-tab-name")
        for tab in tabs:
            if (await tab.inner_text()).strip() == "15 05 2026":
                await tab.click()
                await asyncio.sleep(2)
                print("Aba 15 05 2026 ativada.")
                break

        # Calcular J: Receber somente 19/05
        file_receber = os.path.join(BASE_DIR, "titulos a receber.zip")
        df_list = []
        with zipfile.ZipFile(file_receber, 'r') as z:
            for filename in z.namelist():
                if filename.endswith('.csv'):
                    with z.open(filename) as f:
                        df_list.append(pd.read_csv(f, sep=';', encoding='latin-1', on_bad_lines='skip'))
        df = pd.concat(df_list, ignore_index=True)
        df['ttr_data_vencimento'] = pd.to_datetime(df['ttr_data_vencimento'], dayfirst=True, errors='coerce')
        df['ttr_valor_titulo'] = df['ttr_valor_titulo'].apply(clean_currency).fillna(0)
        df['ttr_saldo'] = df['ttr_saldo'].apply(clean_currency).fillna(0)
        df = df[df['ttr_saldo'] > 0]

        valores_j = df[df['ttr_data_vencimento'] == pd.Timestamp('2026-05-19')].groupby('fil_descricao')['ttr_valor_titulo'].sum().to_dict()
        print(f"Valores J (Rec 19/05): {valores_j}")

        # Preencher coluna J
        print("\nPreenchendo coluna J...")
        for filial, linha in map_filiais.items():
            val = valores_j.get(str(filial), 0)
            if val == 0:
                try:
                    val = valores_j.get(float(filial), 0)
                except:
                    val = 0
            celula = f"J{linha}"
            await page.keyboard.press("F5")
            await asyncio.sleep(0.8)
            await page.keyboard.type(celula)
            await page.keyboard.press("Enter")
            await asyncio.sleep(0.8)
            await page.keyboard.type(str(val).replace('.', ',') if val > 0 else "0")
            await page.keyboard.press("Enter")
            await asyncio.sleep(0.5)
            print(f"  {filial} {celula}: {val:.2f}")

        print("\nColuna J atualizada com sucesso!")
        await asyncio.sleep(2)
        await context.close()

asyncio.run(main())
