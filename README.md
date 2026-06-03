# Automação de Previsão Financeira

## Objetivo
Automatizar o preenchimento da planilha Google Sheets com dados de títulos a receber e a pagar do ERP.

## Estrutura da Planilha

### Colunas e Significados
| Coluna | Significado |
|--------|-------------|
| **F** | Recebíveis do dia 12/05 |
| **C** | Pagamentos do dia 12/05 |
| **J** | Recebíveis do dia 13/05 |
| **G** | Pagamentos do dia 13/05 |
| **K** | Pagamentos do dia 14/05 |
| **M** | Recebíveis originais de 09-11/05 (sem ajuste de data) |

> **Nota**: Coluna B não deve ser alterada (possui fórmula).

### Filiais por Linha
| Linha | Filial |
|-------|--------|
| 16 | 302 |
| 17 | 429 |
| 18 | 551 |
| 19 | 601 |
| 20 | Nevine |

## Lógica de Datas

### Ajuste de Data para Recebíveis
- Sábado → Sexta-feira anterior (-2 dias)
- Domingo → Sexta-feira anterior (-1 dia)

### Ajuste de Data para Pagamentos
- Sábado → Sexta-feira anterior (-1 dia)
- Domingo → Sexta-feira anterior (-2 dias)

## Arquivos
- `automacao_previsao.py` - Script principal
- `titulos a receber.zip` - Dados baixados do ERP (recebíveis)
- `titulos a pagar.zip` - Dados baixados do ERP (pagamentos)

## Correções Aplicadas

### 1. Ajuste de Data Receber
```python
def ajustar_data_receber(d):
    if pd.isna(d):
        return d
    wd = d.weekday()  # 0=Seg, 1=Ter, 2=Qua, 3=Qui, 4=Sex, 5=Sáb, 6=Dom
    if wd == 5:   # Sábado → Sexta anterior (-2)
        return d - timedelta(days=2)
    elif wd == 6: # Domingo → Sexta anterior (-1)
        return d - timedelta(days=1)
    return d
```

### 2. Conversão de Chaves do Dicionário
As chaves do dicionário vinham como "429.0" e precisam ser convertidas para "429":
```python
filial_str = str(int(float(key[1]))) if isinstance(key[1], (int, float)) else str(key[1])
```

### 3. Mapeamento de Colunas
```python
colunas_por_dia = [
    {"header": "F13", "receber": "F", "pagar": "C"},  # Dia 1 = 12/05
    {"header": "J13", "receber": "J", "pagar": "G"},  # Dia 2 = 13/05
    {"header": "N13", "receber": "N", "pagar": "K"}   # Dia 3 = 14/05
]
```

### 4. Preenchimento de Zeros
Sempre preencher com "0" quando o valor for zero:
```python
if val_pagar > 0:
    await page.keyboard.type(str(val_pagar).replace('.', ','))
else:
    await page.keyboard.type("0")
```

## Execução
```bash
python automacao_previsao.py
```

## Fluxo
1. Login no ERP (se necessário)
2. Download dos relatórios 2004 (receber) e 2015 (pagar)
3. Processamento dos CSVs
4. Preenchimento da planilha Google Sheets

## Troubleshooting

### Valores não aparecem na planilha
- Verificar se o navegador está em primeiro plano
- Verificar logs de execução para ver os valores being preenchidos

### Valores incorretos
- Verificar se o ajuste de data está correto
- Verificar se as chaves do dicionário estão no formato correto

### Coluna B sendo alterada
- Removida do loop de preenchimento por ter fórmula