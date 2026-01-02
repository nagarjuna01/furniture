from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch

class SubscriptionMiddleware:

    EXEMPT_URLS = [
        '/accounts/login/',
        '/accounts/logout/',
        '/accounts/subscription-expired/',
    ]

    EXEMPT_USERS = ['admin', 'superuser']  # add your superuser usernames here

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # Allow static and media
        if request.path.startswith(('/static/', '/media/')):
            return self.get_response(request)

        # Allow exempt URLs
        if request.path in self.EXEMPT_URLS:
            return self.get_response(request)

        # Reverse lookup for login & subscription pages
        try:
            login_url = reverse('material-login')
            expired_url = reverse('subscription_expired')
        except NoReverseMatch:
            return self.get_response(request)

        # If user not logged in → redirect to login
        if not request.user.is_authenticated:
            return redirect(login_url)

        # Exempt privileged users (superusers or usernames in EXEMPT_USERS)
        if request.user.is_superuser or request.user.username in self.EXEMPT_USERS:
            return self.get_response(request)

        # Check subscription
        tenant = getattr(request.user, 'tenant', None)
        if tenant and getattr(tenant, 'subscription_active', True):
            return self.get_response(request)

        # Subscription expired
        return redirect(expired_url)
