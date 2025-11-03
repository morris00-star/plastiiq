from django.urls import path
from . import views
from .views_history import calculation_history, download_calculation_history

urlpatterns = [
    path('', views.home, name='home'),
    path('calculate-density/', views.calculate_density, name='calculate_density'),
    path('reference/', views.material_reference, name='material_reference'),
    path('calculation-reasons/', views.calculation_reasons, name='calculation_reasons'),
    path('material-properties/', views.material_properties, name='material_properties'),

    # History and downloads - CORRECTED URL PATTERN
    path('calculation-history/', calculation_history, name='calculation_history'),
    path('download-history/<str:format_type>/', download_calculation_history, name='download_history'),

    path('delete-calculation/<int:calculation_id>/', views.delete_calculation, name='delete_calculation'),
    path('delete-calculations-bulk/', views.delete_calculations_bulk, name='delete_calculations_bulk'),
    path('export-calculations/', views.export_selected_calculations, name='export_calculations'),
]
