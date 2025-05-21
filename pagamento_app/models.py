"""
Modelos de dados aprimorados para o Assistente Virtual de Pagamentos.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
import uuid

class Usuario(AbstractUser):
    """
    Modelo de usuário estendido com campos adicionais para o assistente de pagamentos.
    Herda de AbstractUser para aproveitar a autenticação do Django.
    """
    telefone = models.CharField(max_length=20, blank=True, null=True)
    cpf = models.CharField(max_length=14, blank=True, null=True)
    data_nascimento = models.DateField(blank=True, null=True)

    # Preferências do usuário
    receber_emails = models.BooleanField(default=True)
    receber_notificacoes = models.BooleanField(default=True)

    # Correção de conflitos com o modelo padrão do Django
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='usuario_set',
        related_query_name='usuario',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='usuario_set',
        related_query_name='usuario',
    )

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return self.username or self.email

class Plano(models.Model):
    # ... (sem alterações)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50, unique=True)
    nome = models.CharField(max_length=100)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.TextField()
    beneficios = models.JSONField()
    metodos_pagamento = models.JSONField()
    ativo = models.BooleanField(default=True)
    destaque = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Plano'
        verbose_name_plural = 'Planos'
        ordering = ['preco']

    def __str__(self):
        return f"{self.nome} (R${self.preco})"

class Assinatura(models.Model):
    # ... (sem alterações)
    STATUS_CHOICES = [
        ('ativa', 'Ativa'),
        ('pendente', 'Pendente'),
        ('cancelada', 'Cancelada'),
        ('expirada', 'Expirada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='assinaturas')
    plano = models.ForeignKey(Plano, on_delete=models.PROTECT, related_name='assinaturas')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    data_inicio = models.DateTimeField(null=True, blank=True)
    data_termino = models.DateTimeField(null=True, blank=True)
    renovacao_automatica = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Assinatura'
        verbose_name_plural = 'Assinaturas'
        ordering = ['-criada_em']

    def __str__(self):
        return f"{self.usuario} - {self.plano} ({self.status})"

    def esta_ativa(self):
        return (
            self.status == 'ativa' and
            (self.data_termino is None or self.data_termino > timezone.now())
        )

class Pagamento(models.Model):
    # ... (sem alterações)
    METODO_CHOICES = [
        ('pix', 'PIX'),
        ('boleto', 'Boleto'),
        ('cartao', 'Cartão de Crédito'),
    ]

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('processando', 'Processando'),
        ('aprovado', 'Aprovado'),
        ('recusado', 'Recusado'),
        ('cancelado', 'Cancelado'),
        ('estornado', 'Estornado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='pagamentos')
    assinatura = models.ForeignKey(Assinatura, on_delete=models.SET_NULL, null=True, blank=True, related_name='pagamentos')
    plano = models.ForeignKey(Plano, on_delete=models.PROTECT, related_name='pagamentos')
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    metodo = models.CharField(max_length=20, choices=METODO_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    gateway_response = models.JSONField(null=True, blank=True)
    data_pagamento = models.DateTimeField(null=True, blank=True)
    data_processamento = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.usuario} - {self.plano} - {self.valor} ({self.status})"

    def marcar_como_aprovado(self):
        self.status = 'aprovado'
        self.data_processamento = timezone.now()
        if self.assinatura:
            self.assinatura.status = 'ativa'
            self.assinatura.data_inicio = timezone.now()
            self.assinatura.data_termino = timezone.now() + timezone.timedelta(days=30)
            self.assinatura.save()
        self.save()

class Conversa(models.Model):
    # ... (sem alterações)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='conversas')
    session_id = models.CharField(max_length=100)
    iniciada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Conversa'
        verbose_name_plural = 'Conversas'
        ordering = ['-atualizada_em']

    def __str__(self):
        return f"Conversa {self.id} - {self.usuario}"

class Mensagem(models.Model):
    # ... (sem alterações)
    ORIGEM_CHOICES = [
        ('usuario', 'Usuário'),
        ('assistente', 'Assistente'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversa = models.ForeignKey(Conversa, on_delete=models.CASCADE, related_name='mensagens')
    texto = models.TextField()
    origem = models.CharField(max_length=20, choices=ORIGEM_CHOICES)
    intencao = models.CharField(max_length=100, blank=True, null=True)
    entidades = models.JSONField(null=True, blank=True)
    acoes = models.JSONField(null=True, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mensagem'
        verbose_name_plural = 'Mensagens'
        ordering = ['criada_em']

    def __str__(self):
        return f"{self.origem}: {self.texto[:50]}..."
