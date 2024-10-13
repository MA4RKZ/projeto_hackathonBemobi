# pagamento_app/data.py
planos = {
    "basico": {
        "preço": "R$29,99",
        "benefícios": ["15GB de internet", "Apps com internet ilimitada", "Serviços ilimitados: Ligação, SMS"],
        "descrição": "Ideal para quem não usa muitos dados móveis e não requer para uso profissional.",
        "pagamento": ["PIX", "Boleto", "Cartão de Crédito"]
    },
    "premium": {
        "preço": "R$59,90",
        "benefícios": ["35GB de internet", "Apps com internet ilimitada", "Serviços ilimitados: Ligação, SMS"],
        "descrição": "Para quem necessita de dados móveis para uso diário intenso ou profissional.",
        "pagamento": ["PIX", "Boleto", "Cartão de Crédito"]
    }
}
