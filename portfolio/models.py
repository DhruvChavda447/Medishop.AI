from django.db import models

class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    class Meta: ordering=['-created_at']
    def __str__(self): return f"{self.name} — {self.subject}"

class ResumeFile(models.Model):
    file = models.FileField(upload_to='resume/')
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    class Meta: ordering=['-uploaded_at']
    def __str__(self): return f"Resume — {self.filename}"

class AboutProfile(models.Model):
    """Single-row table — stores all about page content. Editable via password."""
    # Personal
    full_name       = models.CharField(max_length=120, default='Dhruv Chavda')
    role            = models.CharField(max_length=200, default='Python Developer & AI/ML Engineer')
    bio             = models.TextField(default='')
    email           = models.EmailField(default='dhruvchavda.intern@gmail.com')
    phone           = models.CharField(max_length=30, default='8160994508')
    location        = models.CharField(max_length=120, default='Naroda, Ahmedabad, Gujarat')
    status          = models.CharField(max_length=80, default='Open to Opportunities')
    avatar_emoji    = models.CharField(max_length=10, default='👨‍💻')
    # Social links
    linkedin_url    = models.URLField(blank=True, default='https://linkedin.com/in/yourprofile')
    github_url      = models.URLField(blank=True, default='https://github.com/yourprofile')
    twitter_url     = models.URLField(blank=True, default='')
    # Education
    degree          = models.CharField(max_length=200, default='B.Tech in Artificial Intelligence and Data Science')
    college         = models.CharField(max_length=200, default='LJ Institute of Engineering and Technology')
    edu_year        = models.CharField(max_length=60,  default='2022 – 2026')
    cgpa            = models.CharField(max_length=20,  default='8.06')
    # Experience
    job_title       = models.CharField(max_length=120, default='Python Developer')
    company         = models.CharField(max_length=120, default='Actowiz Data Solutions')
    job_period      = models.CharField(max_length=60,  default='Jan 2025 – Present')
    job_desc        = models.TextField(default='')
    # Skills (JSON stored as text)
    skills_json     = models.TextField(default='{}')
    # Certifications
    certifications  = models.TextField(default='Oracle AI & GenAI | IBM Machine Learning | University of Michigan Data Science')
    # Updated
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'About Profile'

    def __str__(self):
        return f"About — {self.full_name}"
