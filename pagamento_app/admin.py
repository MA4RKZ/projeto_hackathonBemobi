from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Usuario, Plano, Pagamento

# Registra os modelos no Django Admin
admin.site.register(Usuario)
admin.site.register(Plano)
admin.site.register(Pagamento)
