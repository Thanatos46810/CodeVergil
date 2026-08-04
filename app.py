import os
import hmac
import hashlib
import threading
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from bot_core import processar_review_background

load_dotenv()

# Instancia o aplicativo Flask primeiro
app = Flask(__name__)
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

def verificar_assinatura(payload_body, header_signature):
    """Valida se o webhook realmente foi enviado pelo GitHub usando nosso secret."""
    if not WEBHOOK_SECRET:
        return True
    
    if not header_signature:
        return False
        
    mac = hmac.new(WEBHOOK_SECRET.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + mac.hexdigest()
    return hmac.compare_digest(expected_signature, header_signature)

@app.route('/webhook', methods=['POST'])
def webhook():
    # 1. Validação de segurança
    signature = request.headers.get('X-Hub-Signature-256')
    if not verificar_assinatura(request.data, signature):
        return jsonify({'error': 'Assinatura HMAC inválida'}), 403

    event = request.headers.get('X-GitHub-Event')
    
    # 2. Responde ao ping inicial
    if event == 'ping':
        return jsonify({'msg': 'Pong! Webhook conectado com sucesso.'}), 200
        
    # 3. Lida com a Pull Request
    if event == 'pull_request':
        payload = request.get_json(silent=True)
        if not payload and request.form:
            import json
            payload_str = request.form.get("payload")
            if payload_str:
                payload = json.loads(payload_str)
                
        if not payload:
            return jsonify({'error': 'Payload inválido'}), 400

        action = payload.get('action')
        
        if action in ['opened', 'synchronize']:
            pr_number = payload['pull_request']['number']
            repo_full_name = payload['repository']['full_name']
            owner, repo = repo_full_name.split('/')
            
            print(f"[WEBHOOK] Evento de PR recebido: {repo_full_name}#{pr_number} (Ação: {action})")
            
            thread = threading.Thread(
                target=processar_review_background, 
                args=(owner, repo, pr_number)
            )
            thread.start()
            
            return jsonify({'msg': 'Processamento de review iniciado em background'}), 202

    return jsonify({'msg': f'Evento {event} ignorado'}), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'bot online'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)