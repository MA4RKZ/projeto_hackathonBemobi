/**
 * Script principal para o Assistente Virtual de Pagamentos
 * Gerencia a interface do chat, processamento de mensagens e integrações de pagamento
 */

// Configuração inicial
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar componentes
    initChat();
    initPaymentMethods();
    initThemeToggle();
    
    // Exibir mensagem de boas-vindas
    setTimeout(() => {
        addBotMessage("Olá! Sou o Assistente Virtual de Pagamentos. Como posso ajudar você hoje?");
    }, 500);
});

// Variáveis globais
let isTyping = false;
let currentPaymentMethod = null;
let transactionInProgress = false;

/**
 * Inicializa a interface de chat
 */
function initChat() {
    const messageForm = document.getElementById('messageForm');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    
    // Manipular envio de mensagem
    messageForm.addEventListener('submit', function(event) {
        event.preventDefault();
        
        const message = messageInput.value.trim();
        if (message) {
            // Adicionar mensagem do usuário
            addUserMessage(message);
            
            // Limpar campo de entrada
            messageInput.value = '';
            
            // Processar mensagem
            processUserMessage(message);
        }
    });
    
    // Habilitar/desabilitar botão de envio com base no conteúdo
    messageInput.addEventListener('input', function() {
        sendButton.disabled = messageInput.value.trim() === '';
    });
    
    // Inicializar com botão desabilitado
    sendButton.disabled = true;
}

/**
 * Inicializa os métodos de pagamento
 */
function initPaymentMethods() {
    const paymentMethods = document.querySelectorAll('.payment-method');
    
    paymentMethods.forEach(method => {
        method.addEventListener('click', function() {
            // Remover classe ativa de todos os métodos
            paymentMethods.forEach(m => m.classList.remove('active'));
            
            // Adicionar classe ativa ao método selecionado
            this.classList.add('active');
            
            // Atualizar método de pagamento atual
            currentPaymentMethod = this.dataset.method;
            
            // Exibir detalhes do método selecionado
            showPaymentDetails(currentPaymentMethod);
        });
    });
}

/**
 * Inicializa o alternador de tema claro/escuro
 */
function initThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-theme');
            
            // Salvar preferência do usuário
            const isDarkTheme = document.body.classList.contains('dark-theme');
            localStorage.setItem('darkTheme', isDarkTheme);
            
            // Atualizar ícone
            updateThemeIcon(isDarkTheme);
        });
        
        // Verificar preferência salva
        const savedTheme = localStorage.getItem('darkTheme');
        if (savedTheme === 'true') {
            document.body.classList.add('dark-theme');
            updateThemeIcon(true);
        }
    }
}

/**
 * Atualiza o ícone do alternador de tema
 * @param {boolean} isDarkTheme - Se o tema escuro está ativo
 */
function updateThemeIcon(isDarkTheme) {
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.innerHTML = isDarkTheme ? 
            '<i class="fas fa-sun"></i>' : 
            '<i class="fas fa-moon"></i>';
    }
}

/**
 * Adiciona uma mensagem do usuário ao chat
 * @param {string} message - Texto da mensagem
 */
function addUserMessage(message) {
    const chatMessages = document.getElementById('chatMessages');
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    const messageHTML = `
        <div class="message message-user">
            <div class="message-content">
                <div class="message-text">${escapeHtml(message)}</div>
                <div class="message-time">${time}</div>
            </div>
        </div>
    `;
    
    chatMessages.insertAdjacentHTML('beforeend', messageHTML);
    scrollToBottom();
}

/**
 * Adiciona uma mensagem do bot ao chat
 * @param {string} message - Texto da mensagem
 * @param {Object} actions - Ações adicionais a serem executadas
 */
function addBotMessage(message, actions = {}) {
    // Remover indicador de digitação
    removeTypingIndicator();
    
    const chatMessages = document.getElementById('chatMessages');
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Processar links e formatação básica
    const processedMessage = processMessageFormatting(message);
    
    const messageHTML = `
        <div class="message message-bot">
            <div class="message-content">
                <div class="message-text">${processedMessage}</div>
                <div class="message-time">${time}</div>
            </div>
        </div>
    `;
    
    chatMessages.insertAdjacentHTML('beforeend', messageHTML);
    
    // Processar ações adicionais
    processActions(actions);
    
    scrollToBottom();
}

/**
 * Processa formatação básica da mensagem (links, negrito, etc.)
 * @param {string} message - Texto da mensagem
 * @returns {string} Mensagem formatada com HTML
 */
