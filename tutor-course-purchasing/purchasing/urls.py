from django.urls import path

from . import views, views_api

app_name = "purchasing"

urlpatterns = [
    # Portal views
    path("", views.catalog, name="catalog"),
    path("cart/", views.cart, name="cart"),
    path("cart/add/", views.cart_add, name="cart_add"),
    path("cart/remove/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path("confirmation/", views.confirmation, name="confirmation"),
    path("orders/", views.orders, name="orders"),
    path("orders/subscriptions/<uuid:subscription_id>/cancel/", views.subscription_cancel, name="subscription_cancel"),

    # REST API
    path("api/v1/course/<str:course_id>/price/", views_api.course_price, name="api_course_price"),
    path("api/v1/course/<str:course_id>/access/", views_api.course_access, name="api_course_access"),
    path("api/v1/orders/", views_api.order_list, name="api_order_list"),
    path("api/v1/subscriptions/", views_api.subscription_list, name="api_subscription_list"),
    path("api/v1/subscriptions/<uuid:subscription_id>/cancel/", views_api.subscription_cancel, name="api_subscription_cancel"),
]
