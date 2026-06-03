import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    user_data_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'Automacao_NFe_Transporte', 'sessao_robo')
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            viewport={'width': 1366, 'height': 768},
            args=['--start-maximized']
        )
        page = await context.new_page()
        
        await page.goto('https://docs.google.com/spreadsheets/d/1OHMAcfxKIS2UTntlB5J7Y8krmCK7JHT9miEHmbbmLE8/edit#gid=993064263')
        await asyncio.sleep(15)
        
        # Clicar na aba 11 05 2026
        tabs = await page.query_selector_all('.docs-sheet-tab-name')
        for tab in tabs:
            nome = await tab.inner_text()
            if nome.strip() == '11 05 2026':
                await tab.click()
                await asyncio.sleep(3)
                print('Aba 11 05 2026 ativada')
                break
        
        print('Verificando valores:')
        
        # Verificar M16:M20
        for linha in range(16, 21):
            cell = f'M{linha}'
            # Usar atalho F5 para selecionar célula
            await page.keyboard.press('F5')
            await asyncio.sleep(0.3)
            await page.keyboard.type(cell)
            await page.keyboard.press('Enter')
            await asyncio.sleep(0.3)
            await page.keyboard.press('Control+a')
            await asyncio.sleep(0.2)
            # Obter valor da barra de fórmulas
            formula_bar = await page.locator('.cell-input').inner_text()
            print(f'{cell}: {formula_bar}')
        
        await context.close()

asyncio.run(main())