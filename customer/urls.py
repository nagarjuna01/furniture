from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientViewSet, LeadViewSet, OpportunityViewSet, SupportTicketViewSet, InteractionViewSet
from . import views

router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'opportunities', OpportunityViewSet, basename='opportunity')
router.register(r'support-tickets', SupportTicketViewSet, basename='supportticket')
router.register(r'interactions', InteractionViewSet, basename='interaction')

urlpatterns = [
    path('v1/', include(router.urls)),
    path('', views.crm_dashboard, name='crm_dashboard'),
    path('leads/', views.leads_page, name='crm_leads'),
    path('opportunities/', views.opportunities_page, name='crm_opportunities'),
    path('supporttickets/', views.support_tickets_page, name='crm_supporttickets'),
    path('customers/', views.customers_page, name='crm_customers'),
]
