# kadamay/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Commented out for testing:
    path('account/', include(('apps.account.urls', 'account'), namespace='account')),
    path('church/', include(('apps.church.urls', 'church'), namespace='church')),
    path('family/', include(('apps.family.urls', 'family'), namespace='family')),
    path('individual/', include(('apps.individual.urls',
                                 'individual'), namespace='individual')),
    # path('payment/', include(('apps.payment.urls', 'payment'), namespace='payment')),
    path('report/', include(('apps.report.urls', 'report'), namespace='report')),
    path('chat/', include(('apps.chat.urls', 'chat'), namespace='chat')),
    path('issues/', include(('apps.issues.urls', 'issues'), namespace='issues')),
    path('contribution-type/', include(('apps.contribution_type.urls',
         'contribution_type'), namespace='contribution_type')),

    path('', RedirectView.as_view(pattern_name='report:dashboard'), name='home'),

    path("__reload__/", include("django_browser_reload.urls")),

]

# Serve media files (user uploads) and static files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
