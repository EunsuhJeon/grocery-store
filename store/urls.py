from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register_customer, name="register_customer"),
    path("register/staff/", views.register_staff, name="register_staff"),
    path("login/", views.StoreLoginView.as_view(), name="login"),
    path("logout/", views.StoreLogoutView.as_view(), name="logout"),
    path(
        "accounts/password-change/",
        views.StorePasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "accounts/password-change/done/",
        views.StorePasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    path("customer/products/", views.customer_product_list, name="customer_product_list"),
    path(
        "customer/basket/add/",
        views.customer_add_to_basket,
        name="customer_add_to_basket",
    ),
    path("customer/basket/", views.customer_basket, name="customer_basket"),
    path("customer/orders/", views.customer_orders, name="customer_orders"),
    path("staff/products/", views.staff_product_list, name="staff_product_list"),
    path("staff/products/new/", views.staff_product_create, name="staff_product_create"),
    path(
        "staff/products/<int:pk>/edit/",
        views.staff_product_update,
        name="staff_product_update",
    ),
    path(
        "staff/products/<int:pk>/delete/",
        views.staff_product_delete,
        name="staff_product_delete",
    ),
    path("staff/baskets/", views.staff_basket_list, name="staff_basket_list"),
    path("staff/baskets/<int:pk>/", views.staff_basket_detail, name="staff_basket_detail"),
    path(
        "staff/baskets/<int:pk>/approve/",
        views.staff_basket_approve,
        name="staff_basket_approve",
    ),
    path(
        "staff/baskets/<int:pk>/deny/",
        views.staff_basket_deny,
        name="staff_basket_deny",
    ),
    path(
        "staff/customers/",
        views.staff_customer_search,
        name="staff_customer_search",
    ),
    path(
        "staff/customers/<int:pk>/",
        views.staff_customer_detail,
        name="staff_customer_detail",
    ),
]