function processMessageFormatting(message) {
    // Converter URLs em links clicáveis
    let processed = message.replace(
        /(https?:\/\/[^\s]+)/g, 
        '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
    );
    
    // Converter **texto** em negrito
    processed = processed.replace(
        /\*\*(.*?)\*\*/g,
        '<strong>$1</strong>'
    );
    
    // Converter _texto_ em itálico
    processed = processed.replace(
        /_(.*?)_/g,
        '<em>$1</em>'
    );
    
    // Converter quebras de linha em <br>
    processed = processed.replace(/\n/g, '<br>');
    
    return processed;
}

/**
 * Processa ações adicionais da mensagem
 * @param {Object} actions - Ações a serem executadas
 */
function processActions(actions) {
    if (!actions) return;
    
    // Processar código PIX
    if (actions.pix_code) {
        showPixPayment(actions.pix_code, actions.qr_code);
    }
    
    // Processar código de barras do boleto
    if (actions.barcode) {
        showBoletoPayment(actions.barcode, actions.payment_url);
    }
    
    // Processar pagamento com cartão
    if (actions.payment_method === 'cartao') {
        showCardPaymentForm();
    }
    
    // Armazenar ID da transação
    if (actions.transaction_id) {
        localStorage.setItem('lastTransactionId', actions.transaction_id);
    }
}

/**
 * Exibe o indicador de digitação do bot
 */
function showTypingIndicator() {
    if (isTyping) return;
    
    isTyping = true;
    const chatMessages = document.getElementById('chatMessages');
    
    const indicatorHTML = `
        <div id="typingIndicator" class="typing-indicator">
            <div class="typing-bubble"></div>
            <div class="typing-bubble"></div>
            <div class="typing-bubble"></div>
        </div>
    `;
    
    chatMessages.insertAdjacentHTML('beforeend', indicatorHTML);
    scrollToBottom();
}

/**
 * Remove o indicador de digitação do bot
 */
function removeTypingIndicator() {
    isTyping = false;
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

/**
 * Processa a mensagem do usuário e obtém resposta do assistente
 * @param {string} message - Mensagem do usuário
 */
function processUserMessage(message) {
    // Mostrar indicador de digitação
    showTypingIndicator();
    
    // Enviar mensagem para o backend
    fetch('/api/assistente/resposta/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ mensagem: message })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Erro na comunicação com o servidor');
        }
        return response.json();
    })
    .then(data => {
        // Simular tempo de resposta natural (opcional)
        setTimeout(() => {
            addBotMessage(data.resposta, data.acoes);
        }, 500 + Math.random() * 1000);
    })
    .catch(error => {
        console.error('Erro:', error);
        setTimeout(() => {
            addBotMessage('Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.');
        }, 500);
    });
}

/**
 * Exibe os detalhes do método de pagamento selecionado
 * @param {string} method - Método de pagamento (pix, boleto, cartao)
 */
function showPaymentDetails(method) {
    const paymentDetails = document.getElementById('paymentDetails');
    
    if (!paymentDetails) return;
    
    // Limpar conteúdo anterior
    paymentDetails.innerHTML = '';
    
    // Exibir detalhes com base no método
    switch (method) {
        case 'pix':
            paymentDetails.innerHTML = `
                <h3>Pagamento via PIX</h3>
                <p>Para pagar com PIX, envie uma mensagem informando o plano desejado e solicite o pagamento via PIX.</p>
                <div class="payment-example">
                    <p>Exemplo: "Quero contratar o plano Premium e pagar com PIX"</p>
                </div>
            `;
            break;
            
        case 'boleto':
            paymentDetails.innerHTML = `
                <h3>Pagamento via Boleto</h3>
                <p>Para pagar com boleto, envie uma mensagem informando o plano desejado e solicite o pagamento via boleto.</p>
                <div class="payment-example">
                    <p>Exemplo: "Quero contratar o plano Básico e pagar com boleto"</p>
                </div>
            `;
            break;
            
        case 'cartao':
            paymentDetails.innerHTML = `
                <h3>Pagamento com Cartão de Crédito</h3>
                <p>Para pagar com cartão, envie uma mensagem informando o plano desejado e solicite o pagamento via cartão de crédito.</p>
                <div class="payment-example">
                    <p>Exemplo: "Quero contratar o plano Premium e pagar com cartão de crédito"</p>
                </div>
            `;
            break;
            
        default:
            paymentDetails.innerHTML = `
                <h3>Selecione um método de pagamento</h3>
                <p>Clique em um dos métodos de pagamento acima para ver mais detalhes.</p>
            `;
    }
}

