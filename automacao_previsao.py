import asyncio
import os
import re
import csv
import io
import zipfile
from datetime import datetime, timedelta
import pandas as pd
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

# ─── Configurações ─────────────────────────────────────────────────────────
BASE_DIR = r"c:\Users\finan\OneDrive\Área de Trabalho\Previsao"
PLANILHA_URL = "https://docs.google.com/spreadsheets/d/1OHMAcfxKIS2UTntlB5J7Y8krmCK7JHT9miEHmbbmLE8/edit#gid=993064263"

# ERP
ERP_URL = "https://erp.admsis.com/Home"
ERP_USER = os.getenv("ERP_USER")
ERP_PASS = os.getenv("ERP_PASS")

# Google
GOOGLE_USER = os.getenv("GOOGLE_USER")
GOOGLE_PASS = os.getenv("GOOGLE_PASS")

# Filiais a pesquisar
FILIAIS = ["302", "429", "551", "601", "Nevine"]

FERIADOS = [
    (1, 1),   # Confraternização Universal
    (1, 5),   # Dia do Trabalho
    (7, 9),   # Independência do Brasil
    (12, 10), # Nossa Senhora Aparecida
    (2, 11),  # Finados
    (15, 11), # Proclamação da República
    (20, 11), # Dia da Consciência Negra
    (25, 12)  # Natal
]

def is_dia_util(d):
    if d.weekday() >= 5:
        return False
    if (d.day, d.month) in FERIADOS:
        return False
    return True

def dia_util_anterior(d):
    d = d - timedelta(days=1)
    while not is_dia_util(d):
        d -= timedelta(days=1)
    return d

def calcular_datas():
    hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    data_inicio = hoje - timedelta(days=2)
    data_fim = hoje + timedelta(days=10)
    
    # Formato para preencher no ERP: dd/mm/yyyy
    str_inicio = data_inicio.strftime("%d/%m/%Y")
    str_fim = data_fim.strftime("%d/%m/%Y")
    
    # A aba base para copiar é a de HOJE
    aba_base = hoje.strftime("%d %m %Y")
    
    return str_inicio, str_fim, aba_base, data_inicio, data_fim

async def esperar_carregamento_erp(page):
    try:
        overlay = page.locator('.blockUI, .loading, :text("Aguarde"), :text("carregando")').first
        for _ in range(20):
            if await overlay.is_visible():
                await asyncio.sleep(1)
            else:
                break
    except:
        pass
    await asyncio.sleep(1)

async def login_erp(page):
    print("Acessando ERP...")
    await page.goto(ERP_URL, timeout=90000, wait_until="load")
    await asyncio.sleep(3)
    
    usuario_logado = page.locator(f'text="{ERP_USER}"').first
    if await usuario_logado.count() > 0:
        print("Sessão do ERP já está ativa.")
        return True
        
    print("Realizando login no ERP...")
    try:
        await page.fill('input[name="usu_codigo"]', ERP_USER)
        await page.fill('input[name="usu_senha"]', ERP_PASS)
        await page.click('button#login')
        await asyncio.sleep(5)
        await esperar_carregamento_erp(page)
        print("Login ERP concluído.")
        return True
    except Exception as e:
        print(f"Erro no login ERP: {e}")
        return False

async def baixar_relatorio(page, relatorio_id, str_inicio, str_fim, nome_arquivo_saida):
    print(f"\nBaixando relatório {relatorio_id}...")
    
    try:
        await page.goto("https://erp.admsis.com/Home?eng_tela=0107030100", timeout=60000)
    except:
        print("Erro ao acessar URL direta do relatório.")
        return False
        
    await asyncio.sleep(5)
    await esperar_carregamento_erp(page)
    
    # 1. Selecionar o relatório
    try:
        await page.select_option('select#relatorio', relatorio_id)
        await asyncio.sleep(2)
        await esperar_carregamento_erp(page)
    except Exception as e:
        print(f"Erro ao selecionar relatório {relatorio_id}: {e}")
        return False

    # Tipo de Nota Fiscal = Todos (sem filtro)
    # Removido filtro de NF-e para trazer todos os tipos

    # 2. Preencher datas
    print("Preenchendo datas de vencimento...")
    try:
        # A data tem máscara no ERP, então digitamos apenas os números
        str_inicio_num = str_inicio.replace("/", "")
        str_fim_num = str_fim.replace("/", "")
        
        # Limpar os campos via JS para garantir que a máscara não atrapalhe
        await page.evaluate('document.getElementById("data_vencimento_i").value = "";')
        await page.type('input#data_vencimento_i', str_inicio_num, delay=50)
        await asyncio.sleep(1)
        
        await page.evaluate('document.getElementById("data_vencimento_f").value = "";')
        await page.type('input#data_vencimento_f', str_fim_num, delay=50)
        await asyncio.sleep(1)
    except Exception as e:
        print(f"Erro ao preencher datas: {e}")
        return False
        
    # 3. Clicar em Gerar CSV e aguardar o download
    print("Gerando relatório...")
    caminho_salvar = os.path.join(BASE_DIR, nome_arquivo_saida)
    try:
        # Removemos o target='_blank' do formulário para evitar que abra em nova aba e trave o expect_download
        await page.evaluate('document.getElementById("Formulario").removeAttribute("target");')
        await asyncio.sleep(1)
        
        async with page.expect_download(timeout=120000) as download_info:
            await page.click('button#btRelatorioCSV')
        
        download = await download_info.value
        await download.save_as(caminho_salvar)
        print(f"Salvo em: {caminho_salvar}")
    except Exception as e:
        print(f"Erro ao fazer o download do arquivo CSV: {e}")
        return False
        
    return True

