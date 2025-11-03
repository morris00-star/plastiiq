from django.urls import path
from . import views

app_name = 'lamination'

urlpatterns = [
    path('', views.lamination_home, name='lamination_home'),

    # Calculation endpoints
    path('calculate-gsm/', views.calculate_gsm, name='calculate_gsm'),
    path('calculate-multilayer-gsm/', views.calculate_multilayer_gsm, name='calculate_multilayer_gsm'),
    path('calculate-weight-breakdown/', views.calculate_weight_breakdown, name='calculate_weight_breakdown'),
    path('calculate-adhesive-components/', views.calculate_adhesive_components, name='calculate_adhesive_components'),
    path('calculate-lamination-time/', views.calculate_lamination_time, name='calculate_lamination_time'),
    path('calculate-production-efficiency/', views.calculate_production_efficiency,
         name='calculate_production_efficiency'),
    path('calculate-yield/', views.calculate_yield, name='calculate_yield'),

    # History
    path('history/', views.lamination_history, name='lamination_history'),
]
