from django.urls import path,include 
from .views import material_login, material_logout, subscription_expired,GlobalCommandCenterView,SuperAdminDashboardViewSet
# ajax_login,landing_page
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'super-admin', SuperAdminDashboardViewSet, basename='super-admin')


urlpatterns = [
    path("login/", material_login, name="material-login"),
    # path("ajax/login/", ajax_login, name="ajax_login"),
    path("logout/", material_logout, name="logout"),
    path("subscription-expired/", subscription_expired, name="subscription_expired"),
    # path("",landing_page,name="landing page" ),
    path("api/", include(router.urls)),
    path("api/command-center/", GlobalCommandCenterView.as_view(), name="command-center"),
]