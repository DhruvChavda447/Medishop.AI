import json, os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from portfolio.models import ContactMessage, ResumeFile, AboutProfile

# ── Default profile data (Dhruv's resume) ────────────────────────
DEFAULT_BIO = (
    "I'm a Python Developer and AI/ML Engineer currently working at Actowiz Data Solutions, "
    "where I build large-scale web scraping pipelines and automation systems. "
    "MediShop Pro is my end-to-end AI portfolio project — featuring XLM-RoBERTa NLP, "
    "Vision Transformer (ViT) image analysis, and multilingual mT5 response generation, "
    "all integrated into a production-ready Django + PostgreSQL application.\n\n"
    "I enjoy building systems that bridge ML research with real-world web applications — "
    "from ETL pipelines on AWS/BigQuery to full-stack AI healthcare platforms."
)

DEFAULT_JOB_DESC = (
    "• Large-scale data extraction using Scrapy, Requests and browser automation tools.\n"
    "• Built and optimised web and app scraping pipelines, integrating data with SQL/NoSQL databases.\n"
    "• Developed reusable Python scripts to enhance automation, accuracy and data reliability.\n"
    "• Implemented anti-bot techniques using headers, proxies and captchas for robust data collection."
)

DEFAULT_SKILLS = {
    "ai": [
        {"name": "Machine Learning / Deep Learning", "pct": 85},
        {"name": "NLP · Transformers · Fine-Tuning", "pct": 82},
        {"name": "Hugging Face · PyTorch", "pct": 80},
        {"name": "RAG · LLM Integration", "pct": 72},
    ],
    "python": [
        {"name": "Python 3.11 · Scripting", "pct": 92},
        {"name": "Django 5 · FastAPI · Flask", "pct": 88},
        {"name": "Pandas · NumPy · Scikit-learn", "pct": 88},
        {"name": "Scrapy · Requests · Automation", "pct": 85},
    ],
    "database": [
        {"name": "PostgreSQL · MySQL · SQLite", "pct": 85},
        {"name": "MongoDB · DynamoDB", "pct": 75},
        {"name": "Google BigQuery", "pct": 72},
        {"name": "AWS S3 · Boto3", "pct": 68},
    ],
    "tools": [
        {"name": "Git · Docker · Linux", "pct": 85},
        {"name": "Apache Airflow (ETL)", "pct": 75},
        {"name": "Power BI · Visualization", "pct": 70},
        {"name": "Supabase · REST APIs", "pct": 72},
    ],
}


def get_profile():
    """Always return the AboutProfile singleton, creating it with defaults if missing."""
    p = AboutProfile.objects.first()
    if not p:
        p = AboutProfile.objects.create(
            bio=DEFAULT_BIO,
            job_desc=DEFAULT_JOB_DESC,
            skills_json=json.dumps(DEFAULT_SKILLS),
        )
    # Ensure skills_json is valid
    if not p.skills_json or p.skills_json.strip() in ('', '{}'):
        p.skills_json = json.dumps(DEFAULT_SKILLS)
        p.save()
    if not p.bio.strip():
        p.bio = DEFAULT_BIO
        p.save()
    if not p.job_desc.strip():
        p.job_desc = DEFAULT_JOB_DESC
        p.save()
    try:
        skills = json.loads(p.skills_json)
    except Exception:
        skills = DEFAULT_SKILLS
    return p, skills


@login_required
def about_view(request):
    profile, skills = get_profile()
    resume = ResumeFile.objects.filter(is_active=True).first()

    if request.method == 'POST':
        name    = request.POST.get('name','').strip()
        email   = request.POST.get('email','').strip()
        phone   = request.POST.get('phone','').strip()
        subject = request.POST.get('subject','').strip()
        msg     = request.POST.get('message','').strip()

        if name and email and subject and msg:
            ContactMessage.objects.create(
                name=name, email=email, phone=phone,
                subject=subject, message=msg
            )
            # Try email — silently ignore any failure
            _try_send_email(name, email, phone, subject, msg)
            messages.success(request, "✅ Message sent! Dhruv will get back to you within 24 hours.")
            return redirect('about')
        messages.error(request, 'Please fill all required fields.')

    certs = [c.strip() for c in profile.certifications.split('|') if c.strip()]
    job_desc_lines = [l.strip().lstrip('•').lstrip('•').strip() for l in profile.job_desc.splitlines() if l.strip()]
    return render(request, 'portfolio/about.html', {
        'profile': profile,
        'skills': skills,
        'resume': resume,
        'certs': certs,
        'job_desc_lines': job_desc_lines,
    })


# def _try_send_email(name, email, phone, subject, msg):
#     """Try multiple methods to send contact notification."""
#     body = (
#         f"New contact from MediShop Pro\n"
#         f"{'─'*42}\n"
#         f"Name:    {name}\n"
#         f"Email:   {email}\n"
#         f"Phone:   {phone or 'Not provided'}\n"
#         f"Subject: {subject}\n"
#         f"{'─'*42}\n"
#         f"Message:\n{msg}\n"
#     )
#     # Method 1: Django email backend (Gmail SMTP)
#     try:
#         from django.core.mail import send_mail
#         send_mail(
#             subject=f"[MediShop Contact] {subject}",
#             message=body,
#             from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@medishop.com'),
#             recipient_list=[getattr(settings, 'CONTACT_EMAIL', 'dhruvchavda.intern@gmail.com')],
#             fail_silently=False,
#         )
#         return True
#     except Exception:
#         pass
#     # Method 2: Direct smtplib fallback
#     try:
#         import smtplib
#         from email.mime.text import MIMEText
#         host_user = os.getenv('EMAIL_HOST_USER','')
#         host_pass = os.getenv('EMAIL_HOST_PASSWORD','')
#         if host_user and host_pass:
#             m = MIMEText(body)
#             m['Subject'] = f"[MediShop Contact] {subject}"
#             m['From'] = host_user
#             m['To'] = getattr(settings,'CONTACT_EMAIL','dhruvchavda.intern@gmail.com')
#             with smtplib.SMTP('smtp.gmail.com', 587) as s:
#                 s.ehlo(); s.starttls(); s.login(host_user, host_pass)
#                 s.send_message(m)
#             return True
#     except Exception:
#         pass
#     return False


