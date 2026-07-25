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
    path('calculate-knife-layout/', views.calculate_knife_layout, name='calculate_knife_layout'),
    path('calculate-rolls-from-mass/', views.calculate_rolls_from_mass, name='calculate_rolls_from_mass'),
    path('calculate-tension-taper/', views.calculate_tension_taper, name='calculate_tension_taper'),
    path('calculate-wind-quality/', views.calculate_wind_quality, name='calculate_wind_quality'),
    path('calculate-downtime-breakdown/', views.calculate_downtime_breakdown, name='calculate_downtime_breakdown'),
    path('calculate-waste-allowance/', views.calculate_waste_allowance, name='calculate_waste_allowance'),

    path('core-materials/', views.get_core_materials, name='get_core_materials'),

    # History
    path('history/', views.slitting_history, name='slitting_history'),
]
