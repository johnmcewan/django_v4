from django.conf import settings


def auth_status(request):
    return {
        'is_authenticated': getattr(request, 'resolved_is_authenticated', False),
        'username': getattr(request, 'resolved_username', ''),
    }

def carto(request):
    return {'CARTO_API_KEY': settings.CARTO_API_KEY}