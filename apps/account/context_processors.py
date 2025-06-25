# apps/account/context_processors.py (Corrected Version)

from apps.account.models import UserChurch, Profile # Import Profile to get role
from apps.church.models import Church # Make sure this import is present

def user_church(request):
    """
    Context processor to make the user's assigned church available in templates.
    """
    if request.user.is_authenticated:
        try:
            # Superusers can see the first church or handle differently
            if request.user.is_superuser:
                # You might want to assign a specific default church for superusers,
                # or let them select which church context they are viewing.
                # For now, let's just return the first church found, or None.
                return {'church': Church.objects.first()}
            
            # Access the church assignment through the Profile model if you're using 'church_assignment'
            # OR through UserChurch if that's the primary assignment method
            if hasattr(request.user, 'profile') and request.user.profile.church_assignment:
                return {'church': request.user.profile.church_assignment}
            
            # Fallback to UserChurch link if Profile.church_assignment is not used
            user_church_instance = UserChurch.objects.filter(user=request.user).first()
            return {'church': user_church_instance.church if user_church_instance else None}
        except Exception as e:
            # print(f"Error in user_church context processor: {e}") # For debugging
            return {'church': None}
    return {'church': None}


def user_permissions_context(request):
    """
    Adds user role booleans (is_cashier, is_incharge) and payment access boolean
    to the template context based on Django Groups AND Profile role.
    """
    is_admin = False # Added for clarity
    is_cashier = False
    is_incharge = False
    user_has_any_payment_access = False

    if request.user.is_authenticated:
        # Check via Django Groups
        user_groups = request.user.groups.values_list('name', flat=True)
        is_cashier = 'Cashier' in user_groups
        is_incharge = 'In-Charge' in user_groups
        is_admin = request.user.is_superuser or 'Admin' in user_groups

        # Also check via Profile role field if you use it for primary role assignment
        if hasattr(request.user, 'profile'):
            profile_role = request.user.profile.role
            if profile_role == Profile.CASHIER:
                is_cashier = True
            elif profile_role == Profile.IN_CHARGE:
                is_incharge = True
            elif profile_role == Profile.ADMIN:
                is_admin = True # Set admin too if profile role is admin

        # Define payment access based on roles
        if is_admin or is_cashier or is_incharge:
            user_has_any_payment_access = True

    return {
        'is_admin': is_admin,
        'is_cashier': is_cashier,
        'is_incharge': is_incharge,
        'user_has_any_payment_access': user_has_any_payment_access,
    }

