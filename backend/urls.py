from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

# API URLs
api_patterns = [
    path('marketplace/', include('marketplace.urls')),
    path('chatbots/', include('chatbots.urls')),
    path('auth/', include('authentication.urls')),  # Cambiado para mejor organización
]

# Documentation URLs
doc_patterns = [
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/', 
         SpectacularSwaggerView.as_view(url_name='schema'), 
         name='swagger-ui'),
    path('schema/redoc/', 
         SpectacularRedocView.as_view(url_name='schema'), 
         name='redoc'),
]

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    path('api/invoicing/', include('invoicing.urls')),
    # API endpoints
    path('api/', include(api_patterns)),
    
    # API documentation
    path('api/', include(doc_patterns)),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)