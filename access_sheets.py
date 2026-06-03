import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        page.on('dialog', lambda dialog: dialog.accept())
        
        print('Acessando planilha...')
        await page.goto('https://docs.google.com/spreadsheets/d/1OHMAcfxKIS2UTntlB5J7Y8krmCK7JHT9miEHmbbmLE8/edit?gid=667163110')
        await asyncio.sleep(10)
        
        if 'accounts.google.com' in page.url:
            print('Fazendo login...')
            await page.fill('input[type="email"]', 'financeiro@nevine.com.br')
            await page.click('#identifierNext')
            await asyncio.sleep(3)
            await page.fill('input[type="password"]', 'FN{25}Nevin3@')
            await page.click('#passwordNext')
            await asyncio.sleep(5)
        
        await asyncio.sleep(5)
        
        print('Aguardando carregar abas...')
        await page.wait_for_selector('.docs-sheet-tab-name', timeout=30000)
        await asyncio.sleep(3)
        
        # Encontrar aba 14 05 2026
        tabs = await page.query_selector_all('.docs-sheet-tab')
        aba_14 = None
        for tab in tabs:
            nome = await tab.inner_text()
            if '14 05 2026' in nome and 'Cópia' not in nome:
                aba_14 = tab
                print(f'Aba 14 05 2026 encontrada')
                break
        
        if aba_14:
            # Clicar na aba
            await aba_14.click()
            await asyncio.sleep(2)
            
            # Clicar no menu da aba (seta)
            seta = page.locator('.docs-sheet-active-tab .docs-sheet-tab-dropdown')
            await seta.click()
            await asyncio.sleep(1)
            
            # Clicar em Duplicar - usar primeiro item
            duplicar = page.locator('.goog-menuitem-content:has-text("Duplicar")').first
            await duplicar.click()
            await asyncio.sleep(5)
            
            # Renomear a nova aba
            nova_aba = page.locator('.docs-sheet-active-tab .docs-sheet-tab-name')
            await nova_aba.dblclick()
            await asyncio.sleep(1)
            await page.keyboard.type('15 05 2026')
            await page.keyboard.press('Enter')
            await asyncio.sleep(3)
            
            print('Aba duplicada e renomeada para 15 05 2026')
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())