from wsgi import application

# Для Vercel Serverless Functions
def handler(request, context):
    return application(request, context)