# ── Password-protected about page editor ─────────────────────────
@login_required
def about_edit_view(request):
    profile, skills = get_profile()
    EDIT_PASS = getattr(settings, 'ABOUT_EDIT_PASSWORD', getattr(settings, 'RESUME_PASSWORD', 'MediShop@Resume2024'))
    ctx = {'profile': profile, 'skills': skills, 'step': 'password', 'error': None, 'success': None}

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'verify_password':
            pwd = request.POST.get('password', '')
            if pwd == EDIT_PASS:
                ctx['step'] = 'edit'
                ctx['skills_json_pretty'] = json.dumps(skills, indent=2)
            else:
                ctx['error'] = 'Incorrect password.'

        elif action == 'save_profile':
            pwd = request.POST.get('password', '')
            if pwd != EDIT_PASS:
                ctx['error'] = 'Session expired. Please re-enter password.'
                ctx['step'] = 'password'
            else:
                # Save all fields
                profile.full_name    = request.POST.get('full_name', profile.full_name).strip()
                profile.role         = request.POST.get('role', profile.role).strip()
                profile.bio          = request.POST.get('bio', profile.bio).strip()
                profile.email        = request.POST.get('email', profile.email).strip()
                profile.phone        = request.POST.get('phone', profile.phone).strip()
                profile.location     = request.POST.get('location', profile.location).strip()
                profile.status       = request.POST.get('status', profile.status).strip()
                profile.avatar_emoji = request.POST.get('avatar_emoji', profile.avatar_emoji).strip()
                profile.linkedin_url = request.POST.get('linkedin_url', profile.linkedin_url).strip()
                profile.github_url   = request.POST.get('github_url', profile.github_url).strip()
                profile.twitter_url  = request.POST.get('twitter_url', profile.twitter_url).strip()
                profile.degree       = request.POST.get('degree', profile.degree).strip()
                profile.college      = request.POST.get('college', profile.college).strip()
                profile.edu_year     = request.POST.get('edu_year', profile.edu_year).strip()
                profile.cgpa         = request.POST.get('cgpa', profile.cgpa).strip()
                profile.job_title    = request.POST.get('job_title', profile.job_title).strip()
                profile.company      = request.POST.get('company', profile.company).strip()
                profile.job_period   = request.POST.get('job_period', profile.job_period).strip()
                profile.job_desc     = request.POST.get('job_desc', profile.job_desc).strip()
                profile.certifications = request.POST.get('certifications', profile.certifications).strip()

                # Validate and save skills JSON
                raw_skills = request.POST.get('skills_json', '').strip()
                try:
                    parsed_skills = json.loads(raw_skills)
                    profile.skills_json = json.dumps(parsed_skills)
                except Exception:
                    profile.skills_json = json.dumps(DEFAULT_SKILLS)

                profile.save()
                ctx['success'] = '✅ Profile updated! All users now see your new About page.'
                ctx['step'] = 'edit'
                ctx['skills_json_pretty'] = json.dumps(json.loads(profile.skills_json), indent=2)

    return render(request, 'portfolio/about_edit.html', ctx)


# ── Resume views ──────────────────────────────────────────────────
def resume_download_view(request):
    """Public — no login required so any visitor can view/download."""
    resume = ResumeFile.objects.filter(is_active=True).first()
    if not resume:
        raise Http404("Resume not uploaded yet. Please use /resume/upload/ to add your PDF.")
    mode = request.GET.get('mode', 'download')
    try:
        resp = FileResponse(resume.file.open('rb'), content_type='application/pdf')
        disp = 'inline' if mode == 'view' else 'attachment'
        safe = resume.filename.replace('"','').replace("'",'')
        resp['Content-Disposition'] = f'{disp}; filename="{safe}"'
        resp['X-Frame-Options'] = 'SAMEORIGIN'
        return resp
    except Exception as e:
        raise Http404(f"Resume file not found: {e}")


def resume_upload_view(request):
    PASS = getattr(settings, 'RESUME_PASSWORD', 'MediShop@Resume2024')
    error = success = None
    if request.method == 'POST':
        pwd = request.POST.get('password', '')
        f   = request.FILES.get('resume_file')
        if pwd != PASS:
            error = 'Incorrect password.'
        elif not f:
            error = 'Please select a PDF file.'
        elif not f.name.lower().endswith('.pdf'):
            error = 'Only PDF files are allowed.'
        else:
            ResumeFile.objects.all().update(is_active=False)
            ResumeFile.objects.create(file=f, filename=f.name, is_active=True)
            success = f"✅ Resume '{f.name}' uploaded! All users now see the new resume."
    return render(request, 'portfolio/resume_upload.html', {'error': error, 'success': success})
def _try_send_email(name, email, phone, subject, msg):
    try:
        import urllib.request, urllib.parse, json
        endpoint = getattr(settings, 'FORMSPREE_URL', '')
        if not endpoint:
            return False
        data = json.dumps({
            'name': name,
            'email': email,
            'phone': phone or 'Not provided',
            'subject': subject,
            'message': msg,
        }).encode('utf-8')
        req = urllib.request.Request(
            endpoint, data=data, method='POST',
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status == 200
    except Exception as e:
        print(f"Email error: {e}")
        return False