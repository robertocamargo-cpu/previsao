import re

with open('erp_2004_form.html', encoding='utf-8') as f:
    html = f.read()

# Buscar o bloco do select tipo_nota
match = re.search(r'id=["\']tipo_nota["\'].*?</select>', html, re.DOTALL | re.IGNORECASE)
if match:
    bloco = match.group(0)
    print("=== SELECT tipo_nota ===")
    print(bloco[:3000])
else:
    # Tentar busca mais ampla
    match2 = re.search(r'tipo_nota.{0,2000}?</select>', html, re.DOTALL | re.IGNORECASE)
    if match2:
        print("=== Resultado alternativo ===")
        print(match2.group(0)[:3000])
    else:
        print("Campo tipo_nota NAO encontrado no HTML salvo.")
        # Buscar NF-e
        nfe_match = re.findall(r'.{100}NF.{0,2}e.{100}', html, re.IGNORECASE)
        for m in nfe_match:
            print("NF-e context:", m)
