# kadamay_project/context_processors.py

def user_permissions(request):
    """
    Adds custom permission flags to the template context for the current user.
    """
    can_validate_payment = False
    can_create_payment = False
    can_view_all_payments = False
    has_any_payment_access = False  # <--- ADD THIS NEW VARIABLE

    if request.user.is_authenticated:
        # Check specific permissions
        can_validate_payment = request.user.has_perm(
            'payment.can_validate_payment')
        can_create_payment = request.user.has_perm(
            'payment.add_payment')  # Usually 'add_<model_name>' for create
        can_view_all_payments = request.user.has_perm(
            'payment.view_payment')  # Assuming you have a view permission

        # If user is superuser, they have all permissions
        if request.user.is_superuser:
            can_validate_payment = True
            can_create_payment = True
            can_view_all_payments = True
            has_any_payment_access = True  # <--- SET THIS TO TRUE FOR SUPERUSER

        # Determine if the user has ANY access to the payment module summary link
        # This combines superuser, staff, and specific payment permissions
        has_any_payment_access = has_any_payment_access or \
            request.user.is_superuser or \
            request.user.is_staff or \
            can_validate_payment or \
            can_create_payment or \
            can_view_all_payments  # Added view_all_payments for broader access

    return {
        'user_can_validate_payment': can_validate_payment,
        'user_can_create_payment': can_create_payment,
        'user_can_view_all_payments': can_view_all_payments,
        'user_has_any_payment_access': has_any_payment_access,  # <--- ADD THIS TO CONTEXT
    }
