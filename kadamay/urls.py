# kadamay_project/kadamay/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import TemplateView  # For a simple home page


urlpatterns = [
    path('admin/', admin.site.urls),
    # Include URLs from your 'account' app
    path('account/', include('apps.account.urls')),
    # Include URLs from your 'theme' app (if it has any)
    # path('theme/', include('theme.urls')),

    # Simple home page (you can replace this with a proper view later)
    path('', TemplateView.as_view(
        template_name='./report/dashboard.html'), name='home'),

    # For django-browser-reload
    path("__reload__/", include("django_browser_reload.urls")),

    # Include other app URLs as needed
    path('individual/', include('apps.individual.urls')),
    path('family/', include('apps.family.urls')),
    path('payment/', include('apps.payment.urls')),
    path('church/', include('apps.church.urls')),
    path('report/', include('apps.report.urls')),
    path('chat/', include('apps.chat.urls')),
    path('issues/', include('apps.issues.urls')),
    path('contribution-type/', include('apps.contribution_type.urls')),
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
