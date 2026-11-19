import json
from collections import OrderedDict
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from shared_data import DOCTORS, DEPTS, get_doctor, doctor_nlp_score, build_checkup_bill_payload
from doctors.models import Appointment, MedicalBill
from doctors.rag_engine import (
    VECTOR_DB,
    generate_rag_response,
    extract_text_from_uploaded_file,
    parse_medical_bill_text,
    render_checkup_bill_png,
)


def jb(r):
    try:
        return json.loads(r.body)
    except Exception:
        return {}


def ok(**kw):
    return JsonResponse({'ok': True, **kw})


def err(msg, s=400):
    return JsonResponse({'ok': False, 'error': msg}, status=s)


def _user_key(request) -> str:
    if request.user.is_authenticated:
        return f"user_{request.user.id}"
    if not request.session.session_key:
        request.session.save()
    return f"sess_{request.session.session_key or 'anon'}"


def _ensure_bill_record(appointment: Appointment) -> dict:
    """Create or retrieve structured checkup bill for an appointment."""
    doc = get_doctor(appointment.dr_id) or DOCTORS[0]
    payload = build_checkup_bill_payload(doc, appointment)
    raw_lines = [
        f"MEDICARE.AI CLINICAL HOSPITAL — OFFICIAL CHECKUP BILL",
        f"Bill No: {payload['bill_no']}",
        f"Date: {payload['appt_date']} ({payload['time_slot']})",
        f"Doctor: {payload['doctor_name']} ({payload['doctor_spec']})",
        f"Department: {payload['department']}",
        f"Patient Name: {payload['patient_name']}",
        f"Diagnosis: {payload['diagnosis']}",
        f"Clinical Notes: {payload['clinical_notes']}",
        "--- ITEMIZED CHARGES ---",
    ]
    for it in payload['items']:
        raw_lines.append(f"{it['desc']} [{it['code']}]   Rs. {it['amount']:.2f}")
    raw_lines.append(f"Grand Total: Rs. {payload['total']:.2f}")
    raw_lines.append("--- PRESCRIBED MEDICATIONS ---")
    for m in payload['medications']:
        raw_lines.append(f"{m['name']} — {m['dosage']} ({m['duration']})")
    payload['raw_text'] = "\n".join(raw_lines)

    try:
        bill_obj, _ = MedicalBill.objects.update_or_create(
            appointment=appointment,
            defaults={
                'user': appointment.user,
                'bill_no': payload['bill_no'],
                'doctor_name': payload['doctor_name'],
                'department': payload['department'],
                'patient_name': payload['patient_name'],
                'bill_date': payload['appt_date'],
                'diagnosis': payload['diagnosis'],
                'raw_text': payload['raw_text'],
                'structured_json': json.dumps(payload),
                'total_amount': payload['total'],
                'source_type': 'doctor_checkup',
            }
        )
    except Exception:
        pass
    return payload


@login_required
def doctors_view(request):
    q = request.GET.get('q', '').strip().lower()
    dept_filter = request.GET.get('dept', 'all')
    docs = [{**d, 'score': doctor_nlp_score(d)} for d in DOCTORS]
    if q:
        docs = [
            d for d in docs
            if q in d['name'].lower() or q in d['spec'].lower() or q in d['dept'].lower()
            or any(q in tg.lower() for tg in d.get('tags', []))
        ]
    if dept_filter != 'all':
        docs = [d for d in docs if d['dept'] == dept_filter]

    dept_names = sorted(set(d['dept'] for d in DOCTORS))
    doctors_by_dept = OrderedDict()
    for dept in sorted(set(d['dept'] for d in docs)):
        dept_docs = [d for d in docs if d['dept'] == dept]
        dept_docs.sort(key=lambda x: x['score'], reverse=True)
        doctors_by_dept[dept] = dept_docs

    recent_appts = Appointment.objects.filter(user=request.user)[:3]
    return render(request, 'doctors/doctors.html', {
        'doctors_by_dept': doctors_by_dept,
        'depts': DEPTS,
        'dept_names': dept_names,
        'q': q,
        'dept_filter': dept_filter,
        'total': len(docs),
        'recent_appts': recent_appts,
    })


@login_required
def doctor_detail_view(request, did):
    d = get_doctor(did)
    if not d:
        return redirect('doctors')
    return render(request, 'doctors/doctor_detail.html', {
        'doctor': {**d, 'score': doctor_nlp_score(d)}
    })


