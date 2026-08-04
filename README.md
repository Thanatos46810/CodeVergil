# PR Review Bot....

Um revisor de código automático que usa **IA local** (rodando 100% offline, sem custo) para analisar Pull Requests do GitHub.

Ao apontar para um repositório, o bot busca uma Pull Request aberta, extrai as mudanças de código (diff) e envia para um modelo de IA local, que devolve uma análise técnica em português: o que a mudança faz e se há riscos ou melhorias possíveis.

##  Tecnologias

- **Python 3**
- **GitHub REST API** — para ler Pull Requests e seus diffs
- **Ollama** + **Qwen2.5-Coder** — modelo de IA rodando localmente, sem API paga

## Como funciona

1. Conecta na API do GitHub e lista as Pull Requests abertas de um repositório
2. Seleciona uma PR e baixa o diff (as linhas adicionadas e removidas)
3. Envia o diff para a IA local com um prompt de revisão
4. Exibe o review gerado pela IA

## Como rodar.....

```bash
# 1. Clonar o repositório
git clone https://github.com/Thanatos46810/pr-review-bot.git
cd pr-review-bot

# 2. Criar e ativar o ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar as dependências
pip install requests ollama

# 4. Instalar o Ollama e baixar o modelo
# (https://ollama.com)
ollama pull qwen2.5-coder:3b

# 5. Rodar
python3 main.py
```

##  Limitações e próximos passos

Este é um MVP funcional. Pontos em evolução:

- Analisa apenas a primeira PR aberta (próximo: escolher PR específica)
- O diff é cortado em 3000 caracteres para caber no modelo
- Por usar um modelo pequeno rodando na CPU, a análise é mais lenta e pode ter imprecisões em detalhes
- **Em desenvolvimento:** comentários linha a linha e automação via webhook (bot reagindo sozinho quando uma PR é aberta)
online 2.0 versionando para automação

---

Projeto desenvolvido como estudo prático de integração de APIs e IA local.
