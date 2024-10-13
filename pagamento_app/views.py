import json
import os
import spacy
import unicodedata
import nltk
import qrcode
from transformers import pipeline
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from .data import planos

# Carregar modelo do spaCy e configurar NLTK
nlp = spacy.load("pt_core_news_lg")
nltk.download("punkt")
nltk.download("stopwords")
stop_words = set(nltk.corpus.stopwords.words("portuguese"))

# Carregar o modelo de geração de texto
generator = pipeline("text-generation", model="pierreguillou/gpt2-small-portuguese")

# Armazenamento do contexto por sessão de usuário
contexto_sessao = {}

# Função para normalizar o texto
def normalizar_texto(texto):
    texto = texto.replace("PIX", "pix")
    texto = unicodedata.normalize('NFKD', texto)
    texto = "".join([c for c in texto if not unicodedata.combining(c)])
    return texto.lower()

# Função para extrair palavras-chave e tipo de pergunta
def extrair_palavras_chave(texto):
    print("Texto recebido para análise:", texto)
    texto_normalizado = normalizar_texto(texto)
    tokens = nltk.word_tokenize(texto_normalizado)
    tokens_limpos = [word for word in tokens if word not in stop_words]

    doc = nlp(" ".join(tokens_limpos))
    palavras_chave = {token.lemma_ for token in doc if token.pos_ in ["NOUN", "VERB", "ADJ"]}

    if 'pix' in tokens_limpos:
        palavras_chave.add('pix')

    plano, tipo_informacao = None, None
    if "basico" in palavras_chave:
        plano = "basico"
    elif "premium" in palavras_chave:
        plano = "premium"
    
    if "preco" in palavras_chave or "valor" in palavras_chave:
        tipo_informacao = "preço"
    elif any(kw in palavras_chave for kw in ["beneficio", "vantagem", "oferece", "oferecer"]):
        tipo_informacao = "benefícios"
    elif "descricao" in palavras_chave or "informacao" in palavras_chave:
        tipo_informacao = "descrição"
    elif "pagamento" in palavras_chave or "forma de pagamento" in palavras_chave:
        tipo_informacao = "pagamento"
    elif "pix" in palavras_chave:
        tipo_informacao = "prosseguir_pagamento_pix"
    elif "boleto" in palavras_chave:
        tipo_informacao = "prosseguir_pagamento_boleto"
    elif "cartao" in palavras_chave or "cartão" in palavras_chave:
        tipo_informacao = "prosseguir_pagamento_cartao"
    elif "assinar" in palavras_chave:
        tipo_informacao = "assinatura"
    elif "cancelar" in palavras_chave:
        tipo_informacao = "cancelamento"
    elif any(kw in palavras_chave for kw in ["planos", "disponivel", "existem"]):
        tipo_informacao = "planos_disponiveis"

    print(f"Palavras-chave extraídas: {palavras_chave}")
    print(f"Plano identificado: {plano}, Tipo de informação identificado: {tipo_informacao}")
    return plano, tipo_informacao

# Função para gerar resposta personalizada com o modelo de linguagem
def gerar_resposta_texto_generativo(contexto, entrada_usuario):
    nome = contexto.get("nome", "Usuário")
    prompt = f"{nome} perguntou: '{entrada_usuario}'"
    resposta_gerada = generator(prompt, max_length=50, num_return_sequences=1)[0]["generated_text"]
    return resposta_gerada

# Função para gerenciar o fluxo de informações do cartão de crédito
def fluxo_pagamento_cartao(contexto, resposta_usuario):
    etapa = contexto.get("etapa_cartao", 0)
    dados_cartao = contexto.setdefault("dados_cartao", {})

    if etapa == 0:
        contexto["etapa_cartao"] = 1
        return "Por favor, insira o número do cartão."
    elif etapa == 1:
        dados_cartao["numero_cartao"] = resposta_usuario
        contexto["etapa_cartao"] = 2
        return "Agora, informe a validade (MM/AA)."
    elif etapa == 2:
        dados_cartao["validade"] = resposta_usuario
        contexto["etapa_cartao"] = 3
        return "Insira o CVV do cartão."
    elif etapa == 3:
        dados_cartao["cvv"] = resposta_usuario
        contexto["etapa_cartao"] = 4
        return "Informe o nome que está no cartão."
    elif etapa == 4:
        dados_cartao["nome_cartao"] = resposta_usuario
        contexto["etapa_cartao"] = 5
        return "Por fim, informe o CPF."
    elif etapa == 5:
        dados_cartao["cpf"] = resposta_usuario
        contexto["etapa_cartao"] = 6

        # Enviar e-mail de confirmação de pagamento
        enviar_email_confirmacao_pagamento(contexto["email"], contexto["plano_atual"])
        contexto["etapa_cartao"] = 0  # Resetar o fluxo do cartão
        return "Pagamento realizado com sucesso! Seu plano foi ativado. Posso ajudar com mais alguma coisa?"

# Função para enviar e-mail de confirmação de pagamento
def enviar_email_confirmacao_pagamento(email, plano):
    try:
        send_mail(
            'Confirmação de Pagamento',
            f'O pagamento do plano {plano.capitalize()} foi realizado com sucesso! Seu plano já está ativo.',
            'contato@seusistema.com',
            [email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Erro ao enviar e-mail de confirmação: {e}")

# Função para gerar QR Code e enviar por e-mail
def enviar_qr_code_email_com_codigo_pix(email, codigo_pix):
    qr_path = os.path.join(settings.BASE_DIR, 'static', 'qr_code_pix.png')
    qr = qrcode.make(codigo_pix)
    qr.save(qr_path)
    try:
        send_mail(
            'Seu Pagamento via PIX',
            f'Código PIX (copia e cola): {codigo_pix}',
            'contato@seusistema.com',
            [email],
            fail_silently=False,
        )
        return "QR Code e código PIX enviados para seu e-mail com sucesso."
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return "Erro ao enviar QR Code por e-mail."

# Função para enviar boleto por e-mail
def enviar_boleto_email(email, codigo_barras):
    try:
        send_mail(
            'Seu Boleto de Pagamento',
            f'Código de barras do boleto: {codigo_barras}',
            'contato@seusistema.com',
            [email],
            fail_silently=False,
        )
        return "Boleto enviado para seu e-mail com sucesso."
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return "Erro ao enviar boleto por e-mail."

# Função para gerar resposta com saudação personalizada e informações de pagamento
def gerar_resposta(plano, tipo_informacao, contexto):
    nome = contexto.get("nome")
    if plano:
        contexto["plano_atual"] = plano
    plano = contexto.get("plano_atual")

    if plano and plano not in planos:
        return "Por favor, especifique o plano (Básico ou Premium)."

    info_plano = planos.get(plano)

    if tipo_informacao == "preço":
        return f"{nome}, o plano {plano.capitalize()} custa {info_plano.get('preço')}."
    elif tipo_informacao == "benefícios":
        beneficios = "\n- " + "\n- ".join(info_plano.get("benefícios", []))
        return f"{nome}, o plano {plano.capitalize()} oferece os seguintes benefícios: {beneficios}."
    elif tipo_informacao == "descrição":
        return info_plano.get("descrição", "Descrição não disponível.")
    elif tipo_informacao == "pagamento":
        pagamentos = ", ".join(info_plano.get("pagamento", []))
        return f"As opções de pagamento para o plano {plano.capitalize()} são: {pagamentos}."
    elif tipo_informacao == "assinatura":
        return f"{nome}, o plano {plano.capitalize()} pode ser assinado pelo nosso site ou app."
    elif tipo_informacao == "cancelamento":
        return f"O cancelamento do plano {plano.capitalize()} pode ser feito pelo suporte."
    elif tipo_informacao == "prosseguir_pagamento_pix":
        codigo_pix = "123456789ABCDEF"
        resposta_email = enviar_qr_code_email_com_codigo_pix(contexto["email"], codigo_pix)
        return f"Código PIX para pagamento (copia e cola): {codigo_pix}. {resposta_email}"
    elif tipo_informacao == "prosseguir_pagamento_boleto":
        codigo_barras = "12345678901234567890123456789012345678901234"
        resposta_email = enviar_boleto_email(contexto["email"], codigo_barras)
        return f"{resposta_email}"
    elif tipo_informacao == "prosseguir_pagamento_cartao":
        return fluxo_pagamento_cartao(contexto, "")
    elif tipo_informacao == "planos_disponiveis":
        resposta = f"{nome}, estes são os planos disponíveis:\n"
        for nome_plano, detalhes in planos.items():
            descricao = detalhes.get("descrição", "Descrição não disponível.")
            preco = detalhes.get("preço", "Preço não disponível.")
            resposta += f"\nPlano {nome_plano.capitalize()}:\n  - Preço: {preco}\n  - Descrição: {descricao}\n"
        return resposta

    entrada_usuario = contexto.get("entrada_atual", "")
    return gerar_resposta_texto_generativo(contexto, entrada_usuario)

# View para exibir o template do formulário inicial do usuário
def inicial_view(request):
    if request.method == "POST":
        nome = request.POST.get("nome")
        email = request.POST.get("email")
        request.session["nome"] = nome
        request.session["email"] = email
        return render(request, "pagamento_app/assistente.html", {"nome": nome})

    return render(request, "pagamento_app/inicial.html")

# View para processar mensagens do chatbot via JSON
@csrf_exempt
def chatbot_response(request):
    if request.method == "POST":
        session_id = request.session.session_key or request.session.create()
        if session_id not in contexto_sessao:
            contexto_sessao[session_id] = {
                "plano_atual": None,
                "nome": request.session.get("nome", "Usuário"),
                "email": request.session.get("email"),
                "etapa_cartao": 0,
                "dados_cartao": {}
            }
        
        contexto = contexto_sessao[session_id]
        try:
            data = json.loads(request.body)
            entrada_usuario = data.get("mensagem", "")
            contexto["entrada_atual"] = entrada_usuario
            print(f"Pergunta do usuário: {entrada_usuario}")

            plano, tipo_informacao = extrair_palavras_chave(entrada_usuario)
            resposta = gerar_resposta(plano, tipo_informacao, contexto)

            print(f"Resposta do assistente: {resposta}")
            return JsonResponse({"resposta": resposta})
        except json.JSONDecodeError:
            return JsonResponse({"resposta": "Erro ao processar a mensagem."})
        except Exception as e:
            print(f"Erro ao processar a mensagem: {e}")
            return JsonResponse({"resposta": f"Erro ao processar a mensagem: {str(e)}"})
    return JsonResponse({"resposta": "Use o chat para enviar mensagens."})
