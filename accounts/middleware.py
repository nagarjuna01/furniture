from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch
from django.http import JsonResponse


class SubscriptionMiddleware:
    """
    Middleware to enforce tenant subscription.
    Redirects browser users to expired page,
    returns 403 for API requests.
    """

    EXEMPT_URL_NAMES = [
        'material-login',
        'subscription_expired',
        'admin:login',
        'admin:logout',
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        # Precompute URLs
        self.exempt_urls = []
        for name in self.EXEMPT_URL_NAMES:
            try:
                self.exempt_urls.append(reverse(name))
            except NoReverseMatch:
                continue

    def __call__(self, request):
        # Allow static and media
        if request.path.startswith(('/static/', '/media/')):
            return self.get_response(request)

        # Allow exempt URLs
        if request.path in self.exempt_urls:
            return self.get_response(request)

        # If user not authenticated → login
        if not request.user.is_authenticated:
            return redirect(reverse('material-login'))

        # Exempt superusers
        if request.user.is_superuser:
            return self.get_response(request)

        # Get tenant
        tenant = getattr(request.user, 'tenant', None)

        # Subscription active?
        if tenant and getattr(tenant, 'subscription_active', False):
            return self.get_response(request)

        # Handle API requests differently
        if request.path.startswith('/api/') or request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'detail': 'Subscription expired.'}, status=403)

        # Browser redirect
        return redirect(reverse('subscription_expired'))
