"""
Configurações de autenticação e autorização para o Assistente Virtual de Pagamentos.
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Autenticação personalizada que permite login com username ou email.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        
        try:
            # Verificar se o usuário existe com o username ou email fornecido
            user = UserModel.objects.filter(
                Q(username=username) | Q(email=username)
            ).first()
            
            # Verificar a senha
            if user and user.check_password(password):
                return user
                
        except UserModel.DoesNotExist:
            return None
            
        return None
