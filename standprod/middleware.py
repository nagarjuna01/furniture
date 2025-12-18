# from django.shortcuts import redirect
# from django.urls import reverse, NoReverseMatch

# class SubscriptionMiddleware:

#     EXEMPT_USERS = ['superadmin', 'founder']  
#     EXEMPT_URLS = [
#         '/material-login/',
#         '/logout/',
#         '/subscription-expired/',
#     ]

#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):

#         # Allow static and media
#         if request.path.startswith('/static/') or request.path.startswith('/media/'):
#             return self.get_response(request)

#         # Allow exempt URLs
#         if request.path in self.EXEMPT_URLS:
#             return self.get_response(request)

#         # Allow URLs without reverse mapping (safety)
#         try:
#             login_url = reverse('material-login')
#             expired_url = reverse('subscription_expired')
#         except NoReverseMatch:
#             return self.get_response(request)

#         # If not logged in → send to login page
#         if not request.user.is_authenticated:
#             return redirect(login_url)

#         # Exempt privileged users
#         if request.user.username in self.EXEMPT_USERS:
#             return self.get_response(request)

#         # Check subscription
#         tenant = getattr(request.user, 'tenant', None)

#         if tenant and getattr(tenant, 'subscription_active', True):
#             return self.get_response(request)

#         # Subscription expired
#         return redirect(expired_url)
