import asyncio
from playwright.async_api import async_playwright

# Dados para 15/05/2026
receber_15 = {
    '302': 6687.61,
    '429': 3482.81,
    '551': 8943.65,
    '601': 8399.07,
    'Nevine': 11674.81
}

pagar_15 = {
    '302': 346.62,
    '429': 24126.35,
    '551': 5343.89,
    '601': 1627.51
}

# Mapeamento: linha -> filial
map_linhas = {
    16: '302',
    17: '429',
    18: '551',
    19: '601',
    20: 'Nevine'
}

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
        
        # Encontrar aba 15 05 2026
        tabs = await page.query_selector_all('.docs-sheet-tab')
        for tab in tabs:
            nome = await tab.inner_text()
            if '15 05 2026' in nome:
                print(f'Acha aba {nome}')
                await tab.click()
                await asyncio.sleep(2)
                break
        
        print('Preenchendo dados...')
        
        # Preencher Receber (coluna F) e Pagar (coluna C)
        for linha, filial in map_linhas.items():
            # Receber - coluna F
            val_rec = receber_15.get(filial, 0)
            print(f'{filial} - linha {linha} - Receber: {val_rec}')
            await page.keyboard.press('F5')
            await asyncio.sleep(0.5)
            await page.keyboard.type(f'F{linha}')
            await page.keyboard.press('Enter')
            await asyncio.sleep(0.5)
            if val_rec > 0:
                await page.keyboard.type(str(val_rec).replace('.', ','))
            else:
                await page.keyboard.type('0')
            await page.keyboard.press('Enter')
            await asyncio.sleep(0.3)
            
            # Pagar - coluna C
            val_pag = pagar_15.get(filial, 0)
            print(f'{filial} - linha {linha} - Pagar: {val_pag}')
            await page.keyboard.press('F5')
            await asyncio.sleep(0.5)
            await page.keyboard.type(f'C{linha}')
            await page.keyboard.press('Enter')
            await asyncio.sleep(0.5)
            if val_pag > 0:
                await page.keyboard.type(str(val_pag).replace('.', ','))
            else:
                await page.keyboard.type('0')
            await page.keyboard.press('Enter')
            await asyncio.sleep(0.3)
        
        print('Dados preenchidos!')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())