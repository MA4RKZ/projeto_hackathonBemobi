# pagamento_app/models.py
from django.db import models

class Usuario(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

class Plano(models.Model):
    nome = models.CharField(max_length=50)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.TextField()
    beneficios = models.JSONField()
    pagamento = models.JSONField()

class Pagamento(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    plano = models.ForeignKey(Plano, on_delete=models.CASCADE, related_name='pagamentos')  # Adiciona related_name
    metodo = models.CharField(max_length=20, choices=[('PIX', 'PIX'), ('Boleto', 'Boleto'), ('Cartão', 'Cartão')])
    status = models.CharField(max_length=20, default='Pendente')
    data_pagamento = models.DateTimeField(null=True, blank=True)
