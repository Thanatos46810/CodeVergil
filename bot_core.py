import os
import requests
import ollama
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

def get_pr_diff(owner, repo, pr_number):
    """Busca o diff da PR usando a API do GitHub."""
    url_pr = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    
    headers = {
        "Accept": "application/vnd.github.diff",
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"
    }
    
    response = requests.get(url_pr, headers=headers)
    if response.status_code == 200:
        return response.text
    return None

def analisar_diff(diff, modelo="qwen2.5-coder:3b"):
    """Envia o diff para o Ollama local e retorna a string de review."""
    prompt = (
        "Você é um revisor de código experiente. Analise o seguinte diff de uma Pull Request "
        "e forneça um feedback construtivo em português. Foque em possíveis bugs, problemas de "
        "segurança e melhorias de legibilidade. Não invente problemas se o código estiver bom. "
        "Limite sua resposta ao essencial.\n\n"
        f"Diff:\n{diff}"
    )
    
    resposta = ollama.generate(model=modelo, prompt=prompt)
    return resposta['response']

def comentar_na_pr(owner, repo, pr_number, review):
    """Posta o review como um comentário na PR."""
    url_comments = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github+json"
    }
    payload = {"body": review}
    
    response = requests.post(url_comments, headers=headers, json=payload)
    return response.status_code == 201

def enviar_telegram(mensagem):
    """Envia a análise do review diretamente para o Telegram."""
    token = "8890942277:AAE92Fcw7oaIBsP_97Zq6jQthyQRoNdHTro"
    chat_id = "8072537497"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": mensagem,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("[SUCESSO] Notificação enviada para o Telegram!")
        else:
            print(f"[ERRO] Falha ao enviar para o Telegram: {response.text}")
    except Exception as e:
        print(f"[ERRO] Exceção ao enviar para o Telegram: {e}")

def processar_review_background(owner, repo, pr_number):
    """Função orquestradora que vai rodar em Thread (segundo plano)."""
    print(f"\n[BACKGROUND] Buscando diff da PR #{pr_number}...")
    diff = get_pr_diff(owner, repo, pr_number)
    
    if not diff:
        print(f"[ERRO] Não foi possível obter o diff da PR #{pr_number}.")
        return

    print(f"[BACKGROUND] Analisando diff com Ollama (Isso pode demorar na CPU)...")
    review = analisar_diff(diff)
    
    print(f"[BACKGROUND] Postando comentário no GitHub...")
    sucesso = comentar_na_pr(owner, repo, pr_number, review)
    
    if sucesso:
        print(f"[SUCESSO] Review postado na PR #{pr_number}!")
    else:
        print(f"[ERRO] Falha ao postar review na PR #{pr_number}.")

    # Envia o resultado completo para o Telegram
    print(f"[BACKGROUND] Enviando notificação para o Telegram...")
    mensagem_telegram = f"🤖 *Review da PR #{pr_number} ({repo})*\n\n{review}"
    enviar_telegram(mensagem_telegram)