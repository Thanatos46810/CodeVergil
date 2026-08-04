import requests

# Token novo atualizado
token = "8890942277:AAE92Fcw7oaIBsP_97Zq6jQthyQRoNdHTro"
chat_id = "8072537497"

print(f"Token lido: {token[:10]}...")
print(f"Chat ID lido: {chat_id}")

url = f"https://api.telegram.org/bot{token}/sendMessage"
payload = {
    "chat_id": chat_id,
    "text": "🤖 Teste direto com o token novo!"
}

response = requests.post(url, json=payload)
print(f"Status Code: {response.status_code}")
print(f"Resposta da API: {response.text}")