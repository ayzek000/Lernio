from vercel_app import app

# Точка входа для Vercel
def handler(request, context):
    return app(request, context)
