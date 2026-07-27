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
    path('calculate-anilox-coverage/', views.calculate_anilox_coverage, name='calculate_anilox_coverage'),
    path('calculate-dot-gain-contrast/', views.calculate_dot_gain_contrast, name='calculate_dot_gain_contrast'),
    path('calculate-delta-e/', views.calculate_delta_e, name='calculate_delta_e'),
    path('calculate-registration-repeat/', views.calculate_registration_repeat, name='calculate_registration_repeat'),
    path('calculate-residual-solvent/', views.calculate_residual_solvent_printing, name='calculate_residual_solvent'),
    path('calculate-ink-waste-allowance/', views.calculate_ink_waste_allowance, name='calculate_ink_waste_allowance'),
    path('calculate-max-safe-speed/', views.calculate_max_safe_speed, name='calculate_max_safe_speed'),
    path('calculate-cylinder-coverage/', views.calculate_cylinder_coverage, name='calculate_cylinder_coverage'),
    path('calculate-cylinder-wear-life/', views.calculate_cylinder_wear_life, name='calculate_cylinder_wear_life'),

    # History
    path('history/', views.printing_history, name='printing_history'),
]