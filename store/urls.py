from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("account/", views.account_view, name="account"),
    path("my-orders/", views.my_orders, name="my_orders"),
    path("my-orders/<int:pk>/cancel/", views.cancel_order, name="cancel_order"),
    path("sneaker/<int:pk>/", views.sneaker_detail, name="sneaker_detail"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:pk>/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:pk>/", views.update_cart_item, name="update_cart_item"),
    path("cart/remove/<int:pk>/", views.remove_from_cart, name="remove_from_cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("admin-simple/", views.admin_simple, name="admin_simple"),
    path("admin-simple/sneaker/<int:pk>/edit/", views.admin_sneaker_edit, name="admin_sneaker_edit"),
    path("admin-simple/sneaker/<int:pk>/delete/", views.admin_sneaker_delete, name="admin_sneaker_delete"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/orders/", views.dashboard_orders, name="dashboard_orders"),
    path("dashboard/orders/<int:pk>/", views.dashboard_order_detail, name="dashboard_order_detail"),
    path("dashboard/products/", views.dashboard_products, name="dashboard_products"),
    path("dashboard/users/", views.dashboard_users, name="dashboard_users"),
    path("admin-dashboard/", views.dashboard, name="admin_dashboard"),
    path("admin-dashboard/orders/", views.dashboard_orders, name="admin_dashboard_orders"),
    path("admin-dashboard/users/", views.dashboard_users, name="admin_dashboard_users"),
]

