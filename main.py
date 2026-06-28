import os
import requests
import ollama
from dotenv import load_dotenv


def buscar_pr_e_diff(owner, repo):
    """Lista as PRs abertas, deixa o usuario escolher uma e retorna numero, titulo e diff."""
    url_prs = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    prs = requests.get(url_prs).json()

    if len(prs) == 0:
        print("Nenhuma PR aberta nesse repositorio no momento.")
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


def postar_comentario(owner, repo, numero, texto, token):
    """Posta um comentario numa PR do GitHub."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{numero}/comments"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }
    dados = {"body": texto}
    resposta = requests.post(url, headers=headers, json=dados)

    if resposta.status_code == 201:
        print("Review postado como comentario na PR!")
    else:
        print(f"Erro ao postar comentario. Codigo: {resposta.status_code}")
        print(resposta.text)


def salvar_review(numero, titulo, review):
    """Salva o review num arquivo de texto."""
    nome_arquivo = "review.txt"
    with open(nome_arquivo, "w", encoding="utf-8") as arquivo:
        arquivo.write(f"Review da PR #{numero} - {titulo}\n")
        arquivo.write("=" * 50 + "\n\n")
        arquivo.write(review)
    print(f"Review salvo no arquivo: {nome_arquivo}")


def main():
    """Funcao principal: coordena a busca da PR, a analise pela IA e o comentario."""
    # Carrega o token do arquivo .env
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        print("ERRO: token nao encontrado. Confira o arquivo .env")
        return

    OWNER = "Thanatos46810"
    REPO = "bot-teste"
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

    # Salva no arquivo
    salvar_review(numero, titulo, review)

    # Posta o review como comentario na PR
    print()
    print("Postando review na PR...")
    postar_comentario(OWNER, REPO, numero, review, token)


if __name__ == "__main__":
    main()