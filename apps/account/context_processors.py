# C:\Users\nylre\Documents\kadamay_project\apps\account\context_processors.py

from apps.account.models import UserChurch
# Make sure this import is present if you use Church.objects.first()
from apps.church.models import Church


def user_church(request):
    if request.user.is_authenticated:
        try:
            if request.user.is_superuser:
                return {'church': Church.objects.first()}
            user_church_instance = UserChurch.objects.filter(
                user=request.user).first()
            return {'church': user_church_instance.church if user_church_instance else None}
        except Exception:
            return {'church': None}
    return {'church': None}


def user_permissions_context(request):
    """
    Adds user role booleans (is_cashier, is_incharge) and payment access boolean
    to the template context.
    """
    is_cashier = False
    is_incharge = False
    user_has_any_payment_access = False

    if request.user.is_authenticated:
        is_cashier = getattr(request.user, 'is_cashier', False)
        is_incharge = getattr(request.user, 'is_incharge', False)

        if request.user.is_superuser or request.user.is_staff or is_cashier or is_incharge:
            user_has_any_payment_access = True

    return {
        'is_cashier': is_cashier,
        'is_incharge': is_incharge,
        'user_has_any_payment_access': user_has_any_payment_access,
    }
