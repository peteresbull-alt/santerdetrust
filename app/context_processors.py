from .models import Notification


def notifications_processor(request):
    """
    Add unread notifications count to all templates
    """
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        return {
            'unread_notifications_count': unread_count
        }
    
    return {
        'unread_notifications_count': 0
    }


def currency_processor(request):
    """
    Add the current user's currency symbol to all templates.
    Falls back to '$' for anonymous users.
    """
    if request.user.is_authenticated:
        return {'currency_symbol': request.user.currency_symbol}

    return {'currency_symbol': '$'}

