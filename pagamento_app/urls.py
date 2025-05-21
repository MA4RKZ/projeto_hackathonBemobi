"""
URLs para o Assistente Virtual de Pagamentos.
Define os endpoints disponíveis na aplicação.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Views principais
    path('', views.inicial_view, name='inicial_view'),
    path('assistente/', views.assistente_view, name='assistente_view'),
    
    # APIs
    path('api/assistente/resposta/', views.chatbot_response, name='chatbot_response'),
    path('api/pagamento/processar/', views.process_payment, name='process_payment'),
]
