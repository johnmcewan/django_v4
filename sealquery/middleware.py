class AsyncUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Access .is_authenticated NOW to force the lazy DB query
        # to fire here, in the synchronous middleware context.
        user = request.user
        is_authenticated = bool(user.is_authenticated)  # evaluates the lazy object
        
        # Store primitive values only — no lazy objects that
        # could defer a DB call into the async view later.
        request.resolved_is_authenticated = is_authenticated
        request.resolved_username = user.username if is_authenticated else ''
        
        response = self.get_response(request)
        return response