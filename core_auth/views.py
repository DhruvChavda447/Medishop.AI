import json
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import UserProfile
from shop.models import Cart, Order
from doctors.models import Appointment

def jb(r):
    try: return json.loads(r.body)
    except: return {}
def ok(**kw): return JsonResponse({'ok':True,**kw})
def err(msg,s=400): return JsonResponse({'ok':False,'error':msg},status=s)
def udict(u): return {'id':u.id,'email':u.email,'full_name':u.get_full_name() or u.username}

def login_view(request):
    if request.user.is_authenticated: return redirect('home')
    error=None
    if request.method=='POST':
        email=request.POST.get('email','').strip().lower()
        pwd=request.POST.get('password','')
        from django.contrib.auth.models import User as DU
        user=authenticate(request,username=email,password=pwd)
        if user is None:
            try:
                u=DU.objects.get(email__iexact=email)
                user=authenticate(request,username=u.username,password=pwd)
            except: pass
        if user and user.is_active:
            login(request,user); Cart.objects.get_or_create(user=user)
            nxt=request.GET.get('next','').strip()
            return redirect(nxt if nxt and nxt.startswith('/') and not nxt.startswith('//') else 'home')
        error='Wrong email or password.'
    return render(request,'auth/login.html',{'error':error})

def signup_view(request):
    if request.user.is_authenticated: return redirect('home')
    errors=[]
    if request.method=='POST':
        fn=request.POST.get('full_name','').strip()
        em=request.POST.get('email','').strip().lower()
        pw=request.POST.get('password','')
        cp=request.POST.get('confirm_password','')
        from django.contrib.auth.models import User as DU
        if not fn: errors.append('Full name is required.')
        if not em: errors.append('Email is required.')
        elif DU.objects.filter(email=em).exists(): errors.append('Email already registered.')
        if len(pw)<6: errors.append('Password must be at least 6 characters.')
        if pw!=cp: errors.append('Passwords do not match.')
        if not errors:
            p=fn.split(' ',1); u=DU.objects.create_user(username=em,email=em,password=pw,first_name=p[0],last_name=p[1] if len(p)>1 else '')
            UserProfile.objects.get_or_create(user=u); Cart.objects.get_or_create(user=u)
            login(request,u); messages.success(request,f"Welcome, {u.first_name}! 🎉")
            return redirect('home')
    return render(request,'auth/signup.html',{'errors':errors,'post':request.POST})

def logout_view(request): logout(request); return redirect('login')

@login_required
def dashboard_view(request):
    orders=Order.objects.filter(user=request.user)
    appointments=Appointment.objects.filter(user=request.user)
    cart,_=Cart.objects.get_or_create(user=request.user)
    return render(request,'dashboard/dashboard.html',{'orders':orders,'appointments':appointments,'cart_qty':cart.total_qty()})

@csrf_exempt
@require_http_methods(['POST'])
def api_login(request):
    d=jb(request); em=d.get('email','').strip().lower(); pw=d.get('password','')
    if not em or not pw: return err('Email and password required.')
    from django.contrib.auth.models import User as DU
    user=authenticate(request,username=em,password=pw)
    if not user:
        try: u=DU.objects.get(email=em); user=authenticate(request,username=u.username,password=pw)
        except: pass
    if not user: return err('Wrong email or password.')
    login(request,user); Cart.objects.get_or_create(user=user)
    return ok(data=udict(user))

@csrf_exempt
@require_http_methods(['POST'])
def api_signup(request):
    d=jb(request); fn=d.get('full_name','').strip(); em=d.get('email','').strip().lower(); pw=d.get('password','')
    if not fn or not em or not pw: return err('All fields required.')
    if len(pw)<6: return err('Password must be at least 6 characters.')
    from django.contrib.auth.models import User as DU
    if DU.objects.filter(email=em).exists(): return err('Email already registered.')
    p=fn.split(' ',1); u=DU.objects.create_user(username=em,email=em,password=pw,first_name=p[0],last_name=p[1] if len(p)>1 else '')
    UserProfile.objects.get_or_create(user=u); Cart.objects.get_or_create(user=u)
    login(request,u); return ok(data=udict(u))

@require_http_methods(['POST'])
def api_logout(request): logout(request); return ok()

def api_me(request):
    if not request.user.is_authenticated: return err('Not authenticated.',401)
    return ok(data=udict(request.user))
