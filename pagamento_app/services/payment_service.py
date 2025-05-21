"""
Serviço de pagamento para o Assistente Virtual de Pagamentos.
Responsável por processar pagamentos e gerenciar transações.
"""

import os
import qrcode
import io
import base64
from datetime import datetime
from django.conf import settings
from django.core.mail import send_mail
from ..data import planos

class PaymentService:
    """
    Serviço para processamento de pagamentos e gerenciamento de transações.
    """
    
    def __init__(self):
        """Inicializa o serviço de pagamento."""
        # Configurações do serviço
        self.email_remetente = 'contato@assistentepagamentos.com'
    
    def processar_pagamento(self, metodo, plano_id, dados_usuario, dados_pagamento=None):
        """
        Processa um pagamento com base no método escolhido.
        
        Args:
            metodo (str): Método de pagamento (pix, boleto, cartao)
            plano_id (str): ID do plano
            dados_usuario (dict): Dados do usuário
            dados_pagamento (dict, optional): Dados específicos do pagamento
            
        Returns:
            dict: Resultado do processamento
        """
        if metodo == "pix":
            return self.processar_pagamento_pix(plano_id, dados_usuario)
        elif metodo == "boleto":
            return self.processar_pagamento_boleto(plano_id, dados_usuario)
        elif metodo == "cartao":
            return self.processar_pagamento_cartao(plano_id, dados_usuario, dados_pagamento)
        else:
            return {
                "sucesso": False,
                "mensagem": "Método de pagamento não suportado",
                "dados": {}
            }
    
    def processar_pagamento_pix(self, plano_id, dados_usuario):
        """
        Processa um pagamento via PIX.
        
        Args:
            plano_id (str): ID do plano
            dados_usuario (dict): Dados do usuário
            
        Returns:
            dict: Resultado do processamento
        """
        # Gerar código PIX
        codigo_pix = "00020101021226880014br.gov.bcb.pix2566qrcodes-pix.gerencianet.com.br/v2/cobv/22571380-6d75-4400-a463-8d502b8054865204000053039865802BR5925ASSISTENTE VIRTUAL DE PAG6009SAO PAULO62070503***6304E2CA"
        
        # Gerar QR Code
        qr_img = self.gerar_qr_code(codigo_pix)
        
        # Enviar por e-mail
        email = dados_usuario.get("email")
        if email:
            self.enviar_email_pix(email, codigo_pix, plano_id)
        
        # Registrar transação (simulado)
        transaction_id = f"PIX_{plano_id}_{datetime.now().timestamp()}"
        
        return {
            "sucesso": True,
            "mensagem": "Pagamento PIX iniciado com sucesso",
            "dados": {
                "transaction_id": transaction_id,
                "codigo_pix": codigo_pix,
                "qr_code": qr_img,
                "status": "pendente"
            }
        }
    
    def processar_pagamento_boleto(self, plano_id, dados_usuario):
        """
        Processa um pagamento via boleto.
        
        Args:
            plano_id (str): ID do plano
            dados_usuario (dict): Dados do usuário
            
        Returns:
            dict: Resultado do processamento
        """
        # Gerar código de barras
        codigo_barras = "34191.79001 01043.510047 91020.150008 9 89110000029990"
        
        # Enviar por e-mail
        email = dados_usuario.get("email")
        if email:
            self.enviar_email_boleto(email, codigo_barras, plano_id)
        
        # Registrar transação (simulado)
        transaction_id = f"BOLETO_{plano_id}_{datetime.now().timestamp()}"
        
        return {
            "sucesso": True,
            "mensagem": "Boleto gerado com sucesso",
            "dados": {
                "transaction_id": transaction_id,
                "codigo_barras": codigo_barras,
                "url_boleto": f"https://exemplo.com/boleto/{transaction_id}",
                "status": "pendente"
            }
        }
    
    def processar_pagamento_cartao(self, plano_id, dados_usuario, dados_cartao):
        """
        Processa um pagamento via cartão de crédito.
        
        Args:
            plano_id (str): ID do plano
            dados_usuario (dict): Dados do usuário
            dados_cartao (dict): Dados do cartão
            
        Returns:
            dict: Resultado do processamento
        """
        # Validar dados do cartão
        if not dados_cartao:
            return {
                "sucesso": False,
                "mensagem": "Dados do cartão não fornecidos",
                "dados": {}
            }
        
        # Verificar campos obrigatórios
        campos_obrigatorios = ["numero_cartao", "validade", "cvv", "nome_cartao"]
        for campo in campos_obrigatorios:
            if campo not in dados_cartao:
                return {
                    "sucesso": False,
                    "mensagem": f"Campo obrigatório ausente: {campo}",
                    "dados": {}
                }
        
        # Simular processamento com gateway de pagamento
        # Em um ambiente real, integraria com um gateway como Stripe, PagSeguro, etc.
        
        # Registrar transação (simulado)
        transaction_id = f"CARTAO_{plano_id}_{datetime.now().timestamp()}"
        
        # Enviar confirmação por e-mail
        email = dados_usuario.get("email")
        if email:
            self.enviar_email_confirmacao(email, plano_id)
        
        return {
            "sucesso": True,
            "mensagem": "Pagamento com cartão aprovado",
            "dados": {
                "transaction_id": transaction_id,
                "status": "aprovado"
            }
        }
    
    def gerar_qr_code(self, codigo_pix):
        """
        Gera um QR Code para pagamento PIX.
        
        Args:
            codigo_pix (str): Código PIX
            
        Returns:
            str: QR Code em formato base64
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(codigo_pix)
        qr.make(fit=True)
        
        # Gerar imagem
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Salvar em arquivo estático
        qr_path = os.path.join(settings.BASE_DIR, 'static', 'qr_code_pix.png')
        img.save(qr_path)
        
        # Converter para base64
        buffer = io.BytesIO()
        img.save(buffer)
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return qr_base64
    
    def enviar_email_pix(self, email, codigo_pix, plano_id):
        """
        Envia e-mail com código PIX.
        
        Args:
            email (str): E-mail do destinatário
            codigo_pix (str): Código PIX
            plano_id (str): ID do plano
            
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        try:
            plano_info = planos.get(plano_id, {})
            plano_nome = plano_id.capitalize()
            plano_preco = plano_info.get("preço", "")
            
            assunto = f'Seu Pagamento via PIX - Plano {plano_nome}'
            mensagem = f'''
            Olá!
            
            Aqui está o código PIX para pagamento do seu Plano {plano_nome} ({plano_preco}):
            
            {codigo_pix}
            
            Basta copiar e colar este código no aplicativo do seu banco para concluir o pagamento.
            
            Após a confirmação do pagamento, seu plano será ativado automaticamente.
            
            Atenciosamente,
            Equipe do Assistente Virtual de Pagamentos
            '''
            
            send_mail(
                assunto,
                mensagem,
                self.email_remetente,
                [email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Erro ao enviar e-mail PIX: {e}")
            return False
    
    def enviar_email_boleto(self, email, codigo_barras, plano_id):
        """
        Envia e-mail com código de barras do boleto.
        
        Args:
            email (str): E-mail do destinatário
            codigo_barras (str): Código de barras
            plano_id (str): ID do plano
            
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        try:
            plano_info = planos.get(plano_id, {})
            plano_nome = plano_id.capitalize()
            plano_preco = plano_info.get("preço", "")
            
            assunto = f'Seu Boleto de Pagamento - Plano {plano_nome}'
            mensagem = f'''
            Olá!
            
            Aqui está o código de barras do boleto para pagamento do seu Plano {plano_nome} ({plano_preco}):
            
            {codigo_barras}
            
            Você também pode acessar o boleto completo através do link:
            https://exemplo.com/boleto/{plano_id}_{datetime.now().timestamp()}
            
            Após a confirmação do pagamento, seu plano será ativado automaticamente.
            
            Atenciosamente,
            Equipe do Assistente Virtual de Pagamentos
            '''
            
            send_mail(
                assunto,
                mensagem,
                self.email_remetente,
                [email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Erro ao enviar e-mail boleto: {e}")
            return False
    
    def enviar_email_confirmacao(self, email, plano_id):
        """
        Envia e-mail de confirmação de pagamento.
        
        Args:
            email (str): E-mail do destinatário
            plano_id (str): ID do plano
            
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        try:
            plano_nome = plano_id.capitalize()
            
            assunto = f'Confirmação de Pagamento - Plano {plano_nome}'
            mensagem = f'''
            Olá!
            
            O pagamento do seu Plano {plano_nome} foi realizado com sucesso!
            
            Seu plano já está ativo e você pode começar a aproveitar todos os benefícios imediatamente.
            
            Agradecemos pela confiança!
            
            Atenciosamente,
            Equipe do Assistente Virtual de Pagamentos
            '''
            
            send_mail(
                assunto,
                mensagem,
                self.email_remetente,
                [email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Erro ao enviar e-mail de confirmação: {e}")
            return False
