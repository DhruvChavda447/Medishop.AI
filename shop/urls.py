from django.urls import path
from . import views
urlpatterns = [
    path('shop/',                    views.shop_view,           name='shop'),
    path('shop/product/<int:pid>/',  views.product_detail_view, name='product_detail'),
    path('cart/',                    views.cart_view,           name='cart'),
    path('checkout/',                views.checkout_view,       name='checkout'),
    path('order-success/',           views.order_success_view,  name='order_success'),
    path('api/cart/',                views.api_cart,            name='api_cart'),
    path('api/cart/add/',            views.api_cart_add,        name='api_cart_add'),
    path('api/cart/remove/',         views.api_cart_remove,     name='api_cart_remove'),
    path('api/cart/update/',         views.api_cart_update,     name='api_cart_update'),
    path('api/orders/',              views.api_orders,          name='api_orders'),
]
