import json
from collections import OrderedDict
from datetime import date
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from shared_data import DOCTORS, DEPTS, get_doctor, doctor_nlp_score
from doctors.models import Appointment

def jb(r):
    try: return json.loads(r.body)
    except: return {}
def ok(**kw): return JsonResponse({'ok':True,**kw})
def err(msg,s=400): return JsonResponse({'ok':False,'error':msg},status=s)

@login_required
def doctors_view(request):
    q = request.GET.get('q','').lower()
    dept_filter = request.GET.get('dept','all')
    docs = [{**d, 'score': doctor_nlp_score(d)} for d in DOCTORS]
    if q:
        docs = [d for d in docs if q in d['name'].lower() or q in d['spec'].lower() or q in d['dept'].lower()]
    if dept_filter != 'all':
        docs = [d for d in docs if d['dept'] == dept_filter]
    # Group by dept, NLP sorted within each dept
    dept_names = sorted(set(d['dept'] for d in docs))
    doctors_by_dept = OrderedDict()
    for dept in dept_names:
        dept_docs = [d for d in docs if d['dept'] == dept]
        dept_docs.sort(key=lambda x: x['score'], reverse=True)
        doctors_by_dept[dept] = dept_docs
    return render(request, 'doctors/doctors.html', {
        'doctors_by_dept': doctors_by_dept,
        'depts': DEPTS,
        'dept_names': dept_names,
        'q': q,
        'dept_filter': dept_filter,
        'total': len(docs),
    })

@login_required
def doctor_detail_view(request,did):
    d = get_doctor(did)
    if not d: return redirect('doctors')
    return render(request,'doctors/doctor_detail.html',{'doctor':{**d,'score':doctor_nlp_score(d)}})

@login_required
def book_appointment_view(request,did):
    d = get_doctor(did)
    if not d: return redirect('doctors')
    if request.method == 'POST':
        appt_date=request.POST.get('appt_date'); ts=request.POST.get('time_slot')
        reason=request.POST.get('reason',''); pn=request.POST.get('patient_name','').strip()
        ph=request.POST.get('patient_phone','')
        if not appt_date or not ts or not pn:
            messages.error(request,'Please fill all required fields.')
        else:
            Appointment.objects.create(user=request.user,dr_id=d['id'],dr_name=d['name'],dept=d['dept'],appt_date=appt_date,time_slot=ts,reason=reason,patient_name=pn,patient_phone=ph,fee=d['fee'],status='Confirmed')
            messages.success(request,f"Appointment with Dr. {d['name']} confirmed! ✅")
            return redirect('dashboard')
    return render(request,'doctors/book_appointment.html',{'doctor':d,'today':date.today().isoformat()})

@login_required
def api_appointments(request):
    if request.method=='GET':
        return ok(data=[{'id':a.id,'dr_id':a.dr_id,'dr_name':a.dr_name,'dept':a.dept,'date':str(a.appt_date),'time':a.time_slot,'status':a.status,'fee':str(a.fee or 0)} for a in Appointment.objects.filter(user=request.user)])
    if request.method=='POST':
        d=jb(request)
        a=Appointment.objects.create(user=request.user,dr_id=int(d.get('dr_id',1)),dr_name=d.get('dr_name',''),dept=d.get('dept',''),appt_date=d.get('appt_date',str(date.today())),time_slot=d.get('time_slot',''),reason=d.get('reason',''),patient_name=d.get('patient_name',request.user.get_full_name()),patient_phone=d.get('patient_phone',''),fee=float(d.get('fee',0)) if d.get('fee') else None)
        return ok(data={'id':a.id,'status':a.status})
    return err('Method not allowed.',405)
