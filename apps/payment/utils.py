# apps/payment/utils.py
# Kining file kay para lang sa mga helper functions, dili URL configurations.

from .models import Payment  # I-assume nato nga naa ang Payment model dinhi


def generate_next_or_number():
    """
    Generates the next available Official Receipt (O.R.) number.
    It finds the highest existing O.R. number and increments it.
    Starts from "2000001" if no payments exist.
    """
    try:
        # Order by or_number descending to get the highest one
        last_payment = Payment.objects.all().order_by('-or_number').first()

        if last_payment and last_payment.or_number:
            # Attempt to convert to integer and increment
            last_or_int = int(last_payment.or_number)
            next_or_number = str(last_or_int + 1)
        else:
            # If no payments exist or or_number is missing, start from base
            next_or_number = "2000001"
    except (ValueError, TypeError):
        # Handle cases where or_number might not be purely numeric or is None
        # Log this error in a real application
        next_or_number = "2000001"  # Fallback to a default starting OR number
    except Exception as e:
        # Catch any other unexpected errors during database query
        # Log this error
        print(f"Error generating OR number: {e}")
        next_or_number = "2000001"  # Fallback

    return next_or_number

# AYAW PAG-BUTANG UG URL PATTERNS DINHI!
# Ang mga URL patterns adto dapat sa apps/payment/urls.py