/**
 * Exibe o formulário de pagamento com PIX
 * @param {string} pixCode - Código PIX
 * @param {string} qrCodeData - Dados do QR Code (base64 ou URL)
 */
function showPixPayment(pixCode, qrCodeData) {
    const paymentContainer = document.getElementById('paymentContainer');
    
    if (!paymentContainer) {
        // Criar container se não existir
        const chatContainer = document.querySelector('.chat-container');
        const newContainer = document.createElement('div');
        newContainer.id = 'paymentContainer';
        newContainer.className = 'payment-details';
        chatContainer.parentNode.insertBefore(newContainer, chatContainer.nextSibling);
        paymentContainer = newContainer;
    }
    
    // Determinar se qrCodeData é base64 ou URL
    const qrCodeSrc = qrCodeData.startsWith('data:') || qrCodeData.startsWith('http') 
        ? qrCodeData 
        : `data:image/png;base64,${qrCodeData}`;
    
    paymentContainer.innerHTML = `
        <h3>Pagamento via PIX</h3>
        <div class="payment-qrcode">
            <p>Escaneie o QR Code abaixo com o aplicativo do seu banco:</p>
            <img src="${qrCodeSrc}" alt="QR Code PIX">
        </div>
        <p>Ou copie o código PIX:</p>
        <div class="payment-code">${pixCode}</div>
        <button class="copy-button" onclick="copyToClipboard('${pixCode}')">
            <i class="fas fa-copy"></i> Copiar código
        </button>
        <p class="payment-note">Após o pagamento, o sistema confirmará automaticamente a transação.</p>
        <button class="btn btn-primary" onclick="checkPaymentStatus()">Verificar status do pagamento</button>
    `;
    
    // Rolar para exibir o container de pagamento
    paymentContainer.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Exibe o formulário de pagamento com boleto
 * @param {string} barcode - Código de barras do boleto
 * @param {string} boletoUrl - URL para visualização do boleto
 */
function showBoletoPayment(barcode, boletoUrl) {
    const paymentContainer = document.getElementById('paymentContainer');
    
    if (!paymentContainer) {
        // Criar container se não existir
        const chatContainer = document.querySelector('.chat-container');
        const newContainer = document.createElement('div');
        newContainer.id = 'paymentContainer';
        newContainer.className = 'payment-details';
        chatContainer.parentNode.insertBefore(newContainer, chatContainer.nextSibling);
        paymentContainer = newContainer;
    }
    
    paymentContainer.innerHTML = `
        <h3>Pagamento via Boleto</h3>
        <p>Utilize o código de barras abaixo para pagar em qualquer banco ou casa lotérica:</p>
        <div class="payment-code">${barcode}</div>
        <button class="copy-button" onclick="copyToClipboard('${barcode}')">
            <i class="fas fa-copy"></i> Copiar código de barras
        </button>
        <p>Ou acesse o boleto completo:</p>
        <a href="${boletoUrl}" target="_blank" class="btn btn-secondary">
            <i class="fas fa-file-invoice-dollar"></i> Visualizar Boleto
        </a>
        <p class="payment-note">O pagamento será confirmado em até 3 dias úteis após o pagamento.</p>
        <button class="btn btn-primary" onclick="checkPaymentStatus()">Verificar status do pagamento</button>
    `;
    
    // Rolar para exibir o container de pagamento
    paymentContainer.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Exibe o formulário de pagamento com cartão de crédito
 */
function showCardPaymentForm() {
    const paymentContainer = document.getElementById('paymentContainer');
    
    if (!paymentContainer) {
        // Criar container se não existir
        const chatContainer = document.querySelector('.chat-container');
        const newContainer = document.createElement('div');
        newContainer.id = 'paymentContainer';
        newContainer.className = 'payment-details';
        chatContainer.parentNode.insertBefore(newContainer, chatContainer.nextSibling);
        paymentContainer = newContainer;
    }
    
    paymentContainer.innerHTML = `
        <h3>Pagamento com Cartão de Crédito</h3>
        <form id="cardPaymentForm">
            <div class="form-group">
                <label for="cardNumber" class="form-label">Número do Cartão</label>
                <input type="text" id="cardNumber" class="form-control" placeholder="0000 0000 0000 0000" required>
            </div>
            <div class="row">
                <div class="col">
                    <div class="form-group">
                        <label for="cardExpiry" class="form-label">Validade</label>
                        <input type="text" id="cardExpiry" class="form-control" placeholder="MM/AA" required>
                    </div>
                </div>
                <div class="col">
                    <div class="form-group">
                        <label for="cardCvv" class="form-label">CVV</label>
                        <input type="text" id="cardCvv" class="form-control" placeholder="123" required>
                    </div>
                </div>
            </div>
            <div class="form-group">
                <label for="cardName" class="form-label">Nome no Cartão</label>
                <input type="text" id="cardName" class="form-control" placeholder="Nome como está no cartão" required>
            </div>
            <div class="form-group">
                <label for="cardCpf" class="form-label">CPF do Titular</label>
                <input type="text" id="cardCpf" class="form-control" placeholder="000.000.000-00" required>
            </div>
            <button type="submit" class="btn btn-primary btn-block">Pagar</button>
        </form>
    `;
    
    // Adicionar máscara aos campos
    const cardNumber = document.getElementById('cardNumber');
    const cardExpiry = document.getElementById('cardExpiry');
    const cardCvv = document.getElementById('cardCvv');
    const cardCpf = document.getElementById('cardCpf');
    
    if (cardNumber) {
        cardNumber.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 16) value = value.slice(0, 16);
            
            // Adicionar espaços a cada 4 dígitos
            value = value.replace(/(\d{4})(?=\d)/g, '$1 ');
            
            e.target.value = value;
        });
    }
    
    if (cardExpiry) {
        cardExpiry.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 4) value = value.slice(0, 4);
            
            // Formato MM/AA
            if (value.length > 2) {
                value = value.slice(0, 2) + '/' + value.slice(2);
            }
            
            e.target.value = value;
        });
    }
    
    if (cardCvv) {
        cardCvv.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 4) value = value.slice(0, 4);
            e.target.value = value;
        });
    }
    
    if (cardCpf) {
        cardCpf.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 11) value = value.slice(0, 11);
            
            // Formato 000.000.000-00
            if (value.length > 9) {
                value = value.slice(0, 3) + '.' + value.slice(3, 6) + '.' + value.slice(6, 9) + '-' + value.slice(9);
            } else if (value.length > 6) {
                value = value.slice(0, 3) + '.' + value.slice(3, 6) + '.' + value.slice(6);
            } else if (value.length > 3) {
                value = value.slice(0, 3) + '.' + value.slice(3);
            }
            
            e.target.value = value;
        });
    }
    
    // Manipular envio do formulário
    const form = document.getElementById('cardPaymentForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Coletar dados do formulário
            const cardData = {
                numero_cartao: cardNumber.value.replace(/\s/g, ''),
                validade: cardExpiry.value,
                cvv: cardCvv.value,
                nome_cartao: cardName.value,
                cpf: cardCpf.value.replace(/\D/g, '')
            };
            
            // Enviar dados para processamento
            processCardPayment(cardData);
        });
    }
    
    // Rolar para exibir o container de pagamento
    paymentContainer.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Processa pagamento com cartão de crédito
 * @param {Object} cardData - Dados do cartão
 */
