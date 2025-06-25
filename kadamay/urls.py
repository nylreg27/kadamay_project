# kadamay_project/kadamay/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# Import RedirectView para sa redirection.
from django.views.generic import RedirectView


urlpatterns = [
    path('admin/', admin.site.urls),
    # Include URLs from your 'account' app
    path('account/', include('apps.account.urls')),
    # Include URLs from your 'theme' app (if it has any)
    # path('theme/', include('theme.urls')), # Uncomment if you have a theme app with its own urls.py

    # KINI ANG GI-USAB: I-redirect ang root URL ('') ngadto sa /report/dashboard/
    # Ang 'permanent=True' nagpasabot nga permanent HTTP 301 redirect.
    path('', RedirectView.as_view(
        url='/report/dashboard/', permanent=True), name='home'),


    # For django-browser-reload
    path("__reload__/", include("django_browser_reload.urls")),

    # Include other app URLs as needed
    path('individual/', include('apps.individual.urls')),
    path('family/', include('apps.family.urls')),
    path('payment/', include('apps.payment.urls')),
    path('church/', include('apps.church.urls')),
    path('report/', include('apps.report.urls')),  # Importante nga naa gyud ni
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