def clean_currency(x):
    if isinstance(x, str):
        return float(x.replace('.', '').replace(',', '.'))
    return x

def format_brl(val):
    """Formata número para padrão brasileiro: 1.234,56"""
    return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def ajustar_data_receber(d):
    """Finais de semana/Feriados → dia útil anterior."""
    if pd.isna(d):
        return d
    if not is_dia_util(d):
        return dia_util_anterior(d)
    return d

def ajustar_data_pagar(d):
    """Finais de semana/Feriados → dia útil anterior."""
    if pd.isna(d):
        return d
    if not is_dia_util(d):
        return dia_util_anterior(d)
    return d

def processar_csvs(d_inicio, d_fim):
    print("\nProcessando arquivos zipados...")
    file_pagar = os.path.join(BASE_DIR, "titulos a pagar.zip")
    file_receber = os.path.join(BASE_DIR, "titulos a receber.zip")
    
    if not os.path.exists(file_pagar) or not os.path.exists(file_receber):
        print("Arquivos ZIP não encontrados. Certifique-se de que o download funcionou.")
        return {}
    
    def get_csv_totals_sem_ajuste(d_inicio, d_fim):
        """Busca valores originais sem ajuste de data para 09-11/05"""
        import zipfile
        try:
            df_list = []
            with zipfile.ZipFile(file_receber, 'r') as z:
                for filename in z.namelist():
                    if filename.endswith('.csv'):
                        with z.open(filename) as f:
                            df_part = pd.read_csv(f, sep=';', encoding='latin-1', on_bad_lines='skip')
                            df_list.append(df_part)
            df = pd.concat(df_list, ignore_index=True)
            
            df['ttr_data_vencimento'] = pd.to_datetime(df['ttr_data_vencimento'], errors='coerce')
            df['ttr_valor_titulo'] = df['ttr_valor_titulo'].apply(clean_currency).fillna(0)
            df['ttr_saldo'] = df['ttr_saldo'].apply(clean_currency).fillna(0)
            
            # Filtrar apenas 09, 10 e 11/05 com saldo > 0 - SEM AJUSTE
            datas = [pd.Timestamp('2026-05-09'), pd.Timestamp('2026-05-10'), pd.Timestamp('2026-05-11')]
            mask = (df['ttr_data_vencimento'].isin(datas)) & (df['ttr_saldo'] > 0)
            df_filtered = df[mask].copy()
            
            # Agrupar por filial
            totals = df_filtered.groupby('fil_descricao')['ttr_valor_titulo'].sum().to_dict()
            return totals
        except Exception as e:
            print(f"Erro ao buscar dados originais: {e}")
            return {}
    
    # Buscar valores originais para M (sem ajuste)
    valores_originais = get_csv_totals_sem_ajuste(d_inicio, d_fim)
    print(f"Valores originais 09-11/05 (para M): {valores_originais}")
        
    def get_csv_totals(path, date_col, value_col, filial_col, saldo_col, ajuste_fn=None):
        import zipfile
        try:
            df_list = []
            with zipfile.ZipFile(path, 'r') as z:
                for filename in z.namelist():
                    if filename.endswith('.csv'):
                        with z.open(filename) as f:
                            df_part = pd.read_csv(f, sep=';', encoding='latin-1', on_bad_lines='skip')
                            df_list.append(df_part)
            if not df_list:
                return {}
            df = pd.concat(df_list, ignore_index=True)
            
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df[value_col] = df[value_col].apply(clean_currency).fillna(0)
            df[saldo_col] = df[saldo_col].apply(clean_currency).fillna(0)
            
            # Filtra o período e saldo > 0
            mask = (df[date_col] >= pd.Timestamp(d_inicio)) & (df[date_col] <= pd.Timestamp(d_fim)) & (df[saldo_col] > 0)
            df_filtered = df[mask].copy()
            
            # Ajuste de datas conforme regra de dia da semana
            if ajuste_fn:
                df_filtered[date_col] = df_filtered[date_col].apply(ajuste_fn)
            
            # Agrupa por Data (ajustada) e Filial
            df_filtered['data_str'] = df_filtered[date_col].dt.strftime('%d/%m/%Y')
            totals = df_filtered.groupby(['data_str', filial_col])[value_col].sum().to_dict()
            return totals
        except Exception as e:
            print(f"Erro processando {path}: {e}")
            return {}

    totals_receber = get_csv_totals(file_receber, 'ttr_data_vencimento', 'ttr_valor_titulo', 'fil_descricao', 'ttr_saldo', ajuste_fn=ajustar_data_receber)
    totals_pagar   = get_csv_totals(file_pagar,   'ttp_data_vencimento', 'ttp_valor_titulo', 'fil_descricao', 'ttp_saldo', ajuste_fn=ajustar_data_pagar)
    
    # Estruturar o dicionário final
    # formato: dados['29/04/2026']['receber']['302']
    dados_organizados = {}
    current_date = d_inicio
    while current_date <= d_fim:
        d_str = current_date.strftime('%d/%m/%Y')
        dados_organizados[d_str] = {'receber': {}, 'pagar': {}}
        
        # Preencher receber
        for key, val in totals_receber.items():
            if key[0] == d_str:
                filial_str = str(int(float(key[1]))) if isinstance(key[1], (int, float)) else str(key[1])
                dados_organizados[d_str]['receber'][filial_str] = val
                
        # Preencher pagar
        for key, val in totals_pagar.items():
            if key[0] == d_str:
                filial_str = str(int(float(key[1]))) if isinstance(key[1], (int, float)) else str(key[1])
                dados_organizados[d_str]['pagar'][filial_str] = val
                
        current_date += timedelta(days=1)
        
    print("Processamento concluído.")
    return dados_organizados, valores_originais

