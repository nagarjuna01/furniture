from django.urls import path
from .views import material_login, material_logout, subscription_expired,brand_list_page

urlpatterns = [
    path("login/", material_login, name="material-login"),
    path("logout/", material_logout, name="logout"),
    path("subscription-expired/", subscription_expired, name="subscription_expired"),
    path("brand/", brand_list_page, name="brand-list-page")
]