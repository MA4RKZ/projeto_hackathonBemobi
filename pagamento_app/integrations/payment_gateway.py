"""
Integração com APIs de pagamento para o Assistente Virtual de Pagamentos.
Implementa conexões com gateways de pagamento simulados.
"""

import requests
import json
import uuid
import hmac
import hashlib
import base64
import time
from datetime import datetime
from django.conf import settings

class PaymentGateway:
    """
    Classe base para integração com gateways de pagamento.
    """
    
    def __init__(self, api_key=None, api_secret=None):
        """
        Inicializa o gateway de pagamento com credenciais.
        
        Args:
            api_key (str, optional): Chave de API do gateway
            api_secret (str, optional): Segredo de API do gateway
        """
        self.api_key = api_key or settings.PAYMENT_API_KEY
        self.api_secret = api_secret or settings.PAYMENT_API_SECRET
        
    def process_payment(self, payment_data):
        """
        Processa um pagamento através do gateway.
        
        Args:
            payment_data (dict): Dados do pagamento
            
        Returns:
            dict: Resultado do processamento
        """
        raise NotImplementedError("Método deve ser implementado pelas subclasses")
    
    def check_status(self, transaction_id):
        """
        Verifica o status de uma transação.
        
        Args:
            transaction_id (str): ID da transação
            
        Returns:
            dict: Status atual da transação
        """
        raise NotImplementedError("Método deve ser implementado pelas subclasses")
    
    def refund(self, transaction_id, amount=None):
        """
        Solicita estorno de uma transação.
        
        Args:
            transaction_id (str): ID da transação
            amount (float, optional): Valor a ser estornado. Se None, estorna o valor total.
            
        Returns:
            dict: Resultado do estorno
        """
        raise NotImplementedError("Método deve ser implementado pelas subclasses")

class MockPaymentGateway(PaymentGateway):
    """
    Gateway de pagamento simulado para testes e demonstração.
    """
    
    def __init__(self, api_key=None, api_secret=None, simulate_error=False):
        """
        Inicializa o gateway simulado.
        
        Args:
            api_key (str, optional): Chave de API simulada
            api_secret (str, optional): Segredo de API simulado
            simulate_error (bool, optional): Se deve simular erros de processamento
        """
        super().__init__(api_key, api_secret)
        self.simulate_error = simulate_error
        self.transactions = {}
        
    def process_payment(self, payment_data):
        """
        Simula o processamento de um pagamento.
        
        Args:
            payment_data (dict): Dados do pagamento
            
        Returns:
            dict: Resultado simulado do processamento
        """
        # Validar dados mínimos
        required_fields = ['amount', 'payment_method', 'customer_email']
        for field in required_fields:
            if field not in payment_data:
                return {
                    'success': False,
                    'error': f'Campo obrigatório ausente: {field}',
                    'error_code': 'MISSING_FIELD'
                }
        
        # Simular erro se configurado
        if self.simulate_error:
            return {
                'success': False,
                'error': 'Erro de processamento simulado',
                'error_code': 'SIMULATED_ERROR'
            }
        
        # Gerar ID de transação
        transaction_id = str(uuid.uuid4())
        
        # Simular processamento com base no método de pagamento
        payment_method = payment_data['payment_method']
        amount = payment_data['amount']
        
        # Criar transação simulada
        transaction = {
            'id': transaction_id,
            'amount': amount,
            'payment_method': payment_method,
            'customer_email': payment_data['customer_email'],
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Processar com base no método de pagamento
        if payment_method == 'pix':
            transaction['status'] = 'pending'
            transaction['pix_code'] = f"00020101021226880014br.gov.bcb.pix2566qrcodes-pix.example.com/v2/cobv/{transaction_id}5204000053039865802BR5925ASSISTENTE VIRTUAL DE PAG6009SAO PAULO62070503***6304{self._generate_checksum(transaction_id)}"
            transaction['qr_code_url'] = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={transaction['pix_code']}"
            
        elif payment_method == 'boleto':
            transaction['status'] = 'pending'
            transaction['barcode'] = f"34191{str(int(amount*100)).zfill(10)}01043510047910201500089{int(time.time())%10000}"
            transaction['boleto_url'] = f"https://exemplo.com/boleto/{transaction_id}"
            
        elif payment_method == 'credit_card':
            # Validar dados do cartão
            card_data = payment_data.get('card_data', {})
            if not card_data or not all(k in card_data for k in ['number', 'expiry', 'cvv', 'holder_name']):
                return {
                    'success': False,
                    'error': 'Dados do cartão incompletos',
                    'error_code': 'INVALID_CARD_DATA'
                }
            
            # Simular aprovação com base no número do cartão
            # Números terminados em número par são aprovados, ímpares são recusados
            card_number = card_data['number'].replace(' ', '')
            if int(card_number[-1]) % 2 == 0:
                transaction['status'] = 'approved'
            else:
                transaction['status'] = 'declined'
                return {
                    'success': False,
                    'error': 'Cartão recusado pela operadora',
                    'error_code': 'CARD_DECLINED',
                    'transaction_id': transaction_id
                }
        else:
            return {
                'success': False,
                'error': 'Método de pagamento não suportado',
                'error_code': 'INVALID_PAYMENT_METHOD'
            }
        
        # Armazenar transação
        self.transactions[transaction_id] = transaction
        
        # Retornar resultado
        return {
            'success': True,
            'transaction_id': transaction_id,
            'status': transaction['status'],
            'data': transaction
        }
    
    def check_status(self, transaction_id):
        """
        Verifica o status de uma transação simulada.
        
        Args:
            transaction_id (str): ID da transação
            
        Returns:
            dict: Status atual da transação
        """
        if transaction_id not in self.transactions:
            return {
                'success': False,
                'error': 'Transação não encontrada',
                'error_code': 'TRANSACTION_NOT_FOUND'
            }
        
        transaction = self.transactions[transaction_id]
        
        # Simular atualização de status para PIX e boleto
        # Em um cenário real, isso seria atualizado por webhooks
        if transaction['status'] == 'pending' and transaction['payment_method'] in ['pix', 'boleto']:
            # Simular 50% de chance de pagamento confirmado
            if uuid.uuid4().int % 2 == 0:
                transaction['status'] = 'approved'
                transaction['updated_at'] = datetime.now().isoformat()
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'status': transaction['status'],
            'data': transaction
        }
    
    def refund(self, transaction_id, amount=None):
        """
        Simula o estorno de uma transação.
        
        Args:
            transaction_id (str): ID da transação
            amount (float, optional): Valor a ser estornado
            
        Returns:
            dict: Resultado do estorno
        """
        if transaction_id not in self.transactions:
            return {
                'success': False,
                'error': 'Transação não encontrada',
                'error_code': 'TRANSACTION_NOT_FOUND'
            }
        
        transaction = self.transactions[transaction_id]
        
        # Verificar se a transação pode ser estornada
        if transaction['status'] != 'approved':
            return {
                'success': False,
                'error': 'Apenas transações aprovadas podem ser estornadas',
                'error_code': 'INVALID_REFUND_STATUS'
            }
        
        # Processar estorno
        refund_amount = amount or transaction['amount']
        if refund_amount > transaction['amount']:
            return {
                'success': False,
                'error': 'Valor de estorno maior que o valor da transação',
                'error_code': 'INVALID_REFUND_AMOUNT'
            }
        
        # Atualizar transação
        transaction['status'] = 'refunded'
        transaction['refunded_amount'] = refund_amount
        transaction['updated_at'] = datetime.now().isoformat()
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'refunded_amount': refund_amount,
            'status': 'refunded',
            'data': transaction
        }
    
    def _generate_checksum(self, data):
        """
        Gera um checksum para dados de transação.
        
        Args:
            data: Dados para gerar checksum
            
        Returns:
            str: Checksum gerado
        """
        key = self.api_secret.encode() if self.api_secret else b'mock_secret_key'
        message = str(data).encode()
        digest = hmac.new(key, message, hashlib.sha256).digest()
        return base64.b64encode(digest).decode()[:4]

