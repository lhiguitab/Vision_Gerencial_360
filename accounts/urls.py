from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('profile/', views.profile_view, name='profile'),
    path('lider/', views.lider_dashboard_view, name='lider_dashboard'),
    path('administrativo/', views.administrativo_dashboard_view, name='administrativo_dashboard'),
    path('negotiator/<str:cedula>/', views.negotiator_detail_view, name='negotiator_detail'),
]