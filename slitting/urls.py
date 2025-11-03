from django.urls import path
from . import views

app_name = 'slitting'

urlpatterns = [
    path('', views.slitting_home, name='slitting_home'),

    # Calculation endpoints
    path('calculate-roll-mass/', views.calculate_roll_mass, name='calculate_roll_mass'),
    path('calculate-roll-diameter/', views.calculate_roll_diameter, name='calculate_roll_diameter'),
    path('calculate-slitting-time/', views.calculate_slitting_time, name='calculate_slitting_time'),
    path('calculate-production-efficiency/', views.calculate_production_efficiency,
         name='calculate_production_efficiency'),
    path('calculate-production-rate/', views.calculate_production_rate, name='calculate_production_rate'),
    path('calculate-yield/', views.calculate_yield, name='calculate_yield'),
    path('calculate-film-length/', views.calculate_film_length, name='calculate_film_length'),

    # History
    path('history/', views.slitting_history, name='slitting_history'),
]
