from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from shared_data import DEPTS

@login_required
def home_view(request):
    return render(request,'home/home.html',{'depts':DEPTS})
