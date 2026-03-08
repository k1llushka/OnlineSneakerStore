from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Order, OrderItem, Sneaker

User = get_user_model()


def _is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def _get_cart(session):
    return session.setdefault("cart", {})


def _save_cart(session, cart):
    session["cart"] = cart
    session.modified = True


def _get_user_order_ids(session):
    return session.setdefault("user_order_ids", [])


def _save_user_order_ids(session, order_ids):
    session["user_order_ids"] = order_ids
    session.modified = True


def _cart_totals(cart):
    total_items = 0
    total_price = 0
    for sneaker_id, data in cart.items():
        sneaker = Sneaker.objects.filter(id=sneaker_id).first()
        if not sneaker:
            continue
        qty = max(1, int(data.get("quantity", 1)))
        total_items += qty
        total_price += sneaker.price * qty
    return total_items, total_price


def home(request):
    sneakers = Sneaker.objects.all()
    for sneaker in sneakers:
        sneaker.available_sizes = [
            s.strip() for s in (sneaker.sizes or "").split(",") if s.strip()
        ]
    return render(request, "store/home.html", {"sneakers": sneakers})


def about(request):
    return render(request, "store/about.html")


def sneaker_detail(request, pk):
    sneaker = get_object_or_404(Sneaker, pk=pk)
    available_sizes = [s.strip() for s in (sneaker.sizes or "").split(",") if s.strip()]
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
                "unit_price": sneaker.price,
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

    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    if is_ajax:
        total_items, _ = _cart_totals(cart)
        return JsonResponse(
            {
                "ok": True,
                "cart_items_count": total_items,
                "product_name": sneaker.name,
            }
        )
    return redirect("cart")


@require_POST
def remove_from_cart(request, pk):
    cart = _get_cart(request.session)
    key = str(pk)
    if key in cart:
        del cart[key]
        _save_cart(request.session, cart)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        total_items, total_price = _cart_totals(cart)
        return JsonResponse(
            {"ok": True, "cart_items_count": total_items, "cart_total": float(total_price)}
        )
    return redirect("cart")


@require_POST
def update_cart_item(request, pk):
    cart = _get_cart(request.session)
    key = str(pk)
    if key not in cart:
        return JsonResponse({"ok": False, "error": "Р В Р’В Р вЂ™Р’В Р В Р Р‹Р РЋРІР‚С”Р В Р’В Р вЂ™Р’В Р В Р Р‹Р Р†Р вЂљРЎС›Р В Р’В Р вЂ™Р’В Р В Р’В Р Р†Р вЂљР’В Р В Р’В Р вЂ™Р’В Р В РІР‚в„ўР вЂ™Р’В°Р В Р’В Р В Р вЂ№Р В Р’В Р Р†Р вЂљРЎв„ў Р В Р’В Р вЂ™Р’В Р В Р’В Р Р†Р вЂљР’В¦Р В Р’В Р вЂ™Р’В Р В РІР‚в„ўР вЂ™Р’Вµ Р В Р’В Р вЂ™Р’В Р В Р’В Р Р†Р вЂљР’В¦Р В Р’В Р вЂ™Р’В Р В РІР‚в„ўР вЂ™Р’В°Р В Р’В Р вЂ™Р’В Р В Р вЂ Р Р†Р вЂљРЎвЂєР Р†Р вЂљРІР‚СљР В Р’В Р вЂ™Р’В Р В РЎС›Р Р†Р вЂљР’ВР В Р’В Р вЂ™Р’В Р В РІР‚в„ўР вЂ™Р’ВµР В Р’В Р вЂ™Р’В Р В Р’В Р Р†Р вЂљР’В¦ Р В Р’В Р вЂ™Р’В Р В Р’В Р Р†Р вЂљР’В  Р В Р’В Р вЂ™Р’В Р В Р Р‹Р Р†Р вЂљРЎСљР В Р’В Р вЂ™Р’В Р В Р Р‹Р Р†Р вЂљРЎС›Р В Р’В Р В Р вЂ№Р В Р’В Р Р†Р вЂљРЎв„ўР В Р’В Р вЂ™Р’В Р В РІР‚в„ўР вЂ™Р’В·Р В Р’В Р вЂ™Р’В Р В Р Р‹Р Р†Р вЂљР’ВР В Р’В Р вЂ™Р’В Р В Р’В Р Р†Р вЂљР’В¦Р В Р’В Р вЂ™Р’В Р В РІР‚в„ўР вЂ™Р’Вµ."}, status=404)

    try:
        quantity = int(request.POST.get("quantity", "1"))
    except ValueError:
        quantity = 1
    quantity = max(1, quantity)

    cart[key]["quantity"] = quantity
    _save_cart(request.session, cart)

    sneaker = Sneaker.objects.filter(id=pk).first()
    item_total = float(sneaker.price * quantity) if sneaker else 0
    total_items, total_price = _cart_totals(cart)

    return JsonResponse(
        {
            "ok": True,
            "quantity": quantity,
            "item_total": item_total,
            "cart_items_count": total_items,
            "cart_total": float(total_price),
        }
    )


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
                {"error": "Р В Р’В Р вЂ™Р’В Р В Р Р‹Р РЋРЎСџР В Р’В Р вЂ™Р’В Р В Р Р‹Р Р†Р вЂљРЎС›Р В Р’В Р вЂ™Р’В Р В РІР‚в„ўР вЂ™Р’В¶Р В Р’В Р вЂ™Р’В Р В РІР‚в„ўР вЂ™Р’В°Р В Р’В Р вЂ™Р’В Р В РІР‚в„ўР вЂ™Р’В»Р В Р’В Р В Р вЂ№Р В Р Р‹Р Р†Р вЂљРЎС™Р В Р’В Р вЂ™Р’В Р В Р вЂ Р Р†Р вЂљРЎвЂєР Р†Р вЂљРІР‚СљР В Р’В Р В Р вЂ№Р В Р’В Р РЋРІР‚СљР В Р’В Р В Р вЂ№Р В Р вЂ Р В РІР‚С™Р РЋРІвЂћСћР В Р’В Р вЂ™Р’В Р В РІР‚в„ўР вЂ™Р’В°, Р В Р’В Р вЂ™Р’В Р В РІР‚в„ўР вЂ™Р’В·Р В Р’В Р вЂ™Р’В Р В РІР‚в„ўР вЂ™Р’В°Р В Р’В Р вЂ™Р’В Р В Р Р‹Р Р†Р вЂљРІР‚СњР В Р’В Р вЂ™Р’В Р В Р Р‹Р Р†Р вЂљРЎС›Р В Р’В Р вЂ™Р’В Р В РІР‚в„ўР вЂ™Р’В»Р В Р’В Р вЂ™Р’В Р В Р’В Р Р†Р вЂљР’В¦Р В Р’В Р вЂ™Р’В Р В Р Р‹Р Р†Р вЂљР’ВР В Р’В Р В Р вЂ№Р В Р вЂ Р В РІР‚С™Р РЋРІвЂћСћР В Р’В Р вЂ™Р’В Р В РІР‚в„ўР вЂ™Р’Вµ Р В Р’В Р вЂ™Р’В Р В Р’В Р Р†Р вЂљР’В Р В Р’В Р В Р вЂ№Р В Р’В Р РЋРІР‚СљР В Р’В Р вЂ™Р’В Р В РІР‚в„ўР вЂ™Р’Вµ Р В Р’В Р вЂ™Р’В Р В Р Р‹Р Р†Р вЂљРІР‚СњР В Р’В Р вЂ™Р’В Р В Р Р‹Р Р†Р вЂљРЎС›Р В Р’В Р вЂ™Р’В Р В РІР‚в„ўР вЂ™Р’В»Р В Р’В Р В Р вЂ№Р В Р’В Р В Р РЏ."},
            )

        order = Order.objects.create(
            customer_name=name,
            phone=phone,
            address=address,
            user=request.user if request.user.is_authenticated else None,
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

        if request.user.is_authenticated:
            order_ids = _get_user_order_ids(request.session)
            if order.id not in order_ids:
                order_ids.append(order.id)
                _save_user_order_ids(request.session, order_ids)

        request.session["cart"] = {}
        request.session.modified = True

        return render(
            request,
            "store/order_success.html",
            {"order": order},
        )

    return render(request, "store/checkout.html")


@login_required
def my_orders(request):
    # Migrate legacy session-linked orders to user-linked orders.
    legacy_ids = _get_user_order_ids(request.session)
    if legacy_ids:
        Order.objects.filter(id__in=legacy_ids, user__isnull=True).update(user=request.user)

    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items__sneaker")
        .order_by("-created_at")
    )
    now = timezone.now()

    for order in orders:
        age = now - order.created_at
        order.can_cancel = age <= timedelta(minutes=10)
        remaining = timedelta(minutes=10) - age
        order.cancel_minutes_left = max(0, int(remaining.total_seconds() // 60))

        # Simple ETA model for storefront UX.
        if order.status == Order.STATUS_NEW:
            eta = order.created_at + timedelta(days=4)
            order.delivery_hint = f"РћР¶РёРґР°РµРјР°СЏ РґРѕСЃС‚Р°РІРєР°: РґРѕ {eta:%d.%m.%Y}"
        elif order.status == Order.STATUS_PROCESSING:
            eta = order.created_at + timedelta(days=3)
            order.delivery_hint = f"Р—Р°РєР°Р· РІ РѕР±СЂР°Р±РѕС‚РєРµ. РћР¶РёРґР°РµРјР°СЏ РґРѕСЃС‚Р°РІРєР°: РґРѕ {eta:%d.%m.%Y}"
        elif order.status == Order.STATUS_SHIPPED:
            eta = order.created_at + timedelta(days=2)
            order.delivery_hint = f"Р—Р°РєР°Р· РІ РїСѓС‚Рё. РћР¶РёРґР°РµРјР°СЏ РґРѕСЃС‚Р°РІРєР°: РґРѕ {eta:%d.%m.%Y}"
        else:
            order.delivery_hint = "РўРѕРІР°СЂ Р·Р°Р±СЂР°Р»Рё, Р·Р°РєР°Р· Р·Р°РІРµСЂС€РµРЅ."
    return render(request, "store/my_orders.html", {"orders": orders})


@login_required
@require_POST
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)

    if (timezone.now() - order.created_at) > timedelta(minutes=10):
        messages.error(request, "Срок отмены заказа (10 минут) уже истек.")
        return redirect("my_orders")

    order.delete()
    messages.success(request, f"Заказ №{pk} отменен.")
    return redirect("my_orders")


@login_required
def account_view(request):
    error = ""
    success = ""

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        current_password = request.POST.get("current_password", "").strip()
        password = request.POST.get("password", "").strip()
        password_confirm = request.POST.get("password_confirm", "").strip()

        if not username:
            error = "Логин не может быть пустым."
        elif User.objects.filter(username=username).exclude(pk=request.user.pk).exists():
            error = "Пользователь с таким логином уже существует."
        elif email and User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
            error = "Пользователь с таким email уже существует."
        elif password and not current_password:
            error = "Введите текущий пароль для смены пароля."
        elif password and not request.user.check_password(current_password):
            error = "Текущий пароль указан неверно."
        elif password and password != password_confirm:
            error = "Новые пароли не совпадают."
        else:
            request.user.username = username
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.email = email
            if password:
                request.user.set_password(password)
            request.user.save()

            if password:
                update_session_auth_hash(request, request.user)
            success = "Профиль обновлен."

    return render(
        request,
        "store/account.html",
        {"error": error, "success": success},
    )



@user_passes_test(_is_admin, login_url="login")
def admin_simple(request):
    # Legacy route: keep compatibility and reuse products dashboard.
    return dashboard_products(request)


@user_passes_test(_is_admin, login_url="login")
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


@user_passes_test(_is_admin, login_url="login")
@require_POST
def admin_sneaker_delete(request, pk):
    Sneaker.objects.filter(pk=pk).delete()
    return redirect(request.POST.get("next") or reverse("admin_simple"))

def login_view(request):
    if request.user.is_authenticated:
        if _is_admin(request.user):
            return redirect("dashboard")
        return redirect("home")

    error = ""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if _is_admin(user):
                return redirect("dashboard")
            return redirect("home")
        error = "РќРµРІРµСЂРЅС‹Р№ Р»РѕРіРёРЅ РёР»Рё РїР°СЂРѕР»СЊ."
    return render(request, "auth/login.html", {"error": error})


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    error = ""
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        password_confirm = request.POST.get("password_confirm", "").strip()

        if not (name and email and password and password_confirm):
            error = "Р—Р°РїРѕР»РЅРёС‚Рµ РІСЃРµ РїРѕР»СЏ."
        elif password != password_confirm:
            error = "РџР°СЂРѕР»Рё РЅРµ СЃРѕРІРїР°РґР°СЋС‚."
        elif User.objects.filter(username=name).exists():
            error = "РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ СЃ С‚Р°РєРёРј РёРјРµРЅРµРј СѓР¶Рµ СЃСѓС‰РµСЃС‚РІСѓРµС‚."
        elif User.objects.filter(email=email).exists():
            error = "РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ СЃ С‚Р°РєРёРј email СѓР¶Рµ СЃСѓС‰РµСЃС‚РІСѓРµС‚."
        else:
            user = User.objects.create_user(
                username=name,
                email=email,
                password=password,
            )
            login(request, user)
            return redirect("home")

    return render(request, "auth/register.html", {"error": error})
@login_required
def logout_view(request):
    logout(request)
    return redirect("home")


@user_passes_test(_is_admin, login_url="login")
@login_required
def dashboard(request):
    orders = Order.objects.all().order_by("-created_at")[:5]
    latest_purchases = OrderItem.objects.select_related("sneaker", "order").order_by("-id")[:6]
    total_orders = Order.objects.count()
    products_count = Sneaker.objects.count()
    new_orders_count = Order.objects.filter(status=Order.STATUS_NEW).count()
    total_amount_value = sum(o.total_amount for o in Order.objects.all())
    status_counts = Order.objects.values("status").annotate(count=Count("id"))
    status_map = {row["status"]: row["count"] for row in status_counts}
    context = {
        "total_orders": total_orders,
        "products_count": products_count,
        "new_orders_count": new_orders_count,
        "total_amount": total_amount_value,
        "status_counts": status_map,
        "latest_orders": orders,
        "latest_purchases": latest_purchases,
    }
    return render(request, "client_admin/dashboard.html", context)


@user_passes_test(_is_admin, login_url="login")
@login_required
def dashboard_orders(request):
    qs = Order.objects.all().prefetch_related("items__sneaker")
    search = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    sort = request.GET.get("sort", "-created_at").strip()
    allowed_sorts = {
        "-created_at",
        "created_at",
        "customer_name",
        "-customer_name",
        "status",
        "-status",
    }
    if sort not in allowed_sorts:
        sort = "-created_at"

    if search:
        qs = qs.filter(customer_name__icontains=search) | qs.filter(
            phone__icontains=search
        )
    if status:
        qs = qs.filter(status=status)

    qs = qs.order_by(sort)

    return render(
        request,
        "client_admin/orders_list.html",
        {
            "orders": qs,
            "search": search,
            "status_filter": status,
            "sort": sort,
        },
    )


@user_passes_test(_is_admin, login_url="login")
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


@user_passes_test(_is_admin, login_url="login")
@login_required
def dashboard_products(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            name = request.POST.get("name", "").strip()
            price = request.POST.get("price", "").strip()
            category = request.POST.get("category", "").strip()
            description = request.POST.get("description", "").strip()
            sizes = request.POST.get("sizes", "").strip()
            if name and price:
                sneaker = Sneaker.objects.create(
                    name=name,
                    price=price,
                    category=category,
                    description=description,
                    sizes=sizes,
                )
                image = request.FILES.get("image")
                images = request.FILES.getlist("images")
                if image:
                    sneaker.main_image = image
                elif images:
                    if len(images) >= 1:
                        sneaker.main_image = images[0]
                    if len(images) >= 2:
                        sneaker.additional_image_1 = images[1]
                    if len(images) >= 3:
                        sneaker.additional_image_2 = images[2]
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
                sneaker.sizes = request.POST.get("sizes", sneaker.sizes).strip()
                image = request.FILES.get("image")
                images = request.FILES.getlist("images")
                if image:
                    sneaker.main_image = image
                if images:
                    if len(images) >= 1:
                        sneaker.main_image = images[0]
                    if len(images) >= 2:
                        sneaker.additional_image_1 = images[1]
                    if len(images) >= 3:
                        sneaker.additional_image_2 = images[2]
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

@user_passes_test(_is_admin, login_url="login")
@login_required
def dashboard_users(request):
    orders = (
        Order.objects.filter(user__isnull=False)
        .select_related("user")
        .order_by("user_id", "-created_at")
    )
    users_map = {}

    for order in orders:
        if order.user_id in users_map:
            users_map[order.user_id]["orders_count"] += 1
            users_map[order.user_id]["total_amount"] += order.total_amount
            continue

        users_map[order.user_id] = {
            "user": order.user,
            "customer_name": order.customer_name,
            "phone": order.phone,
            "last_order_at": order.created_at,
            "orders_count": 1,
            "total_amount": order.total_amount,
        }

    users = list(users_map.values())
    users.sort(key=lambda row: row["last_order_at"], reverse=True)

    return render(request, "client_admin/users.html", {"users": users})

