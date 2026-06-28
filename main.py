import requests
import ollama

OWNER = "psf"
REPO = "requests"
MODELO = "qwen2.5-coder:3b"

# 1. Buscar as PRs abertas
url_prs = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls"
prs = requests.get(url_prs).json()

if len(prs) == 0:
    print("Nenhuma PR aberta no momento.")
    exit()

# 2. Pegar a primeira PR
primeira_pr = prs[0]
numero = primeira_pr["number"]
titulo = primeira_pr["title"]
print(f"Analisando PR #{numero} - {titulo}")
print()

# 3. Buscar o diff dessa PR
url_pr = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls/{numero}"
headers = {"Accept": "application/vnd.github.diff"}
diff = requests.get(url_pr, headers=headers).text

# Cortar o diff se for muito grande (a IA tem limite de tamanho)
diff_cortado = diff[:3000]

# 4. Montar a instrucao (prompt) pra IA
prompt = f"""Voce e um revisor de codigo experiente.
Analise o diff abaixo de uma Pull Request e responda em portugues:
1. O que essa mudanca faz (resumo curto).
2. Ha algum problema, risco ou melhoria possivel?

Seja direto e objetivo.

DIFF:
{diff_cortado}
"""

# 5. Mandar pra IA local e receber a resposta
print("Enviando pra IA... (pode demorar, esta rodando na CPU)")
print()

resposta = ollama.chat(
    model=MODELO,
    messages=[{"role": "user", "content": prompt}]
)

# 6. Mostrar o review
print("=== REVIEW DA IA ===")
print(resposta["message"]["content"])