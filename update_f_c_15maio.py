import asyncio
import os
import zipfile
import pandas as pd
from playwright.async_api import async_playwright

BASE_DIR = r"c:\Users\finan\OneDrive\Área de Trabalho\Previsao"
PLANILHA_URL = "https://docs.google.com/spreadsheets/d/1OHMAcfxKIS2UTntlB5J7Y8krmCK7JHT9miEHmbbmLE8/edit#gid=993064263"

map_filiais = {
    "302": 16,
    "429": 17,
    "551": 18,
    "601": 19,
    "Nevine": 20
}

def clean_currency(x):
    if isinstance(x, str):
        return float(x.replace('.', '').replace(',', '.'))
    return x

async def main():
    local_app_data = os.getenv("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
    user_data_dir = os.path.join(local_app_data, "Automacao_Previsao", "sessao_nova")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            viewport={"width": 1366, "height": 768},
            args=["--start-maximized"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        page.on("dialog", lambda dialog: dialog.accept())

        # Abrir planilha
        print("Abrindo planilha...")
        try:
            await page.goto(PLANILHA_URL, timeout=60000, wait_until="domcontentloaded")
        except:
            pass
        await asyncio.sleep(8)

        # Ativar aba 15 05 2026
        tabs = await page.query_selector_all(".docs-sheet-tab-name")
        aba_ativada = False
        for tab in tabs:
            nome = await tab.inner_text()
            if nome.strip() == "15 05 2026":
                await tab.click()
                await asyncio.sleep(2)
                print("Aba 15 05 2026 ativada.")
                aba_ativada = True
                break

        if not aba_ativada:
            print("ERRO: Aba '15 05 2026' não encontrada!")
            await context.close()
            return

        # ── Calcular F: Receber 16+17+18/05 ──────────────────────────────
        file_receber = os.path.join(BASE_DIR, "titulos a receber.zip")
        df_list = []
        with zipfile.ZipFile(file_receber, 'r') as z:
            for filename in z.namelist():
                if filename.endswith('.csv'):
                    with z.open(filename) as f:
                        df_list.append(pd.read_csv(f, sep=';', encoding='latin-1', on_bad_lines='skip'))
        df_rec = pd.concat(df_list, ignore_index=True)
        df_rec['ttr_data_vencimento'] = pd.to_datetime(df_rec['ttr_data_vencimento'], dayfirst=True, errors='coerce')
        df_rec['ttr_valor_titulo'] = df_rec['ttr_valor_titulo'].apply(clean_currency).fillna(0)
        df_rec['ttr_saldo'] = df_rec['ttr_saldo'].apply(clean_currency).fillna(0)
        df_rec = df_rec[df_rec['ttr_saldo'] > 0]

        datas_f = [pd.Timestamp('2026-05-16'), pd.Timestamp('2026-05-17'), pd.Timestamp('2026-05-18')]
        valores_f = df_rec[df_rec['ttr_data_vencimento'].isin(datas_f)].groupby('fil_descricao')['ttr_valor_titulo'].sum().to_dict()
        print(f"Valores F (Rec 16+17+18/05): {valores_f}")

        # ── Calcular C: Pagar 16+17+18/05 ────────────────────────────────
        file_pagar = os.path.join(BASE_DIR, "titulos a pagar.zip")
        df_list2 = []
        with zipfile.ZipFile(file_pagar, 'r') as z:
            for filename in z.namelist():
                if filename.endswith('.csv'):
                    with z.open(filename) as f:
                        df_list2.append(pd.read_csv(f, sep=';', encoding='latin-1', on_bad_lines='skip'))
        df_pag = pd.concat(df_list2, ignore_index=True)
        df_pag['ttp_data_vencimento'] = pd.to_datetime(df_pag['ttp_data_vencimento'], dayfirst=True, errors='coerce')
        df_pag['ttp_valor_titulo'] = df_pag['ttp_valor_titulo'].apply(clean_currency).fillna(0)
        df_pag['ttp_saldo'] = df_pag['ttp_saldo'].apply(clean_currency).fillna(0)
        df_pag = df_pag[df_pag['ttp_saldo'] > 0]

        datas_c = [pd.Timestamp('2026-05-16'), pd.Timestamp('2026-05-17'), pd.Timestamp('2026-05-18')]
        valores_c = df_pag[df_pag['ttp_data_vencimento'].isin(datas_c)].groupby('fil_descricao')['ttp_valor_titulo'].sum().to_dict()
        print(f"Valores C (Pag 16+17+18/05): {valores_c}")

        # ── Preencher F (linhas 16-20) ────────────────────────────────────
        print("\nPreenchendo coluna F...")
        for filial, linha in map_filiais.items():
            filial_key = str(filial)
            val = valores_f.get(filial_key, 0)
            if val == 0:
                try:
                    val = valores_f.get(float(filial_key), 0)
                except:
                    val = 0
            celula = f"F{linha}"
            await page.keyboard.press("F5")
            await asyncio.sleep(0.8)
            await page.keyboard.type(celula)
            await page.keyboard.press("Enter")
            await asyncio.sleep(0.8)
            await page.keyboard.type(str(val).replace('.', ',') if val > 0 else "0")
            await page.keyboard.press("Enter")
            await asyncio.sleep(0.5)
            print(f"  {filial} {celula}: {val:.2f}")

        # ── Preencher C (linhas 16-20) ────────────────────────────────────
        print("\nPreenchendo coluna C...")
        for filial, linha in map_filiais.items():
            filial_key = str(filial)
            val = valores_c.get(filial_key, 0)
            if val == 0:
                try:
                    val = valores_c.get(float(filial_key), 0)
                except:
                    val = 0
            celula = f"C{linha}"
            await page.keyboard.press("F5")
            await asyncio.sleep(0.8)
            await page.keyboard.type(celula)
            await page.keyboard.press("Enter")
            await asyncio.sleep(0.8)
            await page.keyboard.type(str(val).replace('.', ',') if val > 0 else "0")
            await page.keyboard.press("Enter")
            await asyncio.sleep(0.5)
            print(f"  {filial} {celula}: {val:.2f}")

        print("\nColunas F e C atualizadas com sucesso!")
        await asyncio.sleep(3)
        await context.close()

asyncio.run(main())
