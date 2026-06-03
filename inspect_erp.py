import asyncio
import os
from playwright.async_api import async_playwright

ERP_URL = "https://erp.admsis.com/Home?eng_tela=0107030100"

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
        
        print("Abrindo ERP...")
        await page.goto(ERP_URL, timeout=60000, wait_until="load")
        await asyncio.sleep(5)
        
        # Tirar screenshot
        await page.screenshot(path="erp_tela_0107030100.png", full_page=True)
        print("Screenshot salva como erp_tela_0107030100.png")
        
        # Salvar HTML
        html = await page.content()
        with open("erp_tela_0107030100.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("HTML salvo como erp_tela_0107030100.html")
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