function processCardPayment(cardData) {
    // Mostrar indicador de carregamento
    const paymentContainer = document.getElementById('paymentContainer');
    paymentContainer.innerHTML = `
        <h3>Processando Pagamento</h3>
        <div class="loading-spinner"></div>
        <p>Por favor, aguarde enquanto processamos seu pagamento...</p>
    `;
    
    // Enviar dados para o backend
    fetch('/api/pagamento/processar/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            metodo: 'cartao',
            plano_id: localStorage.getItem('selectedPlan') || 'basico',
            dados_pagamento: cardData
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Erro no processamento do pagamento');
        }
        return response.json();
    })
    .then(data => {
        if (data.sucesso) {
            // Pagamento aprovado
            paymentContainer.innerHTML = `
                <h3>Pagamento Aprovado</h3>
                <div class="success-icon">
                    <i class="fas fa-check-circle"></i>
                </div>
                <p>Seu pagamento foi processado com sucesso!</p>
                <p>ID da Transação: ${data.dados.transaction_id}</p>
                <button class="btn btn-primary" onclick="closePaymentContainer()">Continuar</button>
            `;
            
            // Adicionar mensagem ao chat
            addBotMessage("Pagamento aprovado com sucesso! Seu plano já está ativo.");
        } else {
            // Pagamento recusado
            paymentContainer.innerHTML = `
                <h3>Pagamento Recusado</h3>
                <div class="error-icon">
                    <i class="fas fa-times-circle"></i>
                </div>
                <p>Não foi possível processar seu pagamento.</p>
                <p>Motivo: ${data.mensagem}</p>
                <button class="btn btn-primary" onclick="showCardPaymentForm()">Tentar Novamente</button>
            `;
            
            // Adicionar mensagem ao chat
            addBotMessage("Desculpe, seu pagamento foi recusado. Por favor, verifique os dados do cartão e tente novamente.");
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        
        // Exibir erro
        paymentContainer.innerHTML = `
            <h3>Erro no Processamento</h3>
            <div class="error-icon">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <p>Ocorreu um erro ao processar seu pagamento.</p>
            <p>Por favor, tente novamente mais tarde.</p>
            <button class="btn btn-primary" onclick="showCardPaymentForm()">Tentar Novamente</button>
        `;
        
        // Adicionar mensagem ao chat
        addBotMessage("Desculpe, ocorreu um erro ao processar seu pagamento. Por favor, tente novamente mais tarde.");
    });
}

