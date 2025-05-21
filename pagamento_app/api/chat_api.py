"""
API para o Assistente Virtual de Pagamentos.
Responsável por expor endpoints para interação com o assistente.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from ..services.dialog_manager import DialogManager
from ..services.payment_service import PaymentService

# Inicializar serviços
dialog_manager = DialogManager()
payment_service = PaymentService()

@csrf_exempt
def chatbot_response(request):
    """
    Endpoint para processar mensagens do chatbot.
    
    Args:
        request: Requisição HTTP
        
    Returns:
        JsonResponse: Resposta do assistente
    """
    if request.method == "POST":
        # Obter ID da sessão
        session_id = request.session.session_key or request.session.create()
        
        # Obter dados do usuário da sessão
        user_data = {
            "nome": request.session.get("nome", "Usuário"),
            "email": request.session.get("email")
        }
        
        try:
            # Processar dados da requisição
            data = json.loads(request.body)
            entrada_usuario = data.get("mensagem", "")
            
            # Processar mensagem com o gerenciador de diálogos
            resposta = dialog_manager.processar_mensagem(
                entrada_usuario, 
                session_id, 
                user_data
            )
            
            # Verificar se há ações de pagamento
            if resposta.get("acoes", {}).get("payment_required"):
                # Processar ações de pagamento
                acoes = resposta["acoes"]
                metodo = acoes.get("payment_method")
                plano_id = acoes.get("plan_id")
                
                # Preparar resposta com dados de pagamento
                if metodo == "pix":
                    # Processar pagamento PIX
                    resultado_pix = payment_service.processar_pagamento(
                        "pix", 
                        plano_id, 
                        user_data
                    )
                    
                    if resultado_pix["sucesso"]:
                        # Adicionar dados do PIX à resposta
                        acoes["pix_code"] = resultado_pix["dados"]["codigo_pix"]
                        acoes["qr_code"] = resultado_pix["dados"]["qr_code"]
                        acoes["transaction_id"] = resultado_pix["dados"]["transaction_id"]
                
                elif metodo == "boleto":
                    # Processar pagamento Boleto
                    resultado_boleto = payment_service.processar_pagamento(
                        "boleto", 
                        plano_id, 
                        user_data
                    )
                    
                    if resultado_boleto["sucesso"]:
                        # Adicionar dados do boleto à resposta
                        acoes["barcode"] = resultado_boleto["dados"]["codigo_barras"]
                        acoes["payment_url"] = resultado_boleto["dados"]["url_boleto"]
                        acoes["transaction_id"] = resultado_boleto["dados"]["transaction_id"]
            
            # Retornar resposta formatada
            return JsonResponse({
                "resposta": resposta["texto"],
                "acoes": resposta.get("acoes", {})
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                "resposta": "Erro ao processar a mensagem. Formato JSON inválido.",
                "acoes": {}
            })
        except Exception as e:
            print(f"Erro ao processar a mensagem: {e}")
            return JsonResponse({
                "resposta": f"Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.",
                "acoes": {}
            })
    
    return JsonResponse({
        "resposta": "Use o chat para enviar mensagens.",
        "acoes": {}
    })

@csrf_exempt
def process_payment(request):
    """
    Endpoint para processar pagamentos.
    
    Args:
        request: Requisição HTTP
        
    Returns:
        JsonResponse: Resultado do processamento
    """
    if request.method == "POST":
        try:
            # Processar dados da requisição
            data = json.loads(request.body)
            metodo = data.get("metodo")
            plano_id = data.get("plano_id")
            dados_pagamento = data.get("dados_pagamento", {})
            
            # Obter dados do usuário da sessão
            user_data = {
                "nome": request.session.get("nome", "Usuário"),
                "email": request.session.get("email")
            }
            
            # Validar dados
            if not metodo or not plano_id:
                return JsonResponse({
                    "sucesso": False,
                    "mensagem": "Método de pagamento e plano são obrigatórios",
                    "dados": {}
                })
            
            # Processar pagamento
            resultado = payment_service.processar_pagamento(
                metodo, 
                plano_id, 
                user_data, 
                dados_pagamento
            )
            
            return JsonResponse(resultado)
            
        except json.JSONDecodeError:
            return JsonResponse({
                "sucesso": False,
                "mensagem": "Erro ao processar a requisição. Formato JSON inválido.",
                "dados": {}
            })
        except Exception as e:
            print(f"Erro ao processar pagamento: {e}")
            return JsonResponse({
                "sucesso": False,
                "mensagem": f"Erro ao processar pagamento: {str(e)}",
                "dados": {}
            })
    
    return JsonResponse({
        "sucesso": False,
        "mensagem": "Método não permitido",
        "dados": {}
    })
