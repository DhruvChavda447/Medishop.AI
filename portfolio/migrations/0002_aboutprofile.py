from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('portfolio', '0001_initial')]
    operations = [
        migrations.CreateModel(
            name='AboutProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('full_name',      models.CharField(max_length=120, default='Dhruv Chavda')),
                ('role',           models.CharField(max_length=200, default='Python Developer & AI/ML Engineer')),
                ('bio',            models.TextField(default='')),
                ('email',          models.EmailField(default='dhruvchavda.intern@gmail.com')),
                ('phone',          models.CharField(max_length=30, default='8160994508')),
                ('location',       models.CharField(max_length=120, default='Naroda, Ahmedabad, Gujarat')),
                ('status',         models.CharField(max_length=80, default='Open to Opportunities')),
                ('avatar_emoji',   models.CharField(max_length=10, default='👨‍💻')),
                ('linkedin_url',   models.URLField(blank=True, default='https://linkedin.com/in/yourprofile')),
                ('github_url',     models.URLField(blank=True, default='https://github.com/yourprofile')),
                ('twitter_url',    models.URLField(blank=True, default='')),
                ('degree',         models.CharField(max_length=200, default='B.Tech in Artificial Intelligence and Data Science')),
                ('college',        models.CharField(max_length=200, default='LJ Institute of Engineering and Technology')),
                ('edu_year',       models.CharField(max_length=60,  default='2022 – 2026')),
                ('cgpa',           models.CharField(max_length=20,  default='8.06')),
                ('job_title',      models.CharField(max_length=120, default='Python Developer')),
                ('company',        models.CharField(max_length=120, default='Actowiz Data Solutions')),
                ('job_period',     models.CharField(max_length=60,  default='Jan 2025 – Present')),
                ('job_desc',       models.TextField(default='')),
                ('skills_json',    models.TextField(default='{}')),
                ('certifications', models.TextField(default='Oracle AI & GenAI | IBM Machine Learning | University of Michigan Data Science')),
                ('updated_at',     models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