/**
 * Verifica o status do pagamento
 */
function checkPaymentStatus() {
    const transactionId = localStorage.getItem('lastTransactionId');
    
    if (!transactionId) {
        showToast('Nenhuma transação em andamento');
        return;
    }
    
    // Mostrar indicador de carregamento
    const paymentContainer = document.getElementById('paymentContainer');
    const originalContent = paymentContainer.innerHTML;
    
    paymentContainer.innerHTML = `
        <h3>Verificando Status</h3>
        <div class="loading-spinner"></div>
        <p>Verificando o status do seu pagamento...</p>
    `;
    
    // Verificar status no backend
    fetch(`/api/pagamento/status/?transaction_id=${transactionId}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Erro ao verificar status');
        }
        return response.json();
    })
    .then(data => {
        if (data.sucesso) {
            // Exibir status
            if (data.dados.status === 'approved' || data.dados.status === 'aprovado') {
                paymentContainer.innerHTML = `
                    <h3>Pagamento Confirmado</h3>
                    <div class="success-icon">
                        <i class="fas fa-check-circle"></i>
                    </div>
                    <p>Seu pagamento foi confirmado com sucesso!</p>
                    <p>Status: Aprovado</p>
                    <button class="btn btn-primary" onclick="closePaymentContainer()">Continuar</button>
                `;
                
                // Adicionar mensagem ao chat
                addBotMessage("Seu pagamento foi confirmado! Seu plano já está ativo.");
            } else {
                // Restaurar conteúdo original com mensagem de status
                paymentContainer.innerHTML = originalContent;
                
                // Adicionar mensagem de status
                const statusMessage = document.createElement('div');
                statusMessage.className = 'payment-status';
                statusMessage.innerHTML = `
                    <p>Status atual: <strong>${data.dados.status}</strong></p>
                    <p>Aguardando confirmação do pagamento...</p>
                `;
                
                // Inserir após o botão de verificação
                const checkButton = paymentContainer.querySelector('.btn-primary');
                if (checkButton) {
                    checkButton.parentNode.insertBefore(statusMessage, checkButton);
                } else {
                    paymentContainer.appendChild(statusMessage);
                }
                
                // Adicionar mensagem ao chat
                addBotMessage(`Seu pagamento está sendo processado. Status atual: ${data.dados.status}`);
            }
        } else {
            // Restaurar conteúdo original com mensagem de erro
            paymentContainer.innerHTML = originalContent;
            showToast(data.mensagem || 'Erro ao verificar status');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        
        // Restaurar conteúdo original
        paymentContainer.innerHTML = originalContent;
        showToast('Erro ao verificar status do pagamento');
    });
}

/**
 * Fecha o container de pagamento
 */
function closePaymentContainer() {
    const paymentContainer = document.getElementById('paymentContainer');
    if (paymentContainer) {
        paymentContainer.remove();
    }
}

/**
 * Copia texto para a área de transferência
 * @param {string} text - Texto a ser copiado
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text)
        .then(() => {
            showToast('Copiado para a área de transferência!');
        })
        .catch(err => {
            console.error('Erro ao copiar:', err);
            showToast('Erro ao copiar texto');
        });
}

/**
 * Exibe uma mensagem toast temporária
 * @param {string} message - Mensagem a ser exibida
 * @param {number} duration - Duração em milissegundos
 */
function showToast(message, duration = 3000) {
    // Remover toast existente
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    // Criar novo toast
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Exibir com animação
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // Ocultar após duração
    setTimeout(() => {
        toast.classList.remove('show');
        
        // Remover do DOM após animação
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, duration);
}

/**
 * Rola o chat para a última mensagem
 */
function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Obtém o token CSRF do cookie
 * @returns {string} Token CSRF
 */
function getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    
    return cookieValue;
}

/**
 * Escapa caracteres HTML para prevenir XSS
 * @param {string} unsafe - Texto não seguro
 * @returns {string} Texto escapado
 */
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
