from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeDoneView,
    PasswordChangeView,
)
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from .decorators import customer_required, store_staff_required
from .forms import (
    AddToBasketForm,
    CustomerRegistrationForm,
    ProductForm,
    StaffCustomerSearchForm,
    StaffRegistrationForm,
)
from .models import Basket, BasketItem, Order, OrderItem, Product, User


def home(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("admin:index")
        if request.user.is_store_staff() or request.user.is_staff:
            return redirect("staff_product_list")
        if request.user.is_customer():
            return redirect("customer_product_list")
    return render(request, "store/home.html")


def register_customer(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome! Your customer account is ready.")
            return redirect("home")
    else:
        form = CustomerRegistrationForm()
    return render(request, "store/register_customer.html", {"form": form})


def register_staff(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Staff account created.")
            return redirect("home")
    else:
        form = StaffRegistrationForm()
    return render(request, "store/register_staff.html", {"form": form})


class StoreLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True


class StoreLogoutView(LogoutView):
    next_page = reverse_lazy("home")


class StorePasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("password_change_done")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        return form


class StorePasswordChangeDoneView(LoginRequiredMixin, PasswordChangeDoneView):
    template_name = "registration/password_change_done.html"


def _get_or_create_pending_basket(user):
    basket = Basket.objects.filter(
        customer=user,
        status=Basket.Status.PENDING,
    ).first()
    if basket is None:
        basket = Basket.objects.create(customer=user)
    return basket


@customer_required
def customer_product_list(request):
    products = Product.objects.all()
    return render(
        request,
        "store/customer_product_list.html",
        {"products": products},
    )


@customer_required
def customer_add_to_basket(request):
    if request.method != "POST":
        return redirect("customer_product_list")
    form = AddToBasketForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Could not add item to basket.")
        return redirect("customer_product_list")
    basket = _get_or_create_pending_basket(request.user)
    product = form.cleaned_data["product"]
    quantity = form.cleaned_data["quantity"]
    item, created = BasketItem.objects.get_or_create(
        basket=basket,
        product=product,
        defaults={"quantity": quantity},
    )
    if not created:
        item.quantity += quantity
        item.save()
    messages.success(
        request,
        f"Added {quantity} × {product.name} to your basket.",
    )
    return redirect("customer_basket")


@customer_required
def customer_basket(request):
    pending = Basket.objects.filter(
        customer=request.user,
        status=Basket.Status.PENDING,
    ).first()
    history = Basket.objects.filter(customer=request.user).exclude(
        status=Basket.Status.PENDING,
    )[:20]
    return render(
        request,
        "store/customer_basket.html",
        {"pending_basket": pending, "basket_history": history},
    )


@customer_required
def customer_orders(request):
    orders = Order.objects.filter(customer=request.user).prefetch_related("items")
    return render(
        request,
        "store/customer_orders.html",
        {"orders": orders},
    )


@store_staff_required
def staff_product_list(request):
    products = Product.objects.all()
    return render(request, "store/staff_product_list.html", {"products": products})


@store_staff_required
def staff_product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Product created.")
            return redirect("staff_product_list")
    else:
        form = ProductForm()
    return render(request, "store/staff_product_form.html", {"form": form, "title": "Add product"})


@store_staff_required
def staff_product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated.")
            return redirect("staff_product_list")
    else:
        form = ProductForm(instance=product)
    return render(
        request,
        "store/staff_product_form.html",
        {"form": form, "title": "Update product", "product": product},
    )


@store_staff_required
def staff_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        name = product.name
        product.delete()
        messages.success(request, f'Deleted product "{name}".')
        return redirect("staff_product_list")
    return render(
        request,
        "store/staff_product_confirm_delete.html",
        {"product": product},
    )


@store_staff_required
def staff_basket_list(request):
    baskets = Basket.objects.select_related("customer").prefetch_related("items__product")
    return render(
        request,
        "store/staff_basket_list.html",
        {"baskets": baskets},
    )


@store_staff_required
def staff_basket_detail(request, pk):
    basket = get_object_or_404(
        Basket.objects.select_related("customer").prefetch_related("items__product"),
        pk=pk,
    )
    return render(
        request,
        "store/staff_basket_detail.html",
        {"basket": basket},
    )


@store_staff_required
@transaction.atomic
def staff_basket_approve(request, pk):
    if request.method != "POST":
        return redirect("staff_basket_detail", pk=pk)
    basket = get_object_or_404(
        Basket.objects.select_for_update().prefetch_related("items__product"),
        pk=pk,
    )
    if basket.status != Basket.Status.PENDING:
        messages.warning(request, "Only pending baskets can be approved.")
        return redirect("staff_basket_detail", pk=pk)
    if not basket.items.exists():
        messages.error(request, "Basket is empty.")
        return redirect("staff_basket_detail", pk=pk)
    total = basket.total()
    if total <= 0:
        messages.error(request, "Invalid basket total.")
        return redirect("staff_basket_detail", pk=pk)
    order = Order.objects.create(
        customer=basket.customer,
        basket=basket,
        total=total,
    )
    for item in basket.items.all():
        OrderItem.objects.create(
            order=order,
            product=item.product,
            product_name=item.product.name,
            unit_price=item.product.price,
            quantity=item.quantity,
        )
    basket.status = Basket.Status.APPROVED
    basket.save(update_fields=["status", "updated_at"])
    messages.success(request, f"Basket approved. Order #{order.pk} created.")
    return redirect("staff_basket_detail", pk=pk)


@store_staff_required
def staff_basket_deny(request, pk):
    if request.method != "POST":
        return redirect("staff_basket_detail", pk=pk)
    basket = get_object_or_404(Basket, pk=pk)
    if basket.status != Basket.Status.PENDING:
        messages.warning(request, "Only pending baskets can be denied.")
        return redirect("staff_basket_detail", pk=pk)
    basket.status = Basket.Status.DENIED
    basket.save(update_fields=["status", "updated_at"])
    messages.success(request, "Basket denied.")
    return redirect("staff_basket_detail", pk=pk)


@store_staff_required
def staff_customer_search(request):
    form = StaffCustomerSearchForm(request.GET or None)
    customers = User.objects.filter(role=User.Role.CUSTOMER).order_by("username")
    q = ""
    if form.is_valid():
        q = form.cleaned_data.get("q") or ""
        if q:
            customers = customers.filter(
                Q(username__icontains=q) | Q(email__icontains=q),
            )
    return render(
        request,
        "store/staff_customer_search.html",
        {"form": form, "customers": customers, "q": q},
    )


@store_staff_required
def staff_customer_detail(request, pk):
    customer = get_object_or_404(User, pk=pk, role=User.Role.CUSTOMER)
    orders = Order.objects.filter(customer=customer).prefetch_related("items")
    baskets = Basket.objects.filter(customer=customer).order_by("-created_at")[:25]
    return render(
        request,
        "store/staff_customer_detail.html",
        {
            "customer_user": customer,
            "orders": orders,
            "baskets": baskets,
        },
    )
