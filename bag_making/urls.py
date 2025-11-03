from django.urls import path
from . import views

app_name = 'bag_making'

urlpatterns = [
    path('', views.bag_making_home, name='bag_making_home'),
    path('calculate-pieces-weight/', views.calculate_pieces_weight, name='calculate_pieces_weight'),
    path('calculate-packet-weight/', views.calculate_packet_weight, name='calculate_packet_weight'),
    path('calculate-bundle-weight/', views.calculate_bundle_weight, name='calculate_bundle_weight'),
    path('calculate-production-metrics/', views.calculate_production_metrics, name='calculate_production_metrics'),
    path('history/', views.bag_making_history, name='bag_making_history'),
    path('calculate-packet-weight-dimensions/', views.calculate_packet_weight_from_dimensions, name='calculate_packet_weight_dimensions'),
    path('calculate-bundle-weight-dimensions/', views.calculate_bundle_weight_from_dimensions, name='calculate_bundle_weight_dimensions'),
]
