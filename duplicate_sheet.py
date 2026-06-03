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
        
        # Encontrar aba 15 05 2026 ou Cópia de 14 05 2026
        tabs = await page.query_selector_all('.docs-sheet-tab')
        aba_alvo = None
        
        for tab in tabs:
            nome = await tab.inner_text()
            if '15 05 2026' in nome:
                aba_alvo = tab
                print('Aba 15 05 2026 ja existe')
                break
            elif 'Cópia de 14 05 2026' in nome or 'Cópia de 14 05' in nome:
                aba_alvo = tab
                print('Encontrada copia, renomeando...')
                await aba_alvo.click()
                await asyncio.sleep(1)
                # Clicar na seta para renomear
                seta = page.locator('.docs-sheet-active-tab .docs-sheet-tab-dropdown')
                await seta.click()
                await asyncio.sleep(1)
                # Renomear
                await aba_alvo.dblclick()
                await asyncio.sleep(1)
                await page.keyboard.press('Backspace')
                await page.keyboard.press('Backspace')
                await page.keyboard.press('Backspace')
                await page.keyboard.press('Backspace')
                await page.keyboard.press('Backspace')
                await page.keyboard.press('Backspace')
                await page.keyboard.press('Backspace')
                await page.keyboard.press('Backspace')
                await page.keyboard.press('Backspace')
                await page.keyboard.type('15 05 2026')
                await page.keyboard.press('Enter')
                await asyncio.sleep(2)
                print('Aba renomeada para 15 05 2026')
                break
        
        if not aba_alvo:
            # Criar nova aba a partir da 14 05 2026
            for tab in tabs:
                nome = await tab.inner_text()
                if '14 05 2026' in nome and 'Cópia' not in nome:
                    await tab.click()
                    await asyncio.sleep(2)
                    # Duplicar
                    seta = page.locator('.docs-sheet-active-tab .docs-sheet-tab-dropdown')
                    await seta.click()
                    await asyncio.sleep(1)
                    duplicar = page.locator('.goog-menuitem-content:has-text("Duplicar")').first
                    await duplicar.click()
                    await asyncio.sleep(5)
                    # Renomear
                    nova_aba = page.locator('.docs-sheet-active-tab .docs-sheet-tab-name')
                    await nova_aba.dblclick()
                    await asyncio.sleep(1)
                    await page.keyboard.type('15 05 2026')
                    await page.keyboard.press('Enter')
                    await asyncio.sleep(2)
                    print('Nova aba 15 05 2026 criada')
                    break
        
        print('Processo concluido!')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())