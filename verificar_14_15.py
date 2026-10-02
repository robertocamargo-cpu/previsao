"""
Diagnóstico: Verificação de títulos a receber e a pagar para 14/09 e 15/09/2026.
Mostra contagens, valores brutos e o que a lógica de ajuste de datas faria.
"""
import zipfile
import os
import pandas as pd
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_receber = os.path.join(BASE_DIR, "titulos a receber.zip")
file_pagar   = os.path.join(BASE_DIR, "titulos a pagar.zip")

DATAS_ALVO = [
    pd.Timestamp("2026-09-14"),
    pd.Timestamp("2026-09-15"),
]

# ─── Feriados ────────────────────────────────────────────────────────────────
FERIADOS_RECORRENTES = {
    (1, 1), (21, 4), (1, 5), (9, 7), (7, 9),
    (12, 10), (2, 11), (15, 11), (20, 11), (25, 12)
}

def is_dia_util(d):
    if hasattr(d, "weekday"):
        if d.weekday() >= 5:
            return False
    if (d.day, d.month) in FERIADOS_RECORRENTES:
        return False
    return True

def proximo_dia_util(d):
    d = d + timedelta(days=1)
    while not is_dia_util(d):
        d += timedelta(days=1)
    return d

def dia_util_anterior(d):
    d = d - timedelta(days=1)
    while not is_dia_util(d):
        d -= timedelta(days=1)
    return d

def ajustar_data_receber(d):
    if pd.isna(d): return d
    if not is_dia_util(d):
        return proximo_dia_util(d)
    return d

def ajustar_data_pagar(d):
    if pd.isna(d): return d
    if not is_dia_util(d):
        return dia_util_anterior(d)
    return d

def clean_currency(x):
    if isinstance(x, str):
        return float(x.replace('.', '').replace(',', '.'))
    return x

def ler_zip(path):
    df_list = []
    with zipfile.ZipFile(path, 'r') as z:
        for filename in z.namelist():
            if filename.endswith('.csv'):
                with z.open(filename) as f:
                    df_part = pd.read_csv(f, sep=';', encoding='latin-1', on_bad_lines='skip')
                    df_list.append(df_part)
    if not df_list:
        return pd.DataFrame()
    return pd.concat(df_list, ignore_index=True)

def analisar(path, date_col, value_col, filial_col, saldo_col, ajuste_fn, titulo):
    print(f"\n{'='*70}")
    print(f"  {titulo}")
    print(f"  Arquivo: {os.path.basename(path)}")
    print(f"{'='*70}")

    df = ler_zip(path)
    if df.empty:
        print("  [ERRO] DataFrame vazio.")
        return

    df[date_col]  = pd.to_datetime(df[date_col], errors='coerce')
    df[value_col] = df[value_col].apply(clean_currency).fillna(0)
    df[saldo_col] = df[saldo_col].apply(clean_currency).fillna(0)

    # Filtrar só registros com saldo > 0
    df_saldo = df[df[saldo_col] > 0].copy()

    for data in DATAS_ALVO:
        dia_str = data.strftime('%d/%m/%Y')
        print(f"\n  ── Data ORIGINAL: {dia_str} ──────────────────────────────────")

        mask_orig = df_saldo[date_col] == data
        df_orig   = df_saldo[mask_orig]
        total_registros = len(df_orig)
        total_valor     = df_orig[value_col].sum()

        print(f"  Registros com saldo>0 nessa data : {total_registros}")
        print(f"  Valor total                      : R$ {total_valor:,.2f}")
        if total_registros > 0:
            print(f"  Por filial:")
            for filial, grp in df_orig.groupby(filial_col):
                cnt = len(grp)
                val = grp[value_col].sum()
                print(f"    {str(filial):30s}  qtd={cnt:4d}  valor=R$ {val:,.2f}")

        # Com ajuste de data
        print(f"\n  ── Após ajuste de datas (o que vai para a planilha) ──────────────")
        df_aj = df_saldo.copy()
        df_aj[date_col] = df_aj[date_col].apply(ajuste_fn)
        mask_aj = df_aj[date_col] == data
        df_aj_f = df_aj[mask_aj]
        total_aj = len(df_aj_f)
        total_val_aj = df_aj_f[value_col].sum()

        dia_semana = data.strftime('%A')  # Monday, Tuesday...
        semana_pt  = {"Monday":"Segunda","Tuesday":"Terça","Wednesday":"Quarta",
                      "Thursday":"Quinta","Friday":"Sexta","Saturday":"Sábado","Sunday":"Domingo"}
        print(f"  {dia_str} é {semana_pt.get(dia_semana, dia_semana)} → ", end="")
        if is_dia_util(data):
            print("dia útil ✓")
        else:
            ajustado = ajuste_fn(data)
            print(f"NÃO útil → ajustado para {ajustado.strftime('%d/%m/%Y')}")

        print(f"  Registros que CHEGAM nessa data (pós-ajuste): {total_aj}")
        print(f"  Valor total pós-ajuste                       : R$ {total_val_aj:,.2f}")
        if total_aj > 0:
            print(f"  Por filial:")
            for filial, grp in df_aj_f.groupby(filial_col):
                cnt = len(grp)
                val = grp[value_col].sum()
                print(f"    {str(filial):30s}  qtd={cnt:4d}  valor=R$ {val:,.2f}")

