import requests
import ollama


def buscar_pr_e_diff(owner, repo):
    """Lista as PRs abertas, deixa o usuario escolher uma e retorna numero, titulo e diff."""
    url_prs = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    prs = requests.get(url_prs).json()

    if len(prs) == 0:
        return None, None, None

    print("PRs abertas neste repositorio:")
    for pr in prs:
        print(f"  #{pr['number']} - {pr['title']}")
    print()

    escolha = input("Digite o numero da PR que voce quer analisar: ")
    try:
        numero = int(escolha)
    except ValueError:
        print(f"'{escolha}' nao e um numero valido. Rode o programa de novo e digite um numero.")
        return None, None, None

    titulo = None
    for pr in prs:
        if pr["number"] == numero:
            titulo = pr["title"]

    if titulo is None:
        print(f"Nao encontrei a PR #{numero} na lista de PRs abertas.")
        return None, None, None

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


def salvar_review(numero, titulo, review):
    """Salva o review num arquivo de texto."""
    nome_arquivo = "review.txt"
    with open(nome_arquivo, "w", encoding="utf-8") as arquivo:
        arquivo.write(f"Review da PR #{numero} - {titulo}\n")
        arquivo.write("=" * 50 + "\n\n")
        arquivo.write(review)
    print(f"Review salvo no arquivo: {nome_arquivo}")


def main():
    """Funcao principal: coordena a busca da PR e a analise pela IA."""
    OWNER = "psf"
    REPO = "requests"
    MODELO = "qwen2.5-coder:3b"

    print("Buscando PRs no GitHub...")
    print()
    numero, titulo, diff = buscar_pr_e_diff(OWNER, REPO)

    if numero is None:
        return

    print()
    print(f"Analisando PR #{numero} - {titulo}")
    print("Enviando pra IA... (pode demorar, esta rodando na CPU)")
    print()

    review = analisar_diff(diff, MODELO)

    print("=" * 50)
    print(f"REVIEW DA PR #{numero} - {titulo}")
    print("=" * 50)
    print()
    print(review)
    print()

    salvar_review(numero, titulo, review)


if __name__ == "__main__":
    main()