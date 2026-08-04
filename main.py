import os
import json
import requests
import ollama
from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()

app = Flask(__name__)

MODELO = "qwen2.5-coder:3b"


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

    return resposta.status_code == 201


def enviar_telegram(mensagem):
    """Envia a analise do review diretamente para o Telegram."""
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
            print("[SUCESSO] Notificacao enviada para o Telegram!")
        else:
            print(f"[ERRO] Falha ao enviar para o Telegram: {response.text}")
    except Exception as e:
        print(f"[ERRO] Excecao ao enviar para o Telegram: {e}")


@app.route('/webhook', methods=['POST'])
def webhook():
    """Recebe o evento do GitHub via webhook e dispara a analise."""
    data = request.get_json(silent=True)
    
    # Se não vier como JSON puro, tenta capturar caso venha em form-urlencoded do GitHub
    if not data and request.form:
        payload_str = request.form.get("payload")
        if payload_str:
            try:
                data = json.loads(payload_str)
            except json.JSONDecodeError:
                data = None

    if not data:
        return jsonify({"error": "Invalid payload"}), 400

    action = data.get("action")
    pull_request = data.get("pull_request")
    repository = data.get("repository")

    if pull_request and repository and action in ["opened", "synchronize"]:
        numero = pull_request["number"]
        titulo = pull_request["title"]
        owner = repository["owner"]["login"]
        repo = repository["name"]
        
        print(f"\n[WEBHOOK] PR #{numero} detectada em {owner}/{repo}: {titulo}")
        print("Buscando diff...")
        
        token = os.getenv("GITHUB_TOKEN")
        diff = get_pr_diff(owner, repo, numero)
        
        if diff:
            print("Analisando diff com o Ollama...")
            review = analisar_diff(diff, MODELO)
            
            print("Postando comentario no GitHub...")
            postar_comentario(owner, repo, numero, review, token)
            
            print("Enviando notificacao para o Telegram...")
            mensagem_telegram = f"🤖 *Review da PR #{numero} ({repo})*\n\n{review}"
            enviar_telegram(mensagem_telegram)
        else:
            print("[ERRO] Nao foi possivel obter o diff.")

    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)