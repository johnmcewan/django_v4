def auth_status(request):
    return {
        'is_authenticated': getattr(request, 'resolved_is_authenticated', False),
        'username': getattr(request, 'resolved_username', ''),
    }