# Previsao Automation - Diretrizes Operacionais

## Objetivo
Executar a automacao de previsao financeira sem interferir na automacao de GNRE.

## Regras atuais
- Script principal: `automacao_previsao.py`.
- Tela correta dos relatorios financeiros no ERP: `https://erp.admsis.com/Home?eng_tela=0117030100`.
- A tela antiga `0107030100` nao deve ser usada para baixar os relatorios 2004/2015, pois pode retornar `Tela nao encontrada`.
- Relatorio `2004`: Titulos a Receber, salvar como `titulos a receber.zip`.
- Relatorio `2015`: Titulos a Pagar, salvar como `titulos a pagar.zip`.
- Antes de selecionar o relatorio, aguardar `select#relatorio` aparecer.

## Planilha
- Se a aba do dia atual ja existir, abrir essa aba e sobrescrever os dados calculados.
- Se a aba do dia atual nao existir, duplicar a aba com data mais recente anterior ao dia atual e renomear para hoje.
- Nao excluir a aba de hoje para recriar. A exclusao depende de menu/modal do Google Sheets e e mais arriscada.
- A aba do dia deve ficar na primeira posicao quando possivel.

## Execucao
- A previsao pode ser executada manualmente com `python3 -u automacao_previsao.py`.
- O fluxo completo baixa os dois ZIPs, processa os CSVs, preenche 50 celulas e envia aviso ao Discord.
- Para testar sem alterar ERP/Google Sheets, usar `--dry-run` quando adequado.

## Observacao importante
Este projeto e separado da GNRE. Ao trabalhar aqui, nao alterar arquivos nem agendamentos da pasta `gnre`.
