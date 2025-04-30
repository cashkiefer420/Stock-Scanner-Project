from django.shortcuts import render

subscription_configs = {
    # DVSA
    'dvsa-50': {"heading": "Subscribe to DVSA 50% Alerts", "endpoint": "/subscribe-DVSA-50"},
    'dvsa-100': {"heading": "Subscribe to DVSA 100% Alerts", "endpoint": "/subscribe-DVSA-100"},
    'dvsa-150': {"heading": "Subscribe to DVSA 150% Alerts", "endpoint": "/subscribe-DVSA-150"},

    # Market Cap Increase
    'mc-10-in': {"heading": "Market Cap +10%", "endpoint": "/subscribe-mc-10-in"},
    'mc-20-in': {"heading": "Market Cap +20%", "endpoint": "/subscribe-mc-20-in"},
    'mc-30-in': {"heading": "Market Cap +30%", "endpoint": "/subscribe-mc-30-in"},

    # Market Cap Decrease
    'mc-10-de': {"heading": "Market Cap -10%", "endpoint": "/subscribe-mc-10-de"},
    'mc-20-de': {"heading": "Market Cap -20%", "endpoint": "/subscribe-mc-20-de"},
    'mc-30-de': {"heading": "Market Cap -30%", "endpoint": "/subscribe-mc-30-de"},

    # P/E Increase
    'pe-10-in': {"heading": "P/E +10%", "endpoint": "/subscribe-pe-10-in"},
    'pe-20-in': {"heading": "P/E +20%", "endpoint": "/subscribe-pe-20-in"},
    'pe-30-in': {"heading": "P/E +30%", "endpoint": "/subscribe-pe-30-in"},

    # P/E Decrease
    'pe-10-de': {"heading": "P/E -10%", "endpoint": "/subscribe-pe-10-de"},
    'pe-20-de': {"heading": "P/E -20%", "endpoint": "/subscribe-pe-20-de"},
    'pe-30-de': {"heading": "P/E -30%", "endpoint": "/subscribe-pe-30-de"},

    # Price Decrease
    'price-10-de': {"heading": "Price Drop -10%", "endpoint": "/subscribe-price-10-de"},
    'price-15-de': {"heading": "Price Drop -15%", "endpoint": "/subscribe-price-15-de"},
    'price-20-de': {"heading": "Price Drop -20%", "endpoint": "/subscribe-price-20-de"},
}

def subscription_form(request, category):
    config = subscription_configs.get(category)
    if not config:
        return render(request, "404.html", status=404)  # Or raise 404
    return render(request, "subscription_form.html", config)