@login_required
def book_appointment_view(request, did):
    d = get_doctor(did)
    if not d:
        return redirect('doctors')
    if request.method == 'POST':
        appt_date = request.POST.get('appt_date')
        ts = request.POST.get('time_slot')
        reason = request.POST.get('reason', '').strip()
        pn = request.POST.get('patient_name', '').strip()
        ph = request.POST.get('patient_phone', '').strip()
        if not appt_date or not ts or not pn:
            messages.error(request, 'Please complete all required checkup fields.')
        else:
            appt = Appointment.objects.create(
                user=request.user,
                dr_id=d['id'],
                dr_name=d['name'],
                dept=d['dept'],
                appt_date=appt_date,
                time_slot=ts,
                reason=reason or f"Clinical consultation and checkup with Dr. {d['name']}",
                patient_name=pn,
                patient_phone=ph,
                fee=d['fee'],
                status='Completed'
            )
            bill_payload = _ensure_bill_record(appt)
            request.session['active_bill'] = bill_payload
            VECTOR_DB.index_bill_document(bill_payload, user_key=_user_key(request))
            messages.success(
                request,
                f"Checkup with Dr. {d['name']} completed! Your itemized Medical Checkup Bill ({bill_payload['bill_no']}) is ready below."
            )
            return redirect('checkup_bill', appt_id=appt.id)
    return render(request, 'doctors/book_appointment.html', {
        'doctor': {**d, 'score': doctor_nlp_score(d)},
        'today': date.today().isoformat(),
    })


@login_required
def checkup_bill_view(request, appt_id):
    appt = get_object_or_404(Appointment, id=appt_id, user=request.user)
    bill_payload = _ensure_bill_record(appt)
    request.session['active_bill'] = bill_payload
    VECTOR_DB.index_bill_document(bill_payload, user_key=_user_key(request))
    return render(request, 'doctors/bill_detail.html', {
        'appointment': appt,
        'bill': bill_payload,
    })


@login_required
def checkup_bill_image_view(request, appt_id):
    """Download the Doctor Checkup Bill as a crisp PNG image with visible text for OCR bot testing."""
    appt = get_object_or_404(Appointment, id=appt_id, user=request.user)
    bill_payload = _ensure_bill_record(appt)
    png_bytes = render_checkup_bill_png(bill_payload)
    resp = HttpResponse(png_bytes, content_type='image/png')
    resp['Content-Disposition'] = f'attachment; filename="{bill_payload["bill_no"]}_Checkup_Bill.png"'
    return resp


@login_required
def checkup_bill_txt_view(request, appt_id):
    """Download the Doctor Checkup Bill as a structured plain-text file."""
    appt = get_object_or_404(Appointment, id=appt_id, user=request.user)
    bill_payload = _ensure_bill_record(appt)
    resp = HttpResponse(bill_payload['raw_text'], content_type='text/plain; charset=utf-8')
    resp['Content-Disposition'] = f'attachment; filename="{bill_payload["bill_no"]}_Checkup_Bill.txt"'
    return resp


@login_required
def api_appointments(request):
    if request.method == 'GET':
        appts = Appointment.objects.filter(user=request.user)
        return ok(data=[{
            'id': a.id,
            'dr_id': a.dr_id,
            'dr_name': a.dr_name,
            'dept': a.dept,
            'date': str(a.appt_date),
            'time': a.time_slot,
            'status': a.status,
            'fee': str(a.fee or 0),
            'bill_url': f'/doctors/bill/{a.id}/',
        } for a in appts])
    if request.method == 'POST':
        d = jb(request)
        a = Appointment.objects.create(
            user=request.user,
            dr_id=int(d.get('dr_id', 1)),
            dr_name=d.get('dr_name', 'Priya Sharma'),
            dept=d.get('dept', 'Cardiology'),
            appt_date=d.get('appt_date', str(date.today())),
            time_slot=d.get('time_slot', '10:00 AM'),
            reason=d.get('reason', 'Checkup'),
            patient_name=d.get('patient_name', request.user.get_full_name() or request.user.username),
            patient_phone=d.get('patient_phone', ''),
            fee=float(d.get('fee', 800)) if d.get('fee') else 800,
            status='Completed',
        )
        bill_payload = _ensure_bill_record(a)
        return ok(data={'id': a.id, 'status': a.status, 'bill_no': bill_payload['bill_no'], 'bill_url': f'/doctors/bill/{a.id}/'})
    return err('Method not allowed.', 405)


