from playwright.async_api import async_playwright
import asyncio
import os

PLANILHA_URL = "https://docs.google.com/spreadsheets/d/1OHMAcfxKIS2UTntlB5J7Y8krmCK7JHT9miEHmbbmLE8/edit#gid=993064263"

async def main():
    user_data_dir = os.path.join(os.getenv("LOCALAPPDATA"), "Automacao_Previsao_Temp3")
    os.makedirs(user_data_dir, exist_ok=True)
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            viewport={"width": 1366, "height": 768},
            args=["--start-maximized"]
        )
        page = await context.new_page()
        
        await page.goto(PLANILHA_URL, timeout=120000)
        await asyncio.sleep(20)
        
        if "accounts.google.com" in page.url:
            print("Fazendo login...")
            await page.locator('input[type="email"]').fill("financeiro@nevine.com.br")
            await page.click("#identifierNext")
            await asyncio.sleep(5)
            await page.locator('input[type="password"]').fill("FN{25}Nevin3@")
            await page.click("#passwordNext")
            await asyncio.sleep(15)
        
        await page.wait_for_selector(".docs-sheet-tab-name", timeout=60000)
        tabs = await page.query_selector_all(".docs-sheet-tab-name")
        
        print("\nAbas encontradas:")
        for tab in tabs:
            nome = await tab.inner_text()
            print(f"  - {nome}")
        
        await context.close()

asyncio.run(main())