async def atualizar_planilha(page, dados, valores_originais):
    print("\nAtualizando Google Sheets...")
    
    # 1. Abrir planilha
    try:
        await page.goto(PLANILHA_URL, timeout=60000, wait_until="domcontentloaded")
    except:
        pass
    await asyncio.sleep(5)
    
    # Lidar com login do Google se necessário
    if "accounts.google.com" in page.url:
        print("Login do Google detectado. Inserindo credenciais...")
        try:
            # Tela de email: usar apenas o campo visível (ignora hiddenEmail com aria-hidden)
            email_selector = 'input[type="email"]:not([aria-hidden="true"])'
            email_field = page.locator(email_selector).first
            try:
                await email_field.wait_for(state="visible", timeout=10000)
                await email_field.fill(GOOGLE_USER)
                await page.click('#identifierNext')
                await asyncio.sleep(4)
                print("Email inserido. Aguardando tela de senha...")
            except Exception as e_email:
                print(f"Campo de email não visível (pode já estar na tela de senha): {e_email}")

            # Tela de senha
            password_field = page.locator('input[type="password"]').first
            await password_field.wait_for(state="visible", timeout=20000)
            await password_field.fill(GOOGLE_PASS)
            await page.click('#passwordNext')
            print("Senha inserida. Aguardando redirecionamento...")

            # Aguardar redirecionamento para a planilha
            for _ in range(30):
                await asyncio.sleep(1)
                if "docs.google.com" in page.url:
                    print("Redirecionado para Google Docs com sucesso.")
                    break
        except Exception as e:
            print(f"Erro no login do Google: {e}")
    else:
        print("Sessão do Google já ativa ou não é necessário login.")
    
    # Espera adicional para garantir que a planilha carregue completamente após o login
    await asyncio.sleep(5)
    
    # Tentar recarregar a planilha se ainda não estiver visível
    if "docs.google.com" in page.url:
        print("Planilha carregando...")
        try:
            await page.reload(timeout=120000, wait_until="domcontentloaded")
        except:
            pass
        await asyncio.sleep(5)
    
    # Esperar planilha carregar
    try:
        await page.wait_for_selector(".docs-sheet-tab-name", timeout=120000)
    except:
        try:
            await page.screenshot(path="erro_planilha.png")
            print(f"Print salvo em erro_planilha.png. URL atual: {page.url[:200]}")
        except:
            pass
        print("Planilha não carregou a tempo.")
        return False
        
    await asyncio.sleep(5)
    
    # 2. Calcular hoje e ontem
    hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    ontem = hoje - timedelta(days=1)
    while not is_dia_util(ontem):
        ontem -= timedelta(days=1)
    aba_hoje = hoje.strftime("%d %m %Y")
    aba_ontem = ontem.strftime("%d %m %Y")
    
    print(f"Procurando aba '{aba_ontem}' para duplicar e renomear para: '{aba_hoje}'")
    
    # 3. Encontrar todas as abas
    tabs = await page.query_selector_all(".docs-sheet-tab-name")
    
    aba_origem_tab = None
    aba_hoje_existe = False
    
    for tab in tabs:
        nome = await tab.inner_text()
        nome = nome.strip()
        print(f"  Aba encontrada: '{nome}'")
        if nome == aba_ontem:
            aba_origem_tab = tab
        if nome == aba_hoje:
            aba_hoje_existe = True
    
    if aba_origem_tab is None:
        print(f"Aba '{aba_ontem}' não encontrada! Buscando aba mais recente...")
        for tab in tabs:
            nome = await tab.inner_text()
            nome = nome.strip()
            if nome != aba_hoje and not nome.startswith("Cópia") and not nome.startswith("Copy"):
                aba_origem_tab = tab
                aba_ontem = nome
                print(f"Usando aba '{nome}' como origem.")
                break
        if aba_origem_tab is None:
            print("Nenhuma aba disponível encontrada.")
            return False
    
    print(f"Aba origem encontrada: '{aba_ontem}'")
    
    # 4. Verificar se a aba de hoje já existe
    if aba_hoje_existe:
        print(f"Aba de hoje '{aba_hoje}' já existe. Ativando para preenchimento.")
        for tab in tabs:
            nome = await tab.inner_text()
            if nome.strip() == aba_hoje:
                await tab.click()
                await asyncio.sleep(2)
                break
    else:
        # 6. Ativar a aba origem e duplicar
        print(f"Ativando aba '{aba_ontem}'...")
        await aba_origem_tab.click()
        await asyncio.sleep(2)
        print(f"Duplicando aba '{aba_ontem}'...")
        seta = page.locator('.docs-sheet-active-tab .docs-sheet-tab-dropdown')
        await seta.click()
        await asyncio.sleep(1)
        
        duplicar_btn = page.locator('.goog-menuitem:has-text("Duplicar"):visible, .goog-menuitem:has-text("Duplicate"):visible').first
        await duplicar_btn.click()
        print("Aba duplicada. Aguardando processamento do Google Sheets...")
        await asyncio.sleep(8)
        
        # Esperar modal fechar se existir
        try:
            await page.wait_for_selector('.modal-dialog-bg', state='hidden', timeout=10000)
        except:
            pass
        
        await asyncio.sleep(2)
        
        # 7. Renomear a aba duplicada para hoje
        print(f"Renomeando aba para '{aba_hoje}'...")
        # Ensure the tab name element is ready
        await page.wait_for_selector('.docs-sheet-active-tab .docs-sheet-tab-name', state='visible', timeout=15000)
        nova_aba_tab = page.locator('.docs-sheet-active-tab .docs-sheet-tab-name')
        try:
            await nova_aba_tab.dblclick()
        except Exception:
            # fallback: right-click then choose rename
            await nova_aba_tab.click(button='right')
            await asyncio.sleep(0.5)
            renomear_opt = page.locator('.goog-menuitem:has-text("Renomear"), .goog-menuitem:has-text("Rename")').first
            await renomear_opt.click()
            await asyncio.sleep(0.5)
        # Clear existing name and type new name
        await page.keyboard.press("Control+A")
        await page.keyboard.type(aba_hoje)
        await page.keyboard.press("Enter")
        await asyncio.sleep(3)
        
        print(f"Aba renomeada para '{aba_hoje}'.")
    
    dt_nova = hoje
    
    # 8. Preencher Cabeçalhos e Dados (Apenas os 3 próximos dias úteis)
    print(f"Iniciando preenchimento dos dados para a data {aba_hoje} via interface (Atalho F5)...")
    
    # Calcular os 3 próximos dias úteis baseados na data de hoje
    dias_alvo = []
    curr = dt_nova + timedelta(days=1)
    while len(dias_alvo) < 3:
        if is_dia_util(curr):
            dias_alvo.append(curr)
        curr += timedelta(days=1)
        
    map_filiais = {
        "302": 16,
        "429": 17,
        "551": 18,
        "601": 19,
        "Nevine": 20
    }
    
    colunas_por_dia = [
        {"header": "F13", "receber": None, "pagar": "C"},
        {"header": "J13", "receber": None, "pagar": "G"},
        {"header": "K13", "receber": None, "pagar": "K"}
    ]
    
    # Calcular datas do dia seguinte para C15, G15, K15
    # C15 = dia seguinte ao B15, G15 = dia seguinte ao F15, K15 = dia seguinte ao J15
    dia_seguinte_b15 = dias_alvo[0].strftime("%d/%m")  # próxima data útil após dt_nova
    dia_seguinte_f15 = dias_alvo[1].strftime("%d/%m")  # próxima data útil após dias_alvo[0]
    dia_seguinte_j15 = dias_alvo[2].strftime("%d/%m")  # próxima data útil após dias_alvo[1]
    
    # Atualizar a Linha 15 (rótulos de período baseados em dt_nova)
    str_b15 = dt_nova.strftime("%d/%m")
    str_d15 = f"{dt_nova.strftime('%d/%m')} a {dias_alvo[0].strftime('%d/%m')}"
    str_f15 = dias_alvo[0].strftime("%d/%m")
    str_h15 = f"{dias_alvo[0].strftime('%d/%m')} a {dias_alvo[1].strftime('%d/%m')}"
    str_j15 = dias_alvo[1].strftime("%d/%m")
    str_l15 = f"{dias_alvo[1].strftime('%d/%m')} a {dias_alvo[2].strftime('%d/%m')}"
    
    atualizacoes_row15 = [
        ("B15", str_b15), ("C15", dia_seguinte_b15), ("D15", str_d15),
        ("F15", str_f15), ("G15", dia_seguinte_f15), ("H15", str_h15),
        ("J15", str_j15), ("K15", dia_seguinte_j15), ("L15", str_l15)
    ]
    
    for celula, valor in atualizacoes_row15:
        await page.keyboard.press("F5")
        await asyncio.sleep(0.5)
        await page.keyboard.type(celula)
        await page.keyboard.press("Enter")
        await asyncio.sleep(0.5)
        await page.keyboard.type(valor)
        await page.keyboard.press("Enter")
        await asyncio.sleep(0.5)
    
    # As datas para extrair os valores (correspondentes à linha 15: B15, F15, J15)
    # B = dias_alvo[0], F = dias_alvo[1], J = dias_alvo[2] (dias úteis seguintes)
    datas_para_receber = [dias_alvo[0], dias_alvo[1], dias_alvo[2]]
    
    for i in range(len(colunas_por_dia)):
        data_obj_header = dias_alvo[i]
        data_obj_dados = datas_para_receber[i]
        
        data_str_full_dados = data_obj_dados.strftime("%d/%m/%Y")
        data_str_header = data_obj_header.strftime("%d/%m")
        cols = colunas_por_dia[i]
        data_str_full_pagar = data_obj_header.strftime("%d/%m/%Y")
        
        # Para colunas C, G, K (pagar), usar o dia atual (não o seguinte)
        # C = Pagar 12/05, G = Pagar 13/05, K = Pagar 15/05
        data_str_pagar_seguinte = data_obj_header.strftime("%d/%m/%Y")
        
        print(f"  -> Dia {i+1}: {data_str_header} | Rec: {data_str_full_dados} | Pagar: {data_str_pagar_seguinte}")
        
        # 1. Atualizar o cabeçalho (ex: B13)
        await page.keyboard.press("F5")
        await asyncio.sleep(0.5)
        await page.keyboard.type(cols["header"])
        await page.keyboard.press("Enter")
        await asyncio.sleep(0.5)
        await page.keyboard.type(data_str_header)
        await page.keyboard.press("Enter")
        await asyncio.sleep(0.5)
        
        # 2. Preencher Recebíveis e Pagamentos das filiais
        # Calcular data do dia seguinte para colunas C, G, K (pagamos no dia seguinte ao recebimento)
        # Para i=0, buscar pagar de 13/05; para i=1, buscar pagar de 14/05; para i=2, buscar pagar de 15/05
        if i < 2:
            data_str_pagar_seguinte = dias_alvo[i + 1].strftime("%d/%m/%Y")
        else:
            # Para o último dia, usar o próximo dia útil
            next_day = dias_alvo[i] + timedelta(days=1)
            while not is_dia_util(next_day):
                next_day += timedelta(days=1)
            data_str_pagar_seguinte = next_day.strftime("%d/%m/%Y")
        
        for filial, linha in map_filiais.items():
            val_receber = dados.get(data_str_full_dados, {}).get('receber', {}).get(filial, 0)
            val_pagar = dados.get(data_str_full_pagar, {}).get('pagar', {}).get(filial, 0)
            val_pagar_seguinte = dados.get(data_str_pagar_seguinte, {}).get('pagar', {}).get(filial, 0)
            
            col_pagar = cols['pagar']
            print(f"    {filial}: {cols['receber']}{linha}={val_receber}, {col_pagar}{linha}={val_pagar}")
            
            # PreencherReceber (F) - apenas se não for None
            if cols['receber'] is not None:
                celula_rec = f"{cols['receber']}{linha}"
                await page.keyboard.press("F5")
                await asyncio.sleep(1)
                await page.keyboard.type(celula_rec)
                await page.keyboard.press("Enter")
                await asyncio.sleep(1)
                if val_receber > 0:
                    await page.keyboard.type(str(val_receber).replace('.', ','))
                else:
                    await page.keyboard.type("0")
                await page.keyboard.press("Enter")
            
            # Pular preenchimento de pagar para G, K (serão preenchidos separadamente depois)
            if cols['pagar'] in ["G", "K"]:
                continue
                
            celula_pag = f"{col_pagar}{linha}"
            await page.keyboard.press("F5")
            await asyncio.sleep(1)
            await page.keyboard.type(celula_pag)
            await page.keyboard.press("Enter")
            await asyncio.sleep(1)
            if val_pagar > 0:
                await page.keyboard.type(str(val_pagar).replace('.', ','))
            else:
                await page.keyboard.type("0")
            await page.keyboard.press("Enter")
                
    
        # -----------------------
        # Preencher colunas Receber (F, J) usando dados agregados
        # -----------------------
        receber_cols = ["F", "J"]
        for idx, col in enumerate(receber_cols):
            # data correspondente ao dia de recebimento
            data_str = dias_alvo[idx].strftime("%d/%m/%Y")
            for filial, linha in map_filiais.items():
                val = dados.get(data_str, {}).get('receber', {}).get(filial, 0)
                celula = f"{col}{linha}"
                await page.keyboard.press("F5")
                await asyncio.sleep(1)
                await page.keyboard.type(celula)
                await page.keyboard.press("Enter")
                await asyncio.sleep(1)
                if val > 0:
                    await page.keyboard.type(str(val).replace('.', ','))
                else:
                    await page.keyboard.type("0")
                await page.keyboard.press("Enter")
                await asyncio.sleep(0.5)
                print(f"    {filial} {col}{linha}: {val:.2f}")

        # -----------------------
        # Preencher colunas Pagar (C, G, K) usando dados agregados
        # -----------------------
        pagar_cols = ["C", "G", "K"]
        for idx, col in enumerate(pagar_cols):
            # data correspondente ao pagamento (já ajustada nas funções de ajuste)
            data_str = dias_alvo[idx].strftime("%d/%m/%Y")
            for filial, linha in map_filiais.items():
                val = dados.get(data_str, {}).get('pagar', {}).get(filial, 0)
                celula = f"{col}{linha}"
                await page.keyboard.press("F5")
                await asyncio.sleep(1)
                await page.keyboard.type(celula)
                await page.keyboard.press("Enter")
                await asyncio.sleep(1)
                if val > 0:
                    await page.keyboard.type(str(val).replace('.', ','))
                else:
                    await page.keyboard.type("0")
                await page.keyboard.press("Enter")
                await asyncio.sleep(0.5)
                print(f"    {filial} {col}{linha}: {val:.2f}")



        print("Preenchimento concluído.")
    data_f = dias_alvo[0]  # Recebíveis para 13/05
    print(f"  -> Preenchendo coluna F com Receber {data_f.strftime('%d/%m')} (sem ajuste)...")
    
    file_receber = os.path.join(BASE_DIR, "titulos a receber.zip")
    
    df_list_f = []
    with zipfile.ZipFile(file_receber, 'r') as z:
        for filename in z.namelist():
            if filename.endswith('.csv'):
                with z.open(filename) as f:
                    df_part = pd.read_csv(f, sep=';', encoding='latin-1', on_bad_lines='skip')
                    df_list_f.append(df_part)
    df_f = pd.concat(df_list_f, ignore_index=True)
    df_f['ttr_data_vencimento'] = pd.to_datetime(df_f['ttr_data_vencimento'], errors='coerce')
    df_f['ttr_valor_titulo'] = df_f['ttr_valor_titulo'].apply(clean_currency).fillna(0)
    df_f['ttr_saldo'] = df_f['ttr_saldo'].apply(clean_currency).fillna(0)
    df_f = df_f[df_f['ttr_saldo'] > 0]
    
    mask_f = (df_f['ttr_data_vencimento'] == pd.Timestamp(data_f))
    df_filtered_f = df_f[mask_f].copy()
    valores_f = df_filtered_f.groupby('fil_descricao')['ttr_valor_titulo'].sum().to_dict()
    
    print(f"Valores para F ({data_f.strftime('%d/%m')} Receber): {valores_f}")
    
    for filial, linha in map_filiais.items():
        filial_key = str(filial)
        val_f = valores_f.get(filial_key, 0)
        if val_f == 0:
            try:
                val_f = valores_f.get(float(filial_key), 0)
            except:
                val_f = 0
        
        celula_f = f"F{linha}"
        await page.keyboard.press("F5")
        await asyncio.sleep(1)
        await page.keyboard.type(celula_f)
        await page.keyboard.press("Enter")
        await asyncio.sleep(1)
        if val_f > 0:
            await page.keyboard.type(str(val_f).replace('.', ','))
        else:
            await page.keyboard.type("0")
        await page.keyboard.press("Enter")
        await asyncio.sleep(0.5)
        print(f"    {filial} F{linha}: {val_f:.2f}")
    
    # Preencher coluna G com Pagar - direto do CSV
    data_g = dias_alvo[1]  # Pagamento 14/05
    print(f"  -> Preenchendo coluna G com Pagar {data_g.strftime('%d/%m')}...")
    
    file_pagar = os.path.join(BASE_DIR, "titulos a pagar.zip")
    
    df_list_g = []
    with zipfile.ZipFile(file_pagar, 'r') as z:
        for filename in z.namelist():
            if filename.endswith('.csv'):
                with z.open(filename) as f:
                    df_part = pd.read_csv(f, sep=';', encoding='latin-1', on_bad_lines='skip')
                    df_list_g.append(df_part)
    df_g = pd.concat(df_list_g, ignore_index=True)
    df_g['ttp_data_vencimento'] = pd.to_datetime(df_g['ttp_data_vencimento'], errors='coerce')
    df_g['ttp_valor_titulo'] = df_g['ttp_valor_titulo'].apply(clean_currency).fillna(0)
    df_g['ttp_saldo'] = df_g['ttp_saldo'].apply(clean_currency).fillna(0)
    df_g = df_g[df_g['ttp_saldo'] > 0]
    
    mask_g = (df_g['ttp_data_vencimento'] == pd.Timestamp(data_g))
    df_filtered_g = df_g[mask_g].copy()
    valores_g = df_filtered_g.groupby('fil_descricao')['ttp_valor_titulo'].sum().to_dict()
    
    print(f"Valores para G ({data_g.strftime('%d/%m')} Pagar): {valores_g}")
    
    for filial, linha in map_filiais.items():
        filial_key = str(filial)
        val_g = valores_g.get(filial_key, 0)
        if val_g == 0:
            try:
                val_g = valores_g.get(float(filial_key), 0)
            except:
                val_g = 0
        
        celula_g = f"G{linha}"
        await page.keyboard.press("F5")
        await asyncio.sleep(1)
        await page.keyboard.type(celula_g)
        await page.keyboard.press("Enter")
        await asyncio.sleep(1)
        if val_g > 0:
            await page.keyboard.type(str(val_g).replace('.', ','))
        else:
            await page.keyboard.type("0")
        await page.keyboard.press("Enter")
        await asyncio.sleep(0.5)
        print(f"    {filial} G{linha}: {val_g:.2f}")
    
    # Preencher coluna J com Receber - sem ajuste de data (direto do CSV)
    data_j = dias_alvo[1]
    print(f"  -> Preenchendo coluna J com Receber {data_j.strftime('%d/%m')} (sem ajuste)...")
    
    file_receber = os.path.join(BASE_DIR, "titulos a receber.zip")
    
    df_list_j = []
    with zipfile.ZipFile(file_receber, 'r') as z:
        for filename in z.namelist():
            if filename.endswith('.csv'):
                with z.open(filename) as f:
                    df_part = pd.read_csv(f, sep=';', encoding='latin-1', on_bad_lines='skip')
                    df_list_j.append(df_part)
    df_j = pd.concat(df_list_j, ignore_index=True)
    df_j['ttr_data_vencimento'] = pd.to_datetime(df_j['ttr_data_vencimento'], errors='coerce')
    df_j['ttr_valor_titulo'] = df_j['ttr_valor_titulo'].apply(clean_currency).fillna(0)
    df_j['ttr_saldo'] = df_j['ttr_saldo'].apply(clean_currency).fillna(0)
    df_j = df_j[df_j['ttr_saldo'] > 0]
    
    mask_j = (df_j['ttr_data_vencimento'] == pd.Timestamp(data_j))
    df_filtered_j = df_j[mask_j].copy()
    valores_j = df_filtered_j.groupby('fil_descricao')['ttr_valor_titulo'].sum().to_dict()
    
    print(f"Valores para J ({data_j.strftime('%d/%m')} Receber): {valores_j}")
    
    for filial, linha in map_filiais.items():
        filial_key = str(filial)
        val_j = valores_j.get(filial_key, 0)
        if val_j == 0:
            try:
                val_j = valores_j.get(float(filial_key), 0)
            except:
                val_j = 0
        
        celula_j = f"J{linha}"
        await page.keyboard.press("F5")
        await asyncio.sleep(1)
        await page.keyboard.type(celula_j)
        await page.keyboard.press("Enter")
        await asyncio.sleep(1)
        if val_j > 0:
            await page.keyboard.type(str(val_j).replace('.', ','))
        else:
            await page.keyboard.type("0")
        await page.keyboard.press("Enter")
        await asyncio.sleep(0.5)
        print(f"    {filial} J{linha}: {val_j:.2f}")
                
    # Preencher coluna K com Pagar - direto do CSV
    data_k = dias_alvo[2]
    print(f"  -> Preenchendo coluna K com Pagar {data_k.strftime('%d/%m')}...")
    
    file_pagar = os.path.join(BASE_DIR, "titulos a pagar.zip")
    
    df_list_k = []
    with zipfile.ZipFile(file_pagar, 'r') as z:
        for filename in z.namelist():
            if filename.endswith('.csv'):
                with z.open(filename) as f:
                    df_part = pd.read_csv(f, sep=';', encoding='latin-1', on_bad_lines='skip')
                    df_list_k.append(df_part)
    df_k = pd.concat(df_list_k, ignore_index=True)
    df_k['ttp_data_vencimento'] = pd.to_datetime(df_k['ttp_data_vencimento'], errors='coerce')
    df_k['ttp_valor_titulo'] = df_k['ttp_valor_titulo'].apply(clean_currency).fillna(0)
    df_k['ttp_saldo'] = df_k['ttp_saldo'].apply(clean_currency).fillna(0)
    df_k = df_k[df_k['ttp_saldo'] > 0]
    
    # Soma de data_k
    datas = [pd.Timestamp(data_k)]
    df_k_filt = df_k[df_k['ttp_data_vencimento'].isin(datas)]
    valores_k = df_k_filt.groupby('fil_descricao')['ttp_valor_titulo'].sum().to_dict()
    
    print(f"Valores para K ({data_k.strftime('%d/%m')} Pagar): {valores_k}")
    
    for filial, linha in map_filiais.items():
        filial_key = str(filial)
        val_k = valores_k.get(filial_key, 0)
        if val_k == 0:
            try:
                val_k = valores_k.get(float(filial_key), 0)
            except:
                val_k = 0
        
        celula_k = f"K{linha}"
        await page.keyboard.press("F5")
        await asyncio.sleep(1)
        await page.keyboard.type(celula_k)
        await page.keyboard.press("Enter")
        await asyncio.sleep(1)
        if val_k > 0:
            await page.keyboard.type(str(val_k).replace('.', ','))
        else:
            await page.keyboard.type("0")
        await page.keyboard.press("Enter")
        await asyncio.sleep(0.5)
        print(f"    {filial} K{linha}: {val_k:.2f}")
    
    # Preencher coluna C com Pagamento 13/05 (mesmo dia que recebíveis de F)
    data_c = dias_alvo[0]
    print(f"  -> Preenchendo coluna C com Pagamento {data_c.strftime('%d/%m')}...")
    
    file_pagar_c = os.path.join(BASE_DIR, "titulos a pagar.zip")
    
    df_list_c = []
    with zipfile.ZipFile(file_pagar_c, 'r') as z:
        for filename in z.namelist():
            if filename.endswith('.csv'):
                with z.open(filename) as f:
                    df_part = pd.read_csv(f, sep=';', encoding='latin-1', on_bad_lines='skip')
                    df_list_c.append(df_part)
    df_c = pd.concat(df_list_c, ignore_index=True)
    df_c['ttp_data_vencimento'] = pd.to_datetime(df_c['ttp_data_vencimento'], errors='coerce')
    df_c['ttp_valor_titulo'] = df_c['ttp_valor_titulo'].apply(clean_currency).fillna(0)
    df_c['ttp_saldo'] = df_c['ttp_saldo'].apply(clean_currency).fillna(0)
    df_c = df_c[df_c['ttp_saldo'] > 0]
    
    mask_c = (df_c['ttp_data_vencimento'] == pd.Timestamp(data_c))
    df_filtered_c = df_c[mask_c].copy()
    valores_c = df_filtered_c.groupby('fil_descricao')['ttp_valor_titulo'].sum().to_dict()
    
    print(f"Valores para C ({data_c.strftime('%d/%m')} Pagar): {valores_c}")
    
    for filial, linha in map_filiais.items():
        filial_key = str(filial)
        val_c = valores_c.get(filial_key, 0)
        if val_c == 0:
            try:
                val_c = valores_c.get(float(filial_key), 0)
            except:
                val_c = 0
        
        celula_c = f"C{linha}"
        await page.keyboard.press("F5")
        await asyncio.sleep(1)
        await page.keyboard.type(celula_c)
        await page.keyboard.press("Enter")
        await asyncio.sleep(1)
        if val_c > 0:
            await page.keyboard.type(str(val_c).replace('.', ','))
        else:
            await page.keyboard.type("0")
        await page.keyboard.press("Enter")
        await asyncio.sleep(0.5)
        print(f"    {filial} C{linha}: {val_c:.2f}")
    
    # Preencher coluna M com Receber de hoje - direto do CSV
    data_m = hoje
    print(f"  -> Preenchendo coluna M com Receber {data_m.strftime('%d/%m')}...")
    
    file_receber = os.path.join(BASE_DIR, "titulos a receber.zip")
    
    df_list = []
    with zipfile.ZipFile(file_receber, 'r') as z:
        for filename in z.namelist():
            if filename.endswith('.csv'):
                with z.open(filename) as f:
                    df_part = pd.read_csv(f, sep=';', encoding='latin-1', on_bad_lines='skip')
                    df_list.append(df_part)
    df = pd.concat(df_list, ignore_index=True)
    df['ttr_data_vencimento'] = pd.to_datetime(df['ttr_data_vencimento'], errors='coerce')
    df['ttr_valor_titulo'] = df['ttr_valor_titulo'].apply(clean_currency).fillna(0)
    df['ttr_saldo'] = df['ttr_saldo'].apply(clean_currency).fillna(0)
    df = df[df['ttr_saldo'] > 0]
    
    mask = (df['ttr_data_vencimento'] == pd.Timestamp(data_m))
    df_filtered = df[mask].copy()
    valores_m = df_filtered.groupby('fil_descricao')['ttr_valor_titulo'].sum().to_dict()
    
    print(f"Valores para M ({data_m.strftime('%d/%m')} Receber): {valores_m}")
    
    for filial, linha in map_filiais.items():
        filial_key = str(filial)
        val_m = valores_m.get(filial_key, 0)
        if val_m == 0:
            try:
                val_m = valores_m.get(float(filial_key), 0)
            except:
                val_m = 0
        
        celula_m = f"M{linha}"
        await page.keyboard.press("F5")
        await asyncio.sleep(1)
        await page.keyboard.type(celula_m)
        await page.keyboard.press("Enter")
        await asyncio.sleep(1)
        if val_m > 0:
            await page.keyboard.type(str(val_m).replace('.', ','))
        else:
            await page.keyboard.type("0")
        await page.keyboard.press("Enter")
        await asyncio.sleep(0.5)
        print(f"    {filial} M{linha}: {val_m:.2f}")
    
    # Preencher F3:F7 com Pagar do dia atual
    dt_hoje_str = hoje.strftime("%d/%m/%Y")
    print(f"  -> Preenchendo F3:F7 com Pagar {dt_hoje_str}...")
    valores_pagar_hoje = dados.get(dt_hoje_str, {}).get('pagar', {})
    print(f"Valores para F3:F7: {valores_pagar_hoje}")
    
    map_f3_f7 = {
        "302": 3,
        "429": 4,
        "551": 5,
        "601": 6,
        "Nevine": 7
    }
    
    for filial, linha in map_f3_f7.items():
        val = valores_pagar_hoje.get(filial, 0)
        celula = f"F{linha}"
        await page.keyboard.press("F5")
        await asyncio.sleep(1)
        await page.keyboard.type(celula)
        await page.keyboard.press("Enter")
        await asyncio.sleep(1)
        if val > 0:
            await page.keyboard.type(str(val).replace('.', ','))
        else:
            await page.keyboard.type("0")
        await page.keyboard.press("Enter")
        await asyncio.sleep(0.5)
        print(f"    {filial} F{linha}: {val:.2f}")
    
    print("Preenchimento concluído.")
    return True

async def main():
    print("Iniciando Robô de Previsão...")
    str_inicio, str_fim, _, d_inicio, d_fim = calcular_datas()
    
    print(f"Período de extração: {str_inicio} até {str_fim}")
    
    local_app_data = os.getenv("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
    user_data_dir = os.path.join(local_app_data, "Automacao_Previsao", "sessao_nova")
    os.makedirs(user_data_dir, exist_ok=True)
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            viewport={"width": 1366, "height": 768},
            args=["--start-maximized"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        page.on("dialog", lambda dialog: dialog.accept())
        
        # 1. ERP
        sucesso = await login_erp(page)
        if sucesso:
            print("Baixando Títulos a Receber (2004)...")
            await baixar_relatorio(page, "2004", str_inicio, str_fim, "titulos a receber.zip")
            
            print("Baixando Títulos a Pagar (2015)...")
            await baixar_relatorio(page, "2015", str_inicio, str_fim, "titulos a pagar.zip")
            
        # 2. Pandas
        dados, valores_originais = processar_csvs(d_inicio, d_fim)
        
        # 3. Google Sheets
        await atualizar_planilha(page, dados, valores_originais)
        
        print("\nProcesso finalizado.")
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
