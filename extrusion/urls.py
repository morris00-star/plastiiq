from django.urls import path
from . import views

app_name = 'extrusion'

urlpatterns = [
    path('', views.extrusion_home, name='extrusion_home'),

    # Calculation endpoints
    path('calculate-pieces-weight/', views.calculate_pieces_weight, name='calculate_pieces_weight'),
    path('calculate-thickness/', views.calculate_thickness, name='calculate_thickness'),
    path('calculate-takeup-speed/', views.calculate_takeup_speed, name='calculate_takeup_speed'),
    path('calculate-roll-properties/', views.calculate_roll_properties, name='calculate_roll_properties'),
    path('calculate-roll-radius/', views.calculate_roll_radius, name='calculate_roll_radius'),
    path('calculate-film-length/', views.calculate_film_length, name='calculate_film_length'),
    path('calculate-weight-from-length/', views.calculate_weight_from_length, name='calculate_weight_from_length'),
    path('calculate-production-time/', views.calculate_production_time, name='calculate_production_time'),
    path('calculate-bur-ddr/', views.calculate_bur_ddr, name='calculate_bur_ddr'),
    path('calculate-tensile-strength/', views.calculate_tensile_strength, name='calculate_tensile_strength'),
    path('calculate-elongation/', views.calculate_elongation, name='calculate_elongation'),
    path('calculate-cof/', views.calculate_cof, name='calculate_cof'),
    path('calculate-dart-impact/', views.calculate_dart_impact, name='calculate_dart_impact'),
    path('calculate-gauge-variation/', views.calculate_gauge_variation, name='calculate_gauge_variation'),
    path('calculate-composite-density/', views.calculate_composite_density, name='calculate_composite_density'),
    path('calculate-yield-basis-weight/', views.calculate_yield_basis_weight, name='calculate_yield_basis_weight'),
    path('calculate-roll-radius-from-mass/', views.calculate_roll_radius_from_mass, name='calculate_roll_radius_from_mass'),

    # History
    path('history/', views.extrusion_history, name='extrusion_history'),
]
