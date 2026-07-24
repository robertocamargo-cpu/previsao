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
- Sábado → Próximo dia útil
- Domingo → Próximo dia útil
- Feriado → Próximo dia útil
- Dia útil → Próprio dia

Exemplos:
- Se o próximo dia útil for segunda-feira, os recebíveis de sábado, domingo e segunda-feira são somados na segunda.
- Se houver feriado antes de um dia útil, os recebíveis do feriado são somados nesse próximo dia útil.
- Se o vencimento já cair em dia útil, ele permanece no próprio dia.

### Ajuste de Data para Pagamentos
- Sábado → Sexta-feira anterior (-1 dia)
- Domingo → Sexta-feira anterior (-2 dias)
- Feriado → Dia útil anterior
- Dia útil → Próprio dia

Resumo: recebíveis empurram datas não úteis para frente; pagamentos puxam datas não úteis para trás.

### Feriados
Os feriados ficam em `feriados.md`.

O arquivo deve conter feriados nacionais, estaduais de São Paulo e municipais de São Paulo. A automação aceita:
- `DD/MM - Nome do feriado` para feriados recorrentes todo ano
- `YYYY-MM-DD - Nome do feriado` para feriados específicos

### Abas da Planilha
- A nova aba é criada a partir da aba com data mais recente anterior ao dia atual.
- Depois de criada e renomeada, a nova aba é movida para a primeira posição da planilha.

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

## Agendamento (Cron)

O script é executado automaticamente via crontab todos os dias úteis:

```
30 9 * * 1-5   cd /Users/nevine/Documents/previsao && /usr/bin/python3 automacao_previsao.py >> previsao_cron.log 2>&1
```

| Campo | Valor | Significado |
|-------|-------|-------------|
| Horário | `09:30` | Executa às 09h30 |
| Dias | `1-5` | Segunda a Sexta |
| Log | `previsao_cron.log` | Saída registrada no diretório do projeto |

## Execução Manual
```bash
python automacao_previsao.py
```

## Dry-run
Use para conferir datas, feriados e células calculadas sem abrir ERP nem Google Sheets:

```bash
python automacao_previsao.py --dry-run --data 2026-07-10
```

## Preenchimento
A automação monta uma lista única de células antes de escrever na planilha. Isso evita preencher a mesma coluna várias vezes e facilita conferir o resultado no dry-run.

Campos principais:
- `E1` recebe a data da previsão
- `C13`, `G13`, `K13` recebem os mesmos rótulos de `C15`, `G15`, `K15`
- `F/J/M` usam títulos a receber
- `C/G/K` usam títulos a pagar
- `F3:F7` usa pagamentos do dia da previsão

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
