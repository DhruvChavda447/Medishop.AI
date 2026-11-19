import json, time
from datetime import date
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from shared_data import PRODUCTS, PRODUCT_CATEGORIES, get_product, product_nlp_score, discounted

def jb(r):
    try: return json.loads(r.body)
    except: return {}
def ok(**kw): return JsonResponse({'ok':True,**kw})
def err(msg,s=400): return JsonResponse({'ok':False,'error':msg},status=s)

def get_cart(user):
    from shop.models import Cart
    c,_=Cart.objects.get_or_create(user=user); return c

@login_required
def shop_view(request):
    from collections import OrderedDict
    q = request.GET.get("q", "").lower()
    prods = list(PRODUCTS)
    for p in prods:
        p["nlp_score"] = product_nlp_score(p)
        p["final_price"] = int(discounted(p))
    if q:
        prods = [p for p in prods if q in p["name"].lower() or q in p["tags"] or q in p["mfr"].lower()]
    cats = sorted(set(p["cat"] for p in prods))
    products_by_cat = OrderedDict()
    for cat in cats:
        cat_prods = [p for p in prods if p["cat"] == cat]
        cat_prods.sort(key=lambda x: x["nlp_score"], reverse=True)
        products_by_cat[cat] = cat_prods
    return render(request, "shop/shop.html", {
        "products_by_cat": products_by_cat,
        "categories": cats,
        "total_products": len(prods),
        "total_cats": len(cats),
        "q": q,
    })

@login_required
def product_detail_view(request,pid):
    p=get_product(pid)
    if not p: return redirect('shop')
    p['nlp_score']=product_nlp_score(p); p['final_price']=int(discounted(p))
    related=[{**r,'nlp_score':product_nlp_score(r),'final_price':int(discounted(r))} for r in PRODUCTS if r['cat']==p['cat'] and r['id']!=pid]
    related.sort(key=lambda x:x['nlp_score'],reverse=True)
    return render(request,'shop/product_detail.html',{'product':p,'related':related[:4]})

@login_required
def cart_view(request):
    c=get_cart(request.user); items=[]; sub=0
    for it in c.items:
        p=get_product(it['id'])
        if p:
            dp=discounted(p); lt=dp*it['qty']; sub+=lt
            items.append({**p,'qty':it['qty'],'dp':round(dp,0),'line_total':round(lt,0)})
    dlv=0 if sub>=299 else 49; disc=round(sub*0.05,2); total=sub+dlv-disc
    return render(request,'cart/cart.html',{'items':items,'subtotal':sub,'delivery':dlv,'discount':disc,'total':total,'free_remaining':max(0,299-sub)})

@login_required
def checkout_view(request):
    c=get_cart(request.user)
    if not c.items: return redirect('cart')
    items=[]; sub=0
    for it in c.items:
        p=get_product(it['id'])
        if p:
            dp=discounted(p); lt=dp*it['qty']; sub+=lt
            items.append({**p,'qty':it['qty'],'dp':round(dp,0),'line_total':round(lt,0)})
    dlv=0 if sub>=299 else 49; disc=round(sub*0.05,2); total=sub+dlv-disc
    errors=[]
    if request.method=='POST':
        fn=request.POST.get('full_name','').strip(); ph=request.POST.get('phone','').strip()
        ad=request.POST.get('address','').strip(); ct=request.POST.get('city','').strip()
        pn=request.POST.get('pin_code','').strip(); pm=request.POST.get('payment_method','upi')
        if not fn: errors.append('Full name is required.')
        if not ad: errors.append('Address is required.')
        if not ct: errors.append('City is required.')
        if not errors:
            from shop.models import Order
            ref=f"MSP{int(time.time()*1000)}"
            Order.objects.create(user=request.user,order_ref=ref,items=c.items,total=total,address=f"{ad}, {ct} - {pn}",payment_method=pm,status='Confirmed')
            c.items=[]; c.save()
            messages.success(request,f"Order {ref} placed! 🎉")
            return redirect('order_success')
    return render(request,'checkout/checkout.html',{'items':items,'subtotal':sub,'delivery':dlv,'discount':disc,'total':total,'errors':errors,'post':request.POST})

@login_required
def order_success_view(request):
    from shop.models import Order
    o=Order.objects.filter(user=request.user).first()
    return render(request,'checkout/order_success.html',{'order':o})

# ── Cart APIs ──────────────────────────────────────────────────────
@login_required
def api_cart(request):
    c=get_cart(request.user)
    if request.method=='GET': return ok(data=c.items)
    if request.method=='POST':
        d=jb(request); c.items=d.get('items',[]); c.save(); return ok(data=c.items)
    return err('Method not allowed.',405)

@login_required
def api_cart_add(request):
    d=jb(request)
    pid=d.get('product_id') or d.get('id')
    # qty may be sent as string or accidentally as product name — guard it
    raw_qty = d.get('qty', 1)
    try:
        qty = max(1, int(raw_qty))
    except (ValueError, TypeError):
        qty = 1
    if not pid: return err('Product id required.')
    try:
        pid = int(pid)
    except (ValueError, TypeError):
        return err('Invalid product id.')
    p=get_product(pid)
    if not p: return err('Product not found.')
    c=get_cart(request.user)
    ex=next((i for i in c.items if i['id']==pid),None)
    if ex: ex['qty']+=qty
    else: c.items.append({'id':pid,'qty':qty})
    c.save()
    cart_count=sum(i['qty'] for i in c.items)
    return ok(data={'items':c.items,'total_qty':cart_count},cart_count=cart_count)

@login_required
def api_cart_remove(request):
    d=jb(request); pid=d.get('id'); c=get_cart(request.user)
    c.items=[i for i in c.items if i['id']!=pid]; c.save(); return ok(data=c.items)

@login_required
def api_cart_update(request):
    d=jb(request); pid=d.get('id'); qty=int(d.get('qty',1)); c=get_cart(request.user)
    for it in c.items:
        if it['id']==pid: it['qty']=max(1,qty); break
    c.save(); return ok(data=c.items)

@login_required
def api_orders(request):
    from shop.models import Order
    if request.method=='GET':
        return ok(data=[{'id':o.id,'order_ref':o.order_ref,'total':str(o.total),'status':o.status,'date':o.created_at.strftime('%d/%m/%Y')} for o in Order.objects.filter(user=request.user)])
    return err('Method not allowed.',405)
