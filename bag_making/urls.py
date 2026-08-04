from django.urls import path
from . import views

app_name = 'bag_making'

urlpatterns = [
    path('list-cutout-geometries/', views.list_cutout_geometries, name='list_cutout_geometries'),
    path('list-bulk-products/', views.list_bulk_products, name='list_bulk_products'),
    path('calculate-bag-capacity/', views.calculate_bag_capacity, name='calculate_bag_capacity'),
    path('calculate-roll-requirement/', views.calculate_roll_requirement, name='calculate_roll_requirement'),
    path('calculate-seal-strength/', views.calculate_seal_strength, name='calculate_seal_strength'),
    path('', views.bag_making_home, name='bag_making_home'),
    path('calculate-pieces-weight/', views.calculate_pieces_weight, name='calculate_pieces_weight'),
    path('calculate-packet-weight/', views.calculate_packet_weight, name='calculate_packet_weight'),
    path('calculate-bundle-weight/', views.calculate_bundle_weight, name='calculate_bundle_weight'),
    path('calculate-production-metrics/', views.calculate_production_metrics, name='calculate_production_metrics'),
    path('calculate-packet-weight-dimensions/', views.calculate_packet_weight_from_dimensions_data, name='calculate_packet_weight_dimensions'),
    path('calculate-bundle-weight-dimensions/', views.calculate_bundle_weight_from_dimensions_data, name='calculate_bundle_weight_dimensions'),
]