class MercadoPagoGateway(PaymentGateway):
    """
    Integração com o gateway de pagamento MercadoPago.
    """
    
    def __init__(self, api_key=None, api_secret=None):
        """
        Inicializa a integração com MercadoPago.
        
        Args:
            api_key (str, optional): Chave de API do MercadoPago
            api_secret (str, optional): Segredo de API do MercadoPago
        """
        super().__init__(api_key, api_secret)
        self.base_url = "https://api.mercadopago.com/v1"
        
    def process_payment(self, payment_data):
        """
        Processa um pagamento através do MercadoPago.
        
        Args:
            payment_data (dict): Dados do pagamento
            
        Returns:
            dict: Resultado do processamento
        """
        # Em um ambiente real, faria uma chamada à API do MercadoPago
        # Aqui, simulamos o comportamento
        
        # Simular gateway real com o mock
        mock_gateway = MockPaymentGateway(self.api_key, self.api_secret)
        return mock_gateway.process_payment(payment_data)
    
    def check_status(self, transaction_id):
        """
        Verifica o status de uma transação no MercadoPago.
        
        Args:
            transaction_id (str): ID da transação
            
        Returns:
            dict: Status atual da transação
        """
        # Em um ambiente real, faria uma chamada à API do MercadoPago
        # Aqui, simulamos o comportamento
        
        # Simular gateway real com o mock
        mock_gateway = MockPaymentGateway(self.api_key, self.api_secret)
        return mock_gateway.check_status(transaction_id)
    
    def refund(self, transaction_id, amount=None):
        """
        Solicita estorno de uma transação no MercadoPago.
        
        Args:
            transaction_id (str): ID da transação
            amount (float, optional): Valor a ser estornado
            
        Returns:
            dict: Resultado do estorno
        """
        # Em um ambiente real, faria uma chamada à API do MercadoPago
        # Aqui, simulamos o comportamento
        
        # Simular gateway real com o mock
        mock_gateway = MockPaymentGateway(self.api_key, self.api_secret)
        return mock_gateway.refund(transaction_id, amount)

# Factory para criar instâncias de gateway com base na configuração
def get_payment_gateway(gateway_name=None):
    """
    Obtém uma instância do gateway de pagamento configurado.
    
    Args:
        gateway_name (str, optional): Nome do gateway a ser usado
        
    Returns:
        PaymentGateway: Instância do gateway de pagamento
    """
    gateway_name = gateway_name or getattr(settings, 'PAYMENT_GATEWAY', 'mock')
    
    if gateway_name == 'mercadopago':
        return MercadoPagoGateway(
            api_key=getattr(settings, 'MERCADOPAGO_API_KEY', None),
            api_secret=getattr(settings, 'MERCADOPAGO_API_SECRET', None)
        )
    else:
        # Gateway padrão para testes e desenvolvimento
        return MockPaymentGateway(
            api_key=getattr(settings, 'MOCK_PAYMENT_API_KEY', 'test_key'),
            api_secret=getattr(settings, 'MOCK_PAYMENT_API_SECRET', 'test_secret'),
            simulate_error=getattr(settings, 'MOCK_PAYMENT_SIMULATE_ERROR', False)
        )
