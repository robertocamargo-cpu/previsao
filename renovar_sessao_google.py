"""
Script auxiliar para renovar a sessão do Google.
Execute este script UMA VEZ manualmente para fazer o login no Google
e salvar a sessão. Depois, o automacao_previsao.py funcionará normalmente.

Uso: python3 renovar_sessao_google.py
"""
import asyncio
import os
import platform
from playwright.async_api import async_playwright

# Mesmo diretório de sessão usado pelo automacao_previsao.py
if platform.system() == "Darwin":
    local_app_data = os.path.expanduser("~/Library/Application Support")
elif platform.system() == "Windows":
    local_app_data = os.getenv("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
else:
    local_app_data = os.path.expanduser("~/.local/share")

user_data_dir = os.path.join(local_app_data, "Automacao_Previsao", "sessao_nova")
os.makedirs(user_data_dir, exist_ok=True)

PLANILHA_URL = os.getenv("PLANILHA_URL", "https://docs.google.com/spreadsheets")

async def main():
    print("=" * 60)
    print("RENOVAÇÃO DE SESSÃO DO GOOGLE")
    print("=" * 60)
    print(f"Perfil de sessão: {user_data_dir}")
    print()
    print("Um navegador será aberto. Faça login no Google manualmente.")
    print("Depois de logado e com a planilha aberta, feche o navegador")
    print("ou pressione Enter neste terminal para encerrar.")
    print()

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,  # Modo visível para login manual
            viewport={"width": 1366, "height": 768},
            args=["--start-maximized"],
        )
        page = context.pages[0] if context.pages else await context.new_page()

        # Abrir o Google diretamente
        print("Abrindo Google Sheets...")
        try:
            await page.goto("https://accounts.google.com/", timeout=30000)
        except Exception as e:
            print(f"Aviso ao abrir Google: {e}")

        print()
        print(">>> Faça o login no navegador aberto. <<<")
        print(">>> Quando terminar, pressione Enter aqui para salvar e encerrar. <<<")
        print()

        # Aguardar input do usuário
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, input)

        print("Salvando sessão e encerrando navegador...")
        await context.close()

    print()
    print("✅ Sessão salva com sucesso!")
    print("Agora rode: python3 automacao_previsao.py")

if __name__ == "__main__":
    asyncio.run(main())
