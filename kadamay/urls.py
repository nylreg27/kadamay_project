# kadamay_project/kadamay/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView


urlpatterns = [
    path('admin/', admin.site.urls),

    # Main App URLs (without 'apps.' prefix, organized for clarity)
    path('account/', include(('apps.account.urls', 'account'), namespace='account')),
    path('church/', include(('apps.church.urls', 'church'), namespace='church')),
    path('family/', include(('apps.family.urls', 'family'), namespace='family')),
    path('individual/', include(('apps.individual.urls',
                                 'individual'), namespace='individual')),
    # !!! KEEP ONLY THIS ONE FOR PAYMENT !!!
    path('payment/', include(('apps.payment.urls', 'payment'), namespace='payment')), 
    
    path('report/', include(('apps.report.urls', 'report'), namespace='report')),
    path('chat/', include(('apps.chat.urls', 'chat'), namespace='chat')),
    path('issues/', include(('apps.issues.urls', 'issues'), namespace='issues')),

    # Django's built-in Authentication URLs (for login/logout/password change)
    path('accounts/', include('django.contrib.auth.urls')),

    # Redirect root URL to dashboard
    path('', RedirectView.as_view(pattern_name='report:dashboard'), name='home'),
    
    # !!! KEEP ONLY THIS ONE FOR DJANGO BROWSER RELOAD !!!
    path("__reload__/", include("django_browser_reload.urls")),


    # Other app urls - THIS SECTION IS LIKELY WHERE YOUR DUPLICATES ARE
    # path("__reload__/", include("django_browser_reload.urls")), # <-- DELETE THIS LINE
    # path('payment/', include('apps.payment.urls')), # <-- DELETE THIS LINE

]

# Serve media files (user uploads) and static files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)

