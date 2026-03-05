from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db.models import Count
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


def about(request):
    return render(request, "store/about.html")


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


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    error = ""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        error = "Неверный логин или пароль."
    return render(request, "auth/login.html", {"error": error})


@login_required
def dashboard(request):
    orders = Order.objects.all().order_by("-created_at")[:5]
    total_orders = Order.objects.count()
    total_amount_value = sum(o.total_amount for o in Order.objects.all())
    status_counts = Order.objects.values("status").annotate(count=Count("id"))
    status_map = {row["status"]: row["count"] for row in status_counts}
    context = {
        "total_orders": total_orders,
        "total_amount": total_amount_value,
        "status_counts": status_map,
        "latest_orders": orders,
    }
    return render(request, "client_admin/dashboard.html", context)


@login_required
def dashboard_orders(request):
    qs = Order.objects.all().order_by("-created_at")
    search = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    if search:
        qs = qs.filter(customer_name__icontains=search) | qs.filter(
            phone__icontains=search
        )
    if status:
        qs = qs.filter(status=status)
    return render(
        request,
        "client_admin/orders_list.html",
        {"orders": qs, "search": search, "status_filter": status},
    )


@login_required
def dashboard_order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == "POST":
        if "status" in request.POST:
            new_status = request.POST.get("status")
            if new_status in dict(Order.STATUS_CHOICES):
                order.status = new_status
                order.save()
        elif "delete" in request.POST:
            order.delete()
            return redirect("dashboard_orders")
    return render(
        request,
        "client_admin/order_detail.html",
        {"order": order},
    )


@login_required
def dashboard_products(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            name = request.POST.get("name", "").strip()
            price = request.POST.get("price", "").strip()
            category = request.POST.get("category", "").strip()
            description = request.POST.get("description", "").strip()
            if name and price:
                sneaker = Sneaker.objects.create(
                    name=name,
                    price=price,
                    category=category,
                    description=description,
                )
                image = request.FILES.get("image")
                if image:
                    sneaker.main_image = image
                    sneaker.save()
        elif action == "update":
            sneaker_id = request.POST.get("sneaker_id")
            if sneaker_id:
                sneaker = get_object_or_404(Sneaker, pk=sneaker_id)
                sneaker.name = request.POST.get("name", sneaker.name).strip()
                price = request.POST.get("price")
                if price:
                    sneaker.price = price
                sneaker.category = request.POST.get(
                    "category", sneaker.category
                ).strip()
                sneaker.description = request.POST.get(
                    "description", sneaker.description
                ).strip()
                image = request.FILES.get("image")
                if image:
                    sneaker.main_image = image
                sneaker.save()
        elif action == "delete":
            sneaker_id = request.POST.get("sneaker_id")
            if sneaker_id:
                Sneaker.objects.filter(pk=sneaker_id).delete()
        return redirect("dashboard_products")

    sneakers = Sneaker.objects.all()
    return render(
        request,
        "client_admin/products.html",
        {"sneakers": sneakers},
    )

