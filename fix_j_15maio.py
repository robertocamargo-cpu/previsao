import asyncio
import os
from playwright.async_api import async_playwright

PLANILHA_URL = "https://docs.google.com/spreadsheets/d/1OHMAcfxKIS2UTntlB5J7Y8krmCK7JHT9miEHmbbmLE8/edit#gid=993064263"

# Rec 19/05 por filial
valores = {
    "J16": "0",        # 302
    "J17": "6533,80",  # 429
    "J18": "3499,82",  # 551
    "J19": "0",        # 601
    "J20": "8697,80",  # Nevine
}

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
                await asyncio.sleep(3)
                print("Aba 15 05 2026 ativada.")
                break

        await asyncio.sleep(2)

        for celula, valor in valores.items():
            print(f"Preenchendo {celula} = {valor}...")
            await page.keyboard.press("F5")
            await asyncio.sleep(1)
            await page.keyboard.type(celula)
            await page.keyboard.press("Enter")
            await asyncio.sleep(1)
            await page.keyboard.press("Delete")
            await asyncio.sleep(0.5)
            await page.keyboard.type(valor)
            await page.keyboard.press("Enter")
            await asyncio.sleep(1)

        print("\nColuna J preenchida com sucesso!")
        await asyncio.sleep(3)
        await context.close()

asyncio.run(main())
