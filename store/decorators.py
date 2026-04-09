from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def customer_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not request.user.is_customer():
            messages.error(request, "This page is only for customers.")
            return redirect("home")
        return view_func(request, *args, **kwargs)

    return _wrapped


def store_staff_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not (request.user.is_store_staff() or request.user.is_staff):
            messages.error(request, "This page is only for store staff.")
            return redirect("home")
        return view_func(request, *args, **kwargs)

    return _wrapped
