from django.urls import path
from .views import ProjectInitView
from . import views
urlpatterns = [
    # The Handshake endpoint
    path("init/", ProjectInitView.as_view(), name="project-init"),
    #path("quotes/<uuid:quote_id>/", views.quote_workspace_view, name="quote_workspace"),
    
    
]