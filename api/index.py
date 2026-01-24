def app(request):
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/html; charset=utf-8'
        },
        'body': '<!DOCTYPE html><html><head><title>Test</title></head><body><h1>Markaz to Shopify CSV Converter</h1><p>App is working!</p></body></html>'
    }
