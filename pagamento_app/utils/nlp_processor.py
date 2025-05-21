"""
Módulo de processamento de linguagem natural para o Assistente Virtual de Pagamentos.
Responsável por analisar e extrair intenções e entidades das mensagens dos usuários.
"""

import unicodedata
import spacy
import nltk
from nltk.corpus import stopwords
from transformers import pipeline

# Garantir que os recursos necessários do NLTK estejam disponíveis
nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)

class NLPProcessor:
    """
    Processador de linguagem natural que utiliza spaCy, NLTK e Transformers
    para compreender as intenções do usuário e extrair entidades relevantes.
    """
    
    def __init__(self):
        """Inicializa o processador de linguagem natural com os modelos necessários."""
        # Carregar modelo do spaCy para português
        self.nlp = spacy.load("pt_core_news_lg")
        
        # Configurar stopwords do NLTK
        self.stop_words = set(stopwords.words("portuguese"))
        
        # Carregar modelo de geração de texto
        self.generator = pipeline("text-generation", model="pierreguillou/gpt2-small-portuguese")
        
        # Mapeamento de intenções e palavras-chave
        self.intent_keywords = {
            "saudacao": ["oi", "olá", "bom dia", "boa tarde", "boa noite", "oi", "olá"],
            "info_plano": ["plano", "informação", "detalhes", "benefícios", "preço", "valor", "custa"],
            "pagamento": ["pagar", "pagamento", "comprar", "adquirir", "contratar"],
            "metodo_pagamento": ["pix", "boleto", "cartão", "cartao", "credito", "débito", "debito"],
            "historico": ["histórico", "transações", "pagamentos", "compras"],
            "cancelamento": ["cancelar", "cancelamento", "desistir"]
        }
    
    def normalizar_texto(self, texto):
        """
        Normaliza o texto removendo acentos e convertendo para minúsculas.
        
        Args:
            texto (str): Texto a ser normalizado
            
        Returns:
            str: Texto normalizado
        """
        texto = texto.replace("PIX", "pix")
        texto = unicodedata.normalize('NFKD', texto)
        texto = "".join([c for c in texto if not unicodedata.combining(c)])
        return texto.lower()
    
    def extrair_palavras_chave(self, texto):
        """
        Extrai palavras-chave, plano e tipo de informação do texto do usuário.
        
        Args:
            texto (str): Texto do usuário
            
        Returns:
            tuple: (plano, tipo_informacao, palavras_chave)
        """
        texto_normalizado = self.normalizar_texto(texto)
        tokens = nltk.word_tokenize(texto_normalizado)
        tokens_limpos = [word for word in tokens if word not in self.stop_words]

        doc = self.nlp(" ".join(tokens_limpos))
        palavras_chave = {token.lemma_ for token in doc if token.pos_ in ["NOUN", "VERB", "ADJ"]}

        if 'pix' in tokens_limpos:
            palavras_chave.add('pix')

        plano, tipo_informacao = None, None
        
        # Identificar plano mencionado
        if "basico" in palavras_chave:
            plano = "basico"
        elif "premium" in palavras_chave:
            plano = "premium"
        
        # Identificar tipo de informação solicitada
        if "preco" in palavras_chave or "valor" in palavras_chave:
            tipo_informacao = "preço"
        elif any(kw in palavras_chave for kw in ["beneficio", "vantagem", "oferece", "oferecer"]):
            tipo_informacao = "benefícios"
        elif "descricao" in palavras_chave or "informacao" in palavras_chave:
            tipo_informacao = "descrição"
        elif "pagamento" in palavras_chave or "forma de pagamento" in palavras_chave:
            tipo_informacao = "pagamento"
        elif "pix" in palavras_chave:
            tipo_informacao = "prosseguir_pagamento_pix"
        elif "boleto" in palavras_chave:
            tipo_informacao = "prosseguir_pagamento_boleto"
        elif "cartao" in palavras_chave or "cartão" in palavras_chave:
            tipo_informacao = "prosseguir_pagamento_cartao"
        elif "assinar" in palavras_chave:
            tipo_informacao = "assinatura"
        elif "cancelar" in palavras_chave:
            tipo_informacao = "cancelamento"
        elif any(kw in palavras_chave for kw in ["planos", "disponivel", "existem"]):
            tipo_informacao = "planos_disponiveis"
            
        return plano, tipo_informacao, palavras_chave
    
    def identificar_intencao(self, texto, palavras_chave=None):
        """
        Identifica a intenção principal do usuário com base no texto.
        
        Args:
            texto (str): Texto do usuário
            palavras_chave (set, optional): Conjunto de palavras-chave já extraídas
            
        Returns:
            str: Intenção identificada
        """
        texto_normalizado = self.normalizar_texto(texto)
        
        if palavras_chave is None:
            _, _, palavras_chave = self.extrair_palavras_chave(texto)
        
        # Verificar cada intenção por correspondência de palavras-chave
        for intent, keywords in self.intent_keywords.items():
            if any(keyword in texto_normalizado for keyword in keywords):
                return intent
                
        # Verificar menções específicas a métodos de pagamento
        if "pix" in texto_normalizado:
            return "metodo_pagamento_pix"
        elif "boleto" in texto_normalizado:
            return "metodo_pagamento_boleto"
        elif "cartão" in texto_normalizado or "cartao" in texto_normalizado:
            return "metodo_pagamento_cartao"
            
        # Intenção padrão se nenhuma correspondência for encontrada
        return "desconhecido"
    
    def gerar_resposta_texto(self, contexto, entrada_usuario):
        """
        Gera uma resposta personalizada usando o modelo de linguagem.
        
        Args:
            contexto (dict): Contexto da conversa
            entrada_usuario (str): Texto do usuário
            
        Returns:
            str: Resposta gerada
        """
        nome = contexto.get("nome", "Usuário")
        prompt = f"{nome} perguntou: '{entrada_usuario}'"
        
        # Gerar resposta com o modelo
        resposta_gerada = self.generator(
            prompt, 
            max_length=100,
            num_return_sequences=1,
            temperature=0.7
        )[0]["generated_text"]
        
        # Limpar a resposta para remover o prompt original
        if prompt in resposta_gerada:
            resposta_limpa = resposta_gerada[len(prompt):].strip()
            return resposta_limpa
            
        return resposta_gerada
    
    def processar_mensagem(self, texto, contexto=None):
        """
        Processa uma mensagem do usuário e extrai informações relevantes.
        
        Args:
            texto (str): Texto do usuário
            contexto (dict, optional): Contexto da conversa
            
        Returns:
            dict: Informações extraídas da mensagem
        """
        if contexto is None:
            contexto = {}
            
        # Extrair palavras-chave, plano e tipo de informação
        plano, tipo_informacao, palavras_chave = self.extrair_palavras_chave(texto)
        
        # Identificar intenção
        intencao = self.identificar_intencao(texto, palavras_chave)
        
        # Registrar entrada atual no contexto
        contexto["entrada_atual"] = texto
        
        # Atualizar plano no contexto se identificado
        if plano:
            contexto["plano_atual"] = plano
            
        return {
            "texto": texto,
            "intencao": intencao,
            "plano": plano,
            "tipo_informacao": tipo_informacao,
            "palavras_chave": palavras_chave,
            "contexto": contexto
        }
