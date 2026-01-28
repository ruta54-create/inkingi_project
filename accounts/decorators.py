from django.shortcuts import redirect
from django.contrib import messages

def vendor_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Login required.")
            return redirect("login")

        if request.user.user_type != "vendor":
            messages.error(request, "Only vendors can access this page.")
            return redirect("home")

        return view_func(request, *args, **kwargs)
    return wrapper


def customer_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Login required.")
            return redirect("login")

        if request.user.user_type != "customer":
            messages.error(request, "Only customers can access this page.")
            return redirect("home")

        return view_func(request, *args, **kwargs)
    return wrapper
