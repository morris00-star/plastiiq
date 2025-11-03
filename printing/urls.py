from django.urls import path
from . import views

app_name = 'printing'

urlpatterns = [
    path('', views.printing_home, name='printing_home'),

    # Calculation endpoints
    path('calculate-film-mass-length/', views.calculate_film_mass_length, name='calculate_film_mass_length'),
    path('calculate-ink-mass-needed/', views.calculate_ink_mass_needed, name='calculate_ink_mass_needed'),
    path('calculate-machine-speed-time/', views.calculate_machine_speed_time, name='calculate_machine_speed_time'),
    path('calculate-gsm/', views.calculate_gsm, name='calculate_gsm'),
    path('calculate-ink-mixing/', views.calculate_ink_mixing, name='calculate_ink_mixing'),
    path('calculate-production-time-order/', views.calculate_production_time_order,
         name='calculate_production_time_order'),

    # History
    path('history/', views.printing_history, name='printing_history'),
]