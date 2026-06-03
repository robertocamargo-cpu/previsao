import asyncio
import os
from playwright.async_api import async_playwright

PLANILHA_URL = "https://docs.google.com/spreadsheets/d/1OHMAcfxKIS2UTntlB5J7Y8krmCK7JHT9miEHmbbmLE8/edit#gid=993064263"

async def main():
    local_app_data = os.getenv("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
    user_data_dir = os.path.join(local_app_data, "Automacao_NFe_Transporte", "sessao_robo")
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            viewport={"width": 1366, "height": 768}
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        print("Abrindo planilha...")
        await page.goto(PLANILHA_URL)
        await asyncio.sleep(10)
        
        print("Testando F5 para ir para célula B16...")
        await page.keyboard.press("F5")
        await asyncio.sleep(2)
        
        # O F5 abre a caixa de pesquisa de intervalo. 
        # Vamos digitar B16 e dar Enter
        await page.keyboard.type("B16")
        await asyncio.sleep(1)
        await page.keyboard.press("Enter")
        await asyncio.sleep(2)
        
        print("Tentando digitar 999...")
        await page.keyboard.type("999")
        await asyncio.sleep(1)
        await page.keyboard.press("Enter")
        
        print("Concluído. Veja se o valor foi inserido.")
        await asyncio.sleep(5)
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
