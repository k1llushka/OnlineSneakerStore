from .models import Sneaker


def cart(request):
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
