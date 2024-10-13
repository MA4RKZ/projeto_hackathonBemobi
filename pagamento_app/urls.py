from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicial_view, name='inicial_view'),  # Formulário inicial
    path('assistente/resposta/', views.chatbot_response, name='chatbot_response'),  # API de resposta do assistente
]
