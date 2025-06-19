from apps.account.models import UserChurch


def user_church(request):
    if request.user.is_authenticated:
        try:
            if request.user.is_superuser:
                from apps.church.models import Church
                # fallback to first church
                return {'church': Church.objects.first()}
            user_church = UserChurch.objects.filter(user=request.user).first()
            return {'church': user_church.church if user_church else None}
        except:
            return {'church': None}
    return {'church': None}


def user_roles(request):
    """
    Adds user role booleans (is_cashier, is_incharge) to the template context.
    """
    is_cashier = False
    is_incharge = False
    if request.user.is_authenticated:
        is_cashier = getattr(request.user, 'is_cashier', False)
        is_incharge = getattr(request.user, 'is_incharge', False)
    return {
        'is_cashier': is_cashier,
        'is_incharge': is_incharge,
    }