@csrf_exempt
@login_required
def api_rag_chat(request):
    """Main RAG + Vector DB + Text Creator Model + Page Navigation API endpoint for Medi AI Bot."""
    if request.method != 'POST':
        return err('POST required.', 405)
    d = jb(request)
    query = (d.get('query') or d.get('text') or '').strip()
    if not query:
        return err('Query text is required.')
    active_bill = request.session.get('active_bill')
    res = generate_rag_response(query, user_key=_user_key(request), active_bill=active_bill)
    return ok(data=res)


@csrf_exempt
@login_required
def api_rag_upload_bill(request):
    """
    Powerful Bill Text Finder & Vector Indexer Endpoint:
    Accepts any uploaded medical bill file (Image PNG/JPG/WEBP, PDF, or TXT) or pasted bill text,
    extracts visible text, parses structured clinical & financial entities, indexes into Vector DB,
    and returns an immediate RAG summary so the user can chat about the bill!
    """
    if request.method != 'POST':
        return err('POST required.', 405)

    uploaded_file = request.FILES.get('bill_file')
    client_ocr_text = (request.POST.get('ocr_text') or '').strip()
    raw_text_input = (request.POST.get('raw_text') or '').strip()

    if not uploaded_file and not client_ocr_text and not raw_text_input:
        d = jb(request)
        raw_text_input = (d.get('raw_text') or d.get('ocr_text') or '').strip()

    filename = "Pasted_Medical_Bill.txt"
    extraction_method = "Direct Text Parser"
    extracted_text = raw_text_input or client_ocr_text

    if uploaded_file:
        filename = uploaded_file.name
        extracted_text, extraction_method = extract_text_from_uploaded_file(uploaded_file, client_ocr_text=client_ocr_text)

    if not extracted_text or len(extracted_text.strip()) < 8:
        return err(
            "Could not detect readable text in the uploaded file. Please ensure the bill image or PDF has clear visible text."
        )

    parsed_bill = parse_medical_bill_text(extracted_text, filename=filename)
    request.session['active_bill'] = parsed_bill
    uk = _user_key(request)
    VECTOR_DB.index_bill_document(parsed_bill, user_key=uk)

    # Save to MedicalBill table for dashboard tracking
    try:
        MedicalBill.objects.create(
            user=request.user,
            bill_no=parsed_bill['bill_no'],
            doctor_name=parsed_bill['doctor_name'],
            department=parsed_bill['department'],
            patient_name=parsed_bill['patient_name'],
            bill_date=parsed_bill['appt_date'],
            diagnosis=parsed_bill['diagnosis'],
            raw_text=parsed_bill['raw_text'][:4000],
            structured_json=json.dumps(parsed_bill),
            total_amount=parsed_bill['total'] or 0,
            source_type='uploaded_bill',
        )
    except Exception:
        pass

    summary_res = generate_rag_response(
        "Provide a complete summary of my uploaded medical bill including doctor, diagnosis, itemized charges, total amount, and prescribed medicines.",
        user_key=uk,
        active_bill=parsed_bill
    )

    return ok(data={
        'filename': filename,
        'extraction_method': extraction_method,
        'extracted_char_count': len(extracted_text),
        'extracted_text_preview': extracted_text[:600],
        'bill': parsed_bill,
        'summary_reply': summary_res['reply'],
        'model': summary_res['model'],
    })


@csrf_exempt
@login_required
def api_rag_activate_bill(request, appt_id):
    """Loads an existing checkup bill into the active RAG Vector DB session for instant bot chat."""
    appt = get_object_or_404(Appointment, id=appt_id, user=request.user)
    bill_payload = _ensure_bill_record(appt)
    request.session['active_bill'] = bill_payload
    uk = _user_key(request)
    VECTOR_DB.index_bill_document(bill_payload, user_key=uk)
    summary_res = generate_rag_response(
        "Provide a complete summary of my uploaded medical bill including doctor, diagnosis, itemized charges, total amount, and prescribed medicines.",
        user_key=uk,
        active_bill=bill_payload
    )
    return ok(data={
        'bill': bill_payload,
        'summary_reply': summary_res['reply'],
        'model': summary_res['model'],
    })
