from django.shortcuts import redirect
from functools import wraps

def session_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.session.get("user_id"):
            return view_func(request, *args, **kwargs)
        else:
            return redirect("login")  # nombre de tu login url
    return wrapper
