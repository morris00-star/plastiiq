from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from qc_project import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', include('calculator.urls')),
    path('extrusion/', include('extrusion.urls')),
    path('printing/', include('printing.urls')),
    path('lamination/', include('lamination.urls')),
    path('slitting/', include('slitting.urls')),
    path('bag-making/', include('bag_making.urls')),
    path('sales/', include('sales.urls')),
]

# This serves static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

