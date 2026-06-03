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

        # Selecionar relatório 2004
        print("Selecionando relatório 2004...")
        await page.select_option('select#relatorio', '2004')
        await asyncio.sleep(4)  # Aguardar form carregar campos dinâmicos
        
        # Tirar screenshot após selecionar
        await page.screenshot(path="erp_2004_form.png", full_page=True)
        print("Screenshot salva como erp_2004_form.png")
        
        # Salvar HTML após selecionar relatório
        html = await page.content()
        with open("erp_2004_form.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("HTML salvo como erp_2004_form.html")
        
        # Buscar campos específicos no HTML para log rápido
        print("\n--- Buscando campos 'tipo' ou 'nota' no formulário ---")
        fields = await page.query_selector_all("select, input[type='checkbox'], input[type='radio']")
        for field in fields:
            fid = await field.get_attribute("id") or ""
            fname = await field.get_attribute("name") or ""
            ftype = await field.get_attribute("type") or await field.evaluate("el => el.tagName")
            print(f"  TAG: {ftype} | id={fid} | name={fname}")
        
        print("\nFinalizado.")
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
