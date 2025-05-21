"""
Gerenciador de diálogos para o Assistente Virtual de Pagamentos.
Responsável por manter o contexto da conversa e gerar respostas apropriadas.
"""

import json
from datetime import datetime
from ..utils.nlp_processor import NLPProcessor
from ..data import planos

class DialogManager:
    """
    Gerenciador de diálogos que mantém o estado da conversa
    e determina as próximas ações com base nas intenções do usuário.
    """
    
    def __init__(self):
        """Inicializa o gerenciador de diálogos."""
        self.nlp_processor = NLPProcessor()
        # Dicionário para armazenar contexto das sessões
        self.session_contexts = {}
    
    def get_session_context(self, session_id, user_data=None):
        """
        Obtém ou cria o contexto para uma sessão específica.
        
        Args:
            session_id (str): ID da sessão
            user_data (dict, optional): Dados do usuário para inicializar o contexto
            
        Returns:
            dict: Contexto da sessão
        """
        if session_id not in self.session_contexts:
            # Inicializar novo contexto
            self.session_contexts[session_id] = {
                "plano_atual": None,
                "nome": user_data.get("nome", "Usuário") if user_data else "Usuário",
                "email": user_data.get("email") if user_data else None,
                "etapa_cartao": 0,
                "dados_cartao": {},
                "historico": []
            }
        
        return self.session_contexts[session_id]
    
    def processar_mensagem(self, texto, session_id, user_data=None):
        """
        Processa uma mensagem do usuário e gera uma resposta apropriada.
        
        Args:
            texto (str): Texto da mensagem do usuário
            session_id (str): ID da sessão
            user_data (dict, optional): Dados do usuário
            
        Returns:
            dict: Resposta contendo texto e ações
        """
        # Obter contexto da sessão
        contexto = self.get_session_context(session_id, user_data)
        
        # Processar a mensagem com o NLP
        resultado = self.nlp_processor.processar_mensagem(texto, contexto)
        
        # Extrair informações do resultado
        intencao = resultado["intencao"]
        plano = resultado["plano"]
        tipo_informacao = resultado["tipo_informacao"]
        
        # Atualizar contexto com novas informações
        if plano:
            contexto["plano_atual"] = plano
        
        # Registrar interação no histórico
        contexto["historico"].append({
            "timestamp": datetime.now().isoformat(),
            "texto": texto,
            "intencao": intencao,
            "plano": plano,
            "tipo_informacao": tipo_informacao
        })
        
        # Gerar resposta com base na intenção e contexto
        resposta = self.gerar_resposta(intencao, plano, tipo_informacao, contexto)
        
        return resposta
    
    def gerar_resposta(self, intencao, plano, tipo_informacao, contexto):
        """
        Gera uma resposta com base na intenção, plano e tipo de informação.
        
        Args:
            intencao (str): Intenção identificada
            plano (str): Plano identificado
            tipo_informacao (str): Tipo de informação solicitada
            contexto (dict): Contexto da conversa
            
        Returns:
            dict: Resposta contendo texto e ações
        """
        nome = contexto.get("nome", "Usuário")
        plano_atual = plano or contexto.get("plano_atual")
        
        # Inicializar resposta
        resposta = {
            "texto": "",
            "acoes": {}
        }
        
        # Verificar se é uma continuação do fluxo de pagamento com cartão
        if contexto.get("etapa_cartao", 0) > 0:
            resposta["texto"] = self.fluxo_pagamento_cartao(contexto, contexto.get("entrada_atual", ""))
            return resposta
        
        # Gerar resposta com base na intenção
        if intencao == "saudacao":
            resposta["texto"] = f"Olá, {nome}! Como posso ajudar você hoje? Posso fornecer informações sobre nossos planos ou ajudar com pagamentos."
        
        elif intencao in ["info_plano", "planos_disponiveis"]:
            if tipo_informacao == "planos_disponiveis" or not plano_atual:
                resposta["texto"] = self.listar_planos_disponiveis(nome)
            else:
                resposta["texto"] = self.obter_info_plano(plano_atual, tipo_informacao, nome)
        
        elif intencao.startswith("metodo_pagamento") or tipo_informacao and tipo_informacao.startswith("prosseguir_pagamento"):
            metodo = None
            if intencao == "metodo_pagamento_pix" or tipo_informacao == "prosseguir_pagamento_pix":
                metodo = "pix"
            elif intencao == "metodo_pagamento_boleto" or tipo_informacao == "prosseguir_pagamento_boleto":
                metodo = "boleto"
            elif intencao == "metodo_pagamento_cartao" or tipo_informacao == "prosseguir_pagamento_cartao":
                metodo = "cartao"
            
            resposta = self.iniciar_fluxo_pagamento(plano_atual, metodo, contexto)
        
        elif intencao == "pagamento":
            if not plano_atual:
                resposta["texto"] = f"{nome}, qual plano você gostaria de contratar? Temos o Básico (R$29,99) e o Premium (R$59,90)."
            else:
                resposta["texto"] = f"{nome}, como você prefere pagar o plano {plano_atual.capitalize()}? Aceitamos PIX, boleto ou cartão de crédito."
        
        elif intencao == "cancelamento":
            resposta["texto"] = f"{nome}, para cancelar um plano ou assinatura, precisamos verificar alguns detalhes. Por favor, confirme seu e-mail e o plano que deseja cancelar."
        
        elif intencao == "historico":
            resposta["texto"] = self.obter_historico_transacoes(contexto)
        
        else:
            # Usar geração de texto para respostas não mapeadas
            entrada_usuario = contexto.get("entrada_atual", "")
            resposta["texto"] = self.nlp_processor.gerar_resposta_texto(contexto, entrada_usuario)
        
        return resposta
    
    def listar_planos_disponiveis(self, nome):
        """
        Lista os planos disponíveis.
        
        Args:
            nome (str): Nome do usuário
            
        Returns:
            str: Texto com a lista de planos
        """
        resposta = f"{nome}, estes são os planos disponíveis:\n\n"
        for nome_plano, detalhes in planos.items():
            descricao = detalhes.get("descrição", "Descrição não disponível.")
            preco = detalhes.get("preço", "Preço não disponível.")
            resposta += f"Plano {nome_plano.capitalize()}:\n  - Preço: {preco}\n  - Descrição: {descricao}\n\n"
        return resposta
    
    def obter_info_plano(self, plano, tipo_informacao, nome):
        """
        Obtém informações específicas sobre um plano.
        
        Args:
            plano (str): Nome do plano
            tipo_informacao (str): Tipo de informação solicitada
            nome (str): Nome do usuário
            
        Returns:
            str: Texto com as informações solicitadas
        """
        if plano not in planos:
            return f"{nome}, por favor, especifique o plano (Básico ou Premium)."
        
        info_plano = planos.get(plano)
        
        if tipo_informacao == "preço":
            return f"{nome}, o plano {plano.capitalize()} custa {info_plano.get('preço')}."
        elif tipo_informacao == "benefícios":
            beneficios = "\n- " + "\n- ".join(info_plano.get("benefícios", []))
            return f"{nome}, o plano {plano.capitalize()} oferece os seguintes benefícios: {beneficios}"
        elif tipo_informacao == "descrição":
            return f"{nome}, {info_plano.get('descrição', 'Descrição não disponível.')}"
        elif tipo_informacao == "pagamento":
            pagamentos = ", ".join(info_plano.get("pagamento", []))
            return f"{nome}, as opções de pagamento para o plano {plano.capitalize()} são: {pagamentos}."
        else:
            # Informações gerais
            preco = info_plano.get("preço")
            descricao = info_plano.get("descrição")
            return f"{nome}, o plano {plano.capitalize()} custa {preco}. {descricao}"
    
    def iniciar_fluxo_pagamento(self, plano, metodo, contexto):
        """
        Inicia o fluxo de pagamento para um plano específico.
        
        Args:
            plano (str): Nome do plano
            metodo (str): Método de pagamento
            contexto (dict): Contexto da conversa
            
        Returns:
            dict: Resposta contendo texto e ações
        """
        nome = contexto.get("nome", "Usuário")
        resposta = {
            "texto": "",
            "acoes": {}
        }
        
        if not plano:
            resposta["texto"] = f"{nome}, qual plano você gostaria de contratar? Temos o Básico (R$29,99) e o Premium (R$59,90)."
            return resposta
        
        if plano not in planos:
            resposta["texto"] = f"{nome}, por favor, escolha entre os planos Básico ou Premium."
            return resposta
        
        if not metodo:
            resposta["texto"] = f"{nome}, como você prefere pagar o plano {plano.capitalize()}? Aceitamos PIX, boleto ou cartão de crédito."
            return resposta
        
        # Configurar ações para processamento de pagamento
        resposta["acoes"] = {
            "payment_required": True,
            "plan_id": plano,
            "payment_method": metodo
        }
        
        # Adicionar instruções específicas por método de pagamento
        if metodo == "pix":
            codigo_pix = "00020101021226880014br.gov.bcb.pix2566qrcodes-pix.gerencianet.com.br/v2/cobv/22571380-6d75-4400-a463-8d502b8054865204000053039865802BR5925ASSISTENTE VIRTUAL DE PAG6009SAO PAULO62070503***6304E2CA"
            resposta["texto"] = f"{nome}, vamos processar seu pagamento do plano {plano.capitalize()} via PIX. Aqui está o código:"
            resposta["acoes"]["pix_code"] = codigo_pix
            resposta["acoes"]["qr_code"] = True
        elif metodo == "boleto":
            codigo_barras = "34191.79001 01043.510047 91020.150008 9 89110000029990"
            resposta["texto"] = f"{nome}, vamos processar seu pagamento do plano {plano.capitalize()} via boleto. Aqui está o código de barras:"
            resposta["acoes"]["barcode"] = codigo_barras
        elif metodo == "cartao":
            resposta["texto"] = f"{nome}, vamos processar seu pagamento do plano {plano.capitalize()} via cartão de crédito."
            contexto["etapa_cartao"] = 1
            resposta["texto"] += " Por favor, insira o número do cartão."
        
        return resposta
    
    def fluxo_pagamento_cartao(self, contexto, resposta_usuario):
        """
        Gerencia o fluxo de pagamento com cartão de crédito.
        
        Args:
            contexto (dict): Contexto da conversa
            resposta_usuario (str): Resposta do usuário
            
        Returns:
            str: Próxima instrução ou confirmação
        """
        etapa = contexto.get("etapa_cartao", 0)
        dados_cartao = contexto.setdefault("dados_cartao", {})
        nome = contexto.get("nome", "Usuário")
        
        if etapa == 0:
            contexto["etapa_cartao"] = 1
            return f"{nome}, por favor, insira o número do cartão."
        elif etapa == 1:
            dados_cartao["numero_cartao"] = resposta_usuario
            contexto["etapa_cartao"] = 2
            return f"{nome}, agora, informe a validade (MM/AA)."
        elif etapa == 2:
            dados_cartao["validade"] = resposta_usuario
            contexto["etapa_cartao"] = 3
            return f"{nome}, insira o CVV do cartão."
        elif etapa == 3:
            dados_cartao["cvv"] = resposta_usuario
            contexto["etapa_cartao"] = 4
            return f"{nome}, informe o nome que está no cartão."
        elif etapa == 4:
            dados_cartao["nome_cartao"] = resposta_usuario
            contexto["etapa_cartao"] = 5
            return f"{nome}, por fim, informe o CPF."
        elif etapa == 5:
            dados_cartao["cpf"] = resposta_usuario
            contexto["etapa_cartao"] = 0  # Resetar o fluxo do cartão
            
            # Registrar pagamento no histórico
            plano_atual = contexto.get("plano_atual", "desconhecido")
            contexto["historico"].append({
                "timestamp": datetime.now().isoformat(),
                "tipo": "pagamento",
                "metodo": "cartao",
                "plano": plano_atual,
                "status": "aprovado"
            })
            
            return f"Pagamento realizado com sucesso, {nome}! Seu plano {plano_atual.capitalize()} foi ativado. Posso ajudar com mais alguma coisa?"
    
    def obter_historico_transacoes(self, contexto):
        """
        Obtém o histórico de transações do usuário.
        
        Args:
            contexto (dict): Contexto da conversa
            
        Returns:
            str: Texto com o histórico de transações
        """
        nome = contexto.get("nome", "Usuário")
        historico = [item for item in contexto.get("historico", []) if item.get("tipo") == "pagamento"]
        
        if not historico:
            return f"{nome}, você ainda não realizou nenhuma transação."
        
        resposta = f"{nome}, aqui está seu histórico de transações:\n\n"
        for i, transacao in enumerate(historico, 1):
            data = datetime.fromisoformat(transacao["timestamp"]).strftime("%d/%m/%Y %H:%M")
            plano = transacao.get("plano", "desconhecido").capitalize()
            metodo = transacao.get("metodo", "desconhecido").upper()
            status = transacao.get("status", "pendente").capitalize()
            
            resposta += f"{i}. {data} - Plano {plano} - {metodo} - {status}\n"
        
        return resposta