# ─── Mapeamento de células ─────────────────────────────────────────────────
# Hoje = 16/09/2026 (terça). calcular_datas devolve:
#   dt_nova = 16/09 (hoje)
#   dias_alvo = [17/09 (quarta), 18/09 (quinta), 19/09 (sexta)]  — 3 próximos dias úteis
#
# Células:
#   B15 = dt_nova (16/09)       C15 = dias_alvo[0] (17/09)
#   F15 = dias_alvo[0] (17/09)  G15 = dias_alvo[1] (18/09)
#   J15 = dias_alvo[1] (18/09)  K15 = dias_alvo[2] (19/09)
#
# F{linha} = receber ajustado no dias_alvo[0]  (17/09)
# G{linha} = pagar   no dias_alvo[1]           (18/09)
# J{linha} = receber ajustado no dias_alvo[1]  (18/09)
# K{linha} = pagar   no dias_alvo[2]           (19/09)
# C{linha} = pagar   no dias_alvo[0]           (17/09)
# M{linha} = receber ajustado em dt_nova       (16/09)

if __name__ == "__main__":
    print("\n" + "🔍 DIAGNÓSTICO DE NOTAS/BOLETOS — DIAS 14 e 15/09/2026".center(70))

    # Verificar se 15/09 é feriado (Proclamação da República = 15/11, não 15/09)
    # 07/09 = Independência. 15/09 não é feriado nacional.
    print("\n  Verificação de dias úteis:")
    for d in DATAS_ALVO:
        util = is_dia_util(d)
        semana_pt = {"Monday":"Segunda","Tuesday":"Terça","Wednesday":"Quarta",
                     "Thursday":"Quinta","Friday":"Sexta","Saturday":"Sábado","Sunday":"Domingo"}
        nome_dia = semana_pt.get(d.strftime('%A'), d.strftime('%A'))
        print(f"    {d.strftime('%d/%m/%Y')} ({nome_dia}): {'✅ dia útil' if util else '❌ NÃO útil'}")

    if os.path.exists(file_receber):
        analisar(file_receber,
                 date_col="ttr_data_vencimento",
                 value_col="ttr_valor_titulo",
                 filial_col="fil_descricao",
                 saldo_col="ttr_saldo",
                 ajuste_fn=ajustar_data_receber,
                 titulo="TÍTULOS A RECEBER (notas / boletos a receber)")
    else:
        print(f"\n[AVISO] Arquivo não encontrado: {file_receber}")

    if os.path.exists(file_pagar):
        analisar(file_pagar,
                 date_col="ttp_data_vencimento",
                 value_col="ttp_valor_titulo",
                 filial_col="fil_descricao",
                 saldo_col="ttp_saldo",
                 ajuste_fn=ajustar_data_pagar,
                 titulo="TÍTULOS A PAGAR (boletos a pagar)")
    else:
        print(f"\n[AVISO] Arquivo não encontrado: {file_pagar}")

    print("\n" + "="*70)
    print("  Fim do diagnóstico.")
    print("="*70 + "\n")
