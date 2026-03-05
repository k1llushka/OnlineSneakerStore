from django.db.utils import OperationalError, ProgrammingError

from .models import Sneaker, UserProfile


def cart(request):
    cart_data = request.session.get("cart", {})
    total_items = sum(item["quantity"] for item in cart_data.values())
    total_price = 0
    for sneaker_id, data in cart_data.items():
        sneaker = Sneaker.objects.filter(id=sneaker_id).first()
        if sneaker:
            total_price += sneaker.price * data["quantity"]

    user_profile = None
    if request.user.is_authenticated:
        try:
            user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
        except (OperationalError, ProgrammingError):
            user_profile = None

    return {
        "cart_items_count": total_items,
        "cart_total_price": total_price,
        "user_profile": user_profile,
    }
