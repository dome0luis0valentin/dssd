from django.shortcuts import render
from user.models import User

def index(request):
    user_name = request.session.get("user_name")
    return render(request,'home.html',{"user_name": user_name})
