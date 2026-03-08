from django.db.utils import OperationalError, ProgrammingError

from .models import Cart, Sneaker


def cart(request):
    if request.user.is_authenticated:
        try:
            user_cart, _ = Cart.objects.get_or_create(user=request.user)
            total_items = sum(item.quantity for item in user_cart.items.select_related("sneaker"))
            total_price = sum(item.subtotal for item in user_cart.items.select_related("sneaker"))
            return {
                "cart_items_count": total_items,
                "cart_total_price": total_price,
            }
        except (OperationalError, ProgrammingError):
            return {"cart_items_count": 0, "cart_total_price": 0}

    cart_data = request.session.get("cart", {})
    total_items = sum(item["quantity"] for item in cart_data.values())
    total_price = 0
    for sneaker_id, data in cart_data.items():
        sneaker = Sneaker.objects.filter(id=sneaker_id).first()
        if sneaker:
            total_price += sneaker.price * data["quantity"]

    return {
        "cart_items_count": total_items,
        "cart_total_price": total_price,
    }
