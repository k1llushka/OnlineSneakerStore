from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Sneaker, Order, OrderItem


def _get_cart(session):
    return session.setdefault("cart", {})


def _save_cart(session, cart):
    session["cart"] = cart
    session.modified = True


def home(request):
    sneakers = Sneaker.objects.all()
    return render(request, "store/home.html", {"sneakers": sneakers})


def sneaker_detail(request, pk):
    sneaker = get_object_or_404(Sneaker, pk=pk)
    available_sizes = [s.strip() for s in sneaker.sizes.split(",") if s.strip()]
    return render(
        request,
        "store/sneaker_detail.html",
        {"sneaker": sneaker, "available_sizes": available_sizes},
    )


def cart_view(request):
    cart = _get_cart(request.session)
    items = []
    total = 0
    for sneaker_id, data in cart.items():
        sneaker = Sneaker.objects.filter(id=sneaker_id).first()
        if not sneaker:
            continue
        item_total = sneaker.price * data["quantity"]
        total += item_total
        items.append(
            {
                "sneaker": sneaker,
                "quantity": data["quantity"],
                "size": data.get("size") or "",
                "item_total": item_total,
            }
        )
    return render(request, "store/cart.html", {"items": items, "total": total})


@require_POST
def add_to_cart(request, pk):
    sneaker = get_object_or_404(Sneaker, pk=pk)
    cart = _get_cart(request.session)
    size = request.POST.get("size", "")
    key = str(sneaker.id)
    if key not in cart:
        cart[key] = {"quantity": 0, "size": size}
    cart[key]["quantity"] += 1
    if size:
        cart[key]["size"] = size
    _save_cart(request.session, cart)
    return redirect("cart")


@require_POST
def remove_from_cart(request, pk):
    cart = _get_cart(request.session)
    key = str(pk)
    if key in cart:
        del cart[key]
        _save_cart(request.session, cart)
    return redirect("cart")


def checkout(request):
    cart = _get_cart(request.session)
    if not cart:
        return redirect("home")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()

        if not (name and phone and address):
            return render(
                request,
                "store/checkout.html",
                {"error": "Пожалуйста, заполните все поля."},
            )

        order = Order.objects.create(
            customer_name=name,
            phone=phone,
            address=address,
        )

        for sneaker_id, data in cart.items():
            sneaker = Sneaker.objects.filter(id=sneaker_id).first()
            if not sneaker:
                continue
            OrderItem.objects.create(
                order=order,
                sneaker=sneaker,
                quantity=data["quantity"],
                size=data.get("size") or "",
            )

        request.session["cart"] = {}
        request.session.modified = True

        return render(
            request,
            "store/order_success.html",
            {"order": order},
        )

    return render(request, "store/checkout.html")


def admin_simple(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            name = request.POST.get("name", "").strip()
            price = request.POST.get("price", "").strip()
            description = request.POST.get("description", "").strip()
            sizes = request.POST.get("sizes", "").strip()
            if name and price:
                sneaker = Sneaker.objects.create(
                    name=name,
                    price=price,
                    description=description,
                    sizes=sizes,
                )
                main_image = request.FILES.get("main_image")
                if main_image:
                    sneaker.main_image = main_image
                    sneaker.save()
        elif action == "delete":
            sneaker_id = request.POST.get("sneaker_id")
            if sneaker_id:
                Sneaker.objects.filter(id=sneaker_id).delete()
        return redirect(reverse("admin_simple"))

    sneakers = Sneaker.objects.all()
    return render(request, "store/admin_simple.html", {"sneakers": sneakers})


def admin_sneaker_edit(request, pk):
    sneaker = get_object_or_404(Sneaker, pk=pk)
    if request.method == "POST":
        main_image = request.FILES.get("main_image")
        if main_image:
            sneaker.main_image = main_image
        img1 = request.FILES.get("additional_image_1")
        if img1:
            sneaker.additional_image_1 = img1
        img2 = request.FILES.get("additional_image_2")
        if img2:
            sneaker.additional_image_2 = img2
        sneaker.save()
        return redirect(reverse("admin_simple"))
    return render(request, "store/admin_sneaker_edit.html", {"sneaker": sneaker})

