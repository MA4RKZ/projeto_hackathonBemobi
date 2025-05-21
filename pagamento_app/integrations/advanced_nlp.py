"""
Integração com modelos de linguagem natural avançados para o Assistente Virtual de Pagamentos.
"""

import os
import requests
import json
from django.conf import settings

class AdvancedNLPProcessor:
    """
    Processador avançado de linguagem natural que utiliza modelos LLM modernos
    para compreensão de intenções e geração de respostas naturais.
    """
    
    def __init__(self, api_key=None, model=None):
        """
        Inicializa o processador com configurações para API de LLM.
        
        Args:
            api_key (str, optional): Chave de API para o serviço de LLM
            model (str, optional): Nome do modelo a ser utilizado
        """
        self.api_key = api_key or os.environ.get('LLM_API_KEY') or getattr(settings, 'LLM_API_KEY', None)
        self.model = model or os.environ.get('LLM_MODEL') or getattr(settings, 'LLM_MODEL', 'gpt-3.5-turbo')
        self.api_url = os.environ.get('LLM_API_URL') or getattr(settings, 'LLM_API_URL', 'https://api.openai.com/v1/chat/completions')
        
        # Definir sistema de fallback para quando a API não estiver disponível
        self.use_fallback = False
        
        # Contexto do sistema para o assistente
        self.system_context = """
        Você é um assistente virtual especializado em pagamentos e planos de assinatura.
        Seu objetivo é ajudar usuários a:
        1. Obter informações sobre planos disponíveis (Básico e Premium)
        2. Processar pagamentos via PIX, boleto ou cartão de crédito
        3. Verificar histórico de transações
        4. Resolver dúvidas sobre assinaturas e pagamentos
        
        Seja sempre cordial, objetivo e forneça informações precisas.
        """
    
    def process_message(self, message, context=None):
        """
        Processa uma mensagem do usuário usando LLM avançado.
        
        Args:
            message (str): Mensagem do usuário
            context (dict, optional): Contexto da conversa
            
        Returns:
            dict: Resultado do processamento com intenção, entidades e resposta sugerida
        """
        if self.use_fallback or not self.api_key:
            return self._process_with_fallback(message, context)
        
        try:
            return self._process_with_llm_api(message, context)
        except Exception as e:
            print(f"Erro ao processar com API de LLM: {e}")
            self.use_fallback = True
            return self._process_with_fallback(message, context)
    
    def _process_with_llm_api(self, message, context):
        """
        Processa mensagem usando API de LLM externa.
        
        Args:
            message (str): Mensagem do usuário
            context (dict, optional): Contexto da conversa
            
        Returns:
            dict: Resultado do processamento
        """
        # Preparar contexto para o modelo
        messages = [
            {"role": "system", "content": self.system_context}
        ]
        
        # Adicionar histórico de conversa se disponível
        if context and 'historico' in context:
            for item in context['historico'][-5:]:  # Últimas 5 mensagens
                if 'texto_usuario' in item:
                    messages.append({"role": "user", "content": item['texto_usuario']})
                if 'texto_assistente' in item:
                    messages.append({"role": "assistant", "content": item['texto_assistente']})
        
        # Adicionar mensagem atual
        messages.append({"role": "user", "content": message})
        
        # Adicionar instruções para formato de resposta
        messages.append({
            "role": "system", 
            "content": """
            Analise a mensagem do usuário e forneça uma resposta no seguinte formato JSON:
            {
                "intencao": "nome_da_intencao",
                "entidades": {
                    "plano": "nome_do_plano_se_mencionado",
                    "metodo_pagamento": "metodo_se_mencionado",
                    "outras_entidades": "valores"
                },
                "resposta": "sua_resposta_natural_ao_usuario",
                "acoes_sugeridas": {
                    "acao": "valor"
                }
            }
            
            Intenções possíveis: saudacao, info_plano, pagamento, metodo_pagamento, historico, cancelamento, desconhecido
            """
        })
        
        # Fazer requisição para a API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        response = requests.post(
            self.api_url,
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code != 200:
            raise Exception(f"Erro na API de LLM: {response.text}")
        
        # Processar resposta
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # Extrair JSON da resposta
        try:
            # Limpar possíveis marcadores de código
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            parsed_result = json.loads(content)
            
            # Garantir formato consistente
            return {
                "intencao": parsed_result.get("intencao", "desconhecido"),
                "entidades": parsed_result.get("entidades", {}),
                "resposta": parsed_result.get("resposta", "Desculpe, não consegui processar sua solicitação."),
                "acoes_sugeridas": parsed_result.get("acoes_sugeridas", {})
            }
        except json.JSONDecodeError:
            # Fallback se não conseguir extrair JSON
            return {
                "intencao": "desconhecido",
                "entidades": {},
                "resposta": content,
                "acoes_sugeridas": {}
            }
    
    def _process_with_fallback(self, message, context):
        """
        Processa mensagem usando sistema de fallback local.
        
        Args:
            message (str): Mensagem do usuário
            context (dict, optional): Contexto da conversa
            
        Returns:
            dict: Resultado do processamento
        """
        # Implementação simplificada para fallback
        message_lower = message.lower()
        
        # Detectar intenção básica
        intencao = "desconhecido"
        entidades = {}
        
        # Saudação
        if any(word in message_lower for word in ["olá", "oi", "bom dia", "boa tarde", "boa noite"]):
            intencao = "saudacao"
            resposta = "Olá! Como posso ajudar você hoje com nossos planos e pagamentos?"
        
        # Informações sobre planos
        elif "plano" in message_lower:
            intencao = "info_plano"
            
            # Detectar plano mencionado
            if "básico" in message_lower or "basico" in message_lower:
                entidades["plano"] = "basico"
                resposta = "O plano Básico custa R$29,99 e inclui 15GB de internet, apps com internet ilimitada e serviços ilimitados de ligação e SMS."
            elif "premium" in message_lower:
                entidades["plano"] = "premium"
                resposta = "O plano Premium custa R$59,90 e inclui 35GB de internet, apps com internet ilimitada e serviços ilimitados de ligação e SMS."
            else:
                resposta = "Temos dois planos disponíveis: Básico (R$29,99) e Premium (R$59,90). Qual deles você gostaria de conhecer melhor?"
        
        # Pagamento
        elif any(word in message_lower for word in ["pagar", "pagamento", "comprar", "contratar"]):
            intencao = "pagamento"
            
            # Detectar método de pagamento
            if "pix" in message_lower:
                entidades["metodo_pagamento"] = "pix"
                resposta = "Para pagar com PIX, vou gerar um código para você. Qual plano você deseja contratar?"
            elif "boleto" in message_lower:
                entidades["metodo_pagamento"] = "boleto"
                resposta = "Para pagar com boleto, vou gerar um código de barras para você. Qual plano você deseja contratar?"
            elif "cartão" in message_lower or "cartao" in message_lower:
                entidades["metodo_pagamento"] = "cartao"
                resposta = "Para pagar com cartão, precisarei de algumas informações. Qual plano você deseja contratar?"
            else:
                resposta = "Como você prefere pagar? Aceitamos PIX, boleto ou cartão de crédito."
        
        # Histórico
        elif "histórico" in message_lower or "transações" in message_lower or "pagamentos" in message_lower:
            intencao = "historico"
            resposta = "Você ainda não possui histórico de transações. Após realizar um pagamento, ele aparecerá aqui."
        
        # Cancelamento
        elif "cancelar" in message_lower or "cancelamento" in message_lower:
            intencao = "cancelamento"
            resposta = "Para cancelar um plano, precisamos verificar alguns detalhes. Por favor, confirme seu e-mail e o plano que deseja cancelar."
        
        # Resposta padrão
        else:
            resposta = "Desculpe, não entendi completamente. Posso ajudar com informações sobre planos, pagamentos ou histórico de transações."
        
        return {
            "intencao": intencao,
            "entidades": entidades,
            "resposta": resposta,
            "acoes_sugeridas": {}
        }
    
    def generate_response(self, prompt, context=None, max_tokens=150):
        """
        Gera uma resposta textual para um prompt específico.
        
        Args:
            prompt (str): Prompt para geração de texto
            context (dict, optional): Contexto adicional
            max_tokens (int, optional): Número máximo de tokens na resposta
            
        Returns:
            str: Texto gerado
        """
        if self.use_fallback or not self.api_key:
            return f"Resposta para: {prompt}"
        
        try:
            # Preparar mensagens para a API
            messages = [
                {"role": "system", "content": self.system_context},
                {"role": "user", "content": prompt}
            ]
            
            # Adicionar contexto se disponível
            if context:
                context_str = json.dumps(context)
                messages.insert(1, {"role": "system", "content": f"Contexto adicional: {context_str}"})
            
            # Fazer requisição para a API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": max_tokens
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code != 200:
                raise Exception(f"Erro na API de LLM: {response.text}")
            
            # Extrair resposta
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            print(f"Erro ao gerar resposta: {e}")
            return f"Não foi possível gerar uma resposta para: {prompt}"
