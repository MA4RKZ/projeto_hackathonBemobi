"""
Configurações de autenticação e middleware para o Assistente Virtual de Pagamentos.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from functools import wraps
import json

def api_login_required(view_func):
    """
    Decorador para verificar se o usuário está autenticado em endpoints de API.
    Retorna erro JSON em vez de redirecionar para a página de login.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'erro': 'Autenticação necessária',
                'codigo': 401
            }, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper

class APILoginRequiredMixin:
    """
    Mixin para verificar se o usuário está autenticado em views baseadas em classe.
    Retorna erro JSON em vez de redirecionar para a página de login.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'erro': 'Autenticação necessária',
                'codigo': 401
            }, status=401)
        return super().dispatch(request, *args, **kwargs)

def api_permission_required(permission):
    """
    Decorador para verificar se o usuário tem uma permissão específica.
    Retorna erro JSON em vez de redirecionar.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.has_perm(permission):
                return JsonResponse({
                    'erro': 'Permissão negada',
                    'codigo': 403
                }, status=403)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

class APIPermissionRequiredMixin(UserPassesTestMixin):
    """
    Mixin para verificar se o usuário tem permissões específicas.
    Retorna erro JSON em vez de redirecionar.
    """
    permission_required = None
    
    def test_func(self):
        if self.permission_required is None:
            return True
        if isinstance(self.permission_required, str):
            perms = (self.permission_required,)
        else:
            perms = self.permission_required
        return self.request.user.has_perms(perms)
    
    def handle_no_permission(self):
        return JsonResponse({
            'erro': 'Permissão negada',
            'codigo': 403
        }, status=403)

class JSONMiddleware:
    """
    Middleware para processar automaticamente requisições JSON.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Processar requisições JSON
        if request.content_type == 'application/json':
            try:
                request.json = json.loads(request.body)
            except json.JSONDecodeError:
                request.json = None
        
        response = self.get_response(request)
        return response
