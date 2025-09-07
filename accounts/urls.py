from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('profile/', views.profile_view, name='profile'),
    path('lider/', views.lider_dashboard_view, name='lider_dashboard'),
    path('lider/pending-evaluations/', views.pending_evaluations_view, name='pending_evaluations'),
    path('administrativo/', views.administrativo_dashboard_view, name='administrativo_dashboard'),
    path('negotiator/<str:cedula>/', views.negotiator_detail_view, name='negotiator_detail'),
    path('negotiator/<str:cedula>/last-evaluation/', views.last_evaluation_view, name='last_evaluation'),
    path('negotiator/<str:cedula>/start-evaluation/', views.start_evaluation_view, name='start_evaluation'),
    path('negotiator/<str:cedula>/indicators/', views.negotiator_indicators_view, name='negotiator_indicators'),
    path('negotiator/<str:cedula>/indicators/api/', views.negotiator_indicators_api, name='negotiator_indicators_api'),
]