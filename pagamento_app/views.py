"""
Views para o Assistente Virtual de Pagamentos.
Responsável por renderizar templates e coordenar a interação com o usuário.
"""

from django.shortcuts import render
from django.http import JsonResponse
from .api.chat_api import chatbot_response as api_chatbot_response
from .api.chat_api import process_payment as api_process_payment

def inicial_view(request):
    """
    View para exibir o template do formulário inicial do usuário.
    
    Args:
        request: Requisição HTTP
        
    Returns:
        Resposta HTTP com o template renderizado
    """
    if request.method == "POST":
        # Capturar dados do formulário
        nome = request.POST.get("nome")
        email = request.POST.get("email")
        
        # Armazenar na sessão
        request.session["nome"] = nome
        request.session["email"] = email
        
        # Redirecionar para o assistente
        return render(request, "pagamento_app/assistente.html", {"nome": nome})

    # Exibir formulário inicial
    return render(request, "pagamento_app/inicial.html")

def assistente_view(request):
    """
    View para exibir o template do assistente virtual.
    
    Args:
        request: Requisição HTTP
        
    Returns:
        Resposta HTTP com o template renderizado
    """
    # Obter nome da sessão
    nome = request.session.get("nome", "Usuário")
    
    # Renderizar template do assistente
    return render(request, "pagamento_app/assistente.html", {"nome": nome})

# Delegação para as APIs
def chatbot_response(request):
    """
    View para processar mensagens do chatbot.
    Delega para a API correspondente.
    
    Args:
        request: Requisição HTTP
        
    Returns:
        JsonResponse: Resposta do assistente
    """
    return api_chatbot_response(request)

def process_payment(request):
    """
    View para processar pagamentos.
    Delega para a API correspondente.
    
    Args:
        request: Requisição HTTP
        
    Returns:
        JsonResponse: Resultado do processamento
    """
    return api_process_payment(request)
