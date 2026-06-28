import requests
import ollama


def buscar_pr_e_diff(owner, repo):
    """Busca a primeira PR aberta de um repositorio e retorna numero, titulo e diff."""
    url_prs = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    prs = requests.get(url_prs).json()

    if len(prs) == 0:
        return None, None, None

    primeira_pr = prs[0]
    numero = primeira_pr["number"]
    titulo = primeira_pr["title"]

    url_pr = f"https://api.github.com/repos/{owner}/{repo}/pulls/{numero}"
    headers = {"Accept": "application/vnd.github.diff"}
    diff = requests.get(url_pr, headers=headers).text

    return numero, titulo, diff


def analisar_diff(diff, modelo):
    """Envia o diff para a IA local e retorna o texto do review."""
    diff_cortado = diff[:3000]

    prompt = f"""Voce e um revisor de codigo experiente.
Analise o diff abaixo de uma Pull Request e responda em portugues:
1. O que essa mudanca faz (resumo curto).
2. Ha algum problema, risco ou melhoria possivel?

Seja direto e objetivo.

DIFF:
{diff_cortado}
"""

    resposta = ollama.chat(
        model=modelo,
        messages=[{"role": "user", "content": prompt}]
    )
    return resposta["message"]["content"]


def main():
    """Funcao principal: coordena a busca da PR e a analise pela IA."""
    OWNER = "psf"
    REPO = "requests"
    MODELO = "qwen2.5-coder:3b"

    print("Buscando PR no GitHub...")
    numero, titulo, diff = buscar_pr_e_diff(OWNER, REPO)

    if numero is None:
        print("Nenhuma PR aberta nesse repositorio no momento.")
        return

    print(f"Analisando PR #{numero} - {titulo}")
    print("Enviando pra IA... (pode demorar, esta rodando na CPU)")
    print()

    review = analisar_diff(diff, MODELO)

    print("=== REVIEW DA IA ===")
    print(review)


if __name__ == "__main__":
    main()