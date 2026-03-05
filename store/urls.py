from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("login/", views.login_view, name="login"),
    path("sneaker/<int:pk>/", views.sneaker_detail, name="sneaker_detail"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:pk>/", views.add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:pk>/", views.remove_from_cart, name="remove_from_cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("admin-simple/", views.admin_simple, name="admin_simple"),
    path("admin-simple/sneaker/<int:pk>/edit/", views.admin_sneaker_edit, name="admin_sneaker_edit"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/orders/", views.dashboard_orders, name="dashboard_orders"),
    path("dashboard/orders/<int:pk>/", views.dashboard_order_detail, name="dashboard_order_detail"),
    path("dashboard/products/", views.dashboard_products, name="dashboard_products"),
]

