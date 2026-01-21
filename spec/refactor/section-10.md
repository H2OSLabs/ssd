## Section 10: Security Considerations

### 10.1 File Upload Security

#### 10.1.1 File Size Limits

**Enforce strict file size limits to prevent DoS attacks:**

```python
# settings/base.py
HACKATHON_MAX_SUBMISSION_SIZE = 50 * 1024 * 1024  # 50 MB

# forms.py
class QuestSubmissionForm(forms.ModelForm):
    def clean_submission_file(self):
        file = self.cleaned_data.get('submission_file')
        if file:
            if file.size > settings.HACKATHON_MAX_SUBMISSION_SIZE:
                raise forms.ValidationError(
                    f"File size exceeds {settings.HACKATHON_MAX_SUBMISSION_SIZE / (1024*1024)}MB limit."
                )
        return file
```

#### 10.1.2 File Type Validation

**Whitelist allowed file extensions:**

```python
# settings/base.py
HACKATHON_ALLOWED_EXTENSIONS = [
    '.zip', '.tar', '.tar.gz', '.tgz',
    '.pdf', '.md', '.txt',
    '.py', '.js', '.java', '.go', '.rs', '.cpp', '.c', '.h'
]

# forms.py
import os

def clean_submission_file(self):
    file = self.cleaned_data.get('submission_file')
    if file:
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in settings.HACKATHON_ALLOWED_EXTENSIONS:
            raise forms.ValidationError(
                f"File type '{ext}' not allowed. Allowed types: {', '.join(settings.HACKATHON_ALLOWED_EXTENSIONS)}"
            )
    return file
```

#### 10.1.3 Virus Scanning (Production)

**For production, integrate antivirus scanning:**

```python
# Optional: ClamAV integration
import subprocess

def scan_file_for_viruses(file_path):
    """Scan uploaded file with ClamAV"""
    try:
        result = subprocess.run(
            ['clamscan', '--no-summary', file_path],
            capture_output=True,
            timeout=30
        )
        if result.returncode != 0:
            return False, "Virus detected"
        return True, "Clean"
    except subprocess.TimeoutExpired:
        return False, "Scan timeout"
    except FileNotFoundError:
        # ClamAV not installed - skip scanning in development
        return True, "Scan skipped (ClamAV not available)"

# In view or signal handler:
def handle_submission_upload(submission):
    if submission.submission_file:
        is_clean, message = scan_file_for_viruses(submission.submission_file.path)
        if not is_clean:
            submission.delete()  # Remove infected file
            raise ValidationError(f"File failed security scan: {message}")
```

#### 10.1.4 Secure File Storage

**Store uploads outside web root with Django's FileField:**

```python
# models.py
class Submission(models.Model):
    submission_file = models.FileField(
        upload_to='submissions/%Y/%m/',  # Organized by year/month
        blank=True,
        null=True
    )

# settings/base.py
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# For production, use S3 or similar:
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

### 10.2 Code Execution Prevention

**NEVER execute user-submitted code on Synnovator servers.**

❌ **Dangerous - DO NOT DO THIS:**
```python
# These are DANGEROUS and should NEVER be used:
eval(user_code)
exec(submission.code)
subprocess.run(f"python {user_script}")
os.system(user_command)
```

✅ **Safe MVP Approach:**
- COO downloads files and reviews them manually in a safe, isolated environment
- No automatic code execution on server
- External verification (GitHub Actions) runs in Phase 3, not on Synnovator servers

### 10.3 Access Control

#### 10.3.1 Team Management Permissions

**Ensure users can only modify teams they're members of:**

```python
# views.py
from django.core.exceptions import PermissionDenied

def update_team(request, team_slug):
    team = get_object_or_404(Team, slug=team_slug)

    # Check if user is team member
    if not team.members.filter(id=request.user.id).exists():
        raise PermissionDenied("You are not a member of this team")

    # Check if user is leader for privileged actions
    membership = team.membership.get(user=request.user)

    if request.method == 'DELETE':
        if not membership.is_leader:
            raise PermissionDenied("Only team leaders can disband teams")

    if 'remove_member' in request.POST:
        if not membership.is_leader:
            raise PermissionDenied("Only team leaders can remove members")

    # Process request...
```

#### 10.3.2 Submission Access Control

**Users can only view their own submissions:**

```python
# views.py
@login_required
def view_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)

    # Check ownership
    is_owner = (
        submission.user == request.user or
        (submission.team and submission.team.members.filter(id=request.user.id).exists())
    )

    if not is_owner and not request.user.is_staff:
        raise PermissionDenied("You do not have access to this submission")

    return render(request, 'hackathons/submission_detail.html', {
        'submission': submission
    })
```

### 10.4 Input Validation

#### 10.4.1 URL Validation

**Validate submission URLs to prevent SSRF attacks:**

```python
from urllib.parse import urlparse

def clean_submission_url(self):
    url = self.cleaned_data.get('submission_url')
    if url:
        parsed = urlparse(url)

        # Only allow http/https
        if parsed.scheme not in ['http', 'https']:
            raise forms.ValidationError("Only HTTP(S) URLs are allowed")

        # Block localhost and private IPs
        hostname = parsed.hostname
        if hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
            raise forms.ValidationError("Local URLs are not allowed")

        # Optional: Whitelist specific domains
        allowed_domains = ['github.com', 'gitlab.com', 'bitbucket.org']
        if hostname and not any(hostname.endswith(domain) for domain in allowed_domains):
            raise forms.ValidationError(
                f"URL must be from an allowed domain: {', '.join(allowed_domains)}"
            )

    return url
```

#### 10.4.2 Score Validation

**Validate score range in Wagtail admin:**

```python
# models.py
class Submission(models.Model):
    score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )

    def clean(self):
        super().clean()
        if self.score is not None:
            if self.score < 0 or self.score > 100:
                raise ValidationError("Score must be between 0 and 100")
```

#### 10.4.3 XSS Prevention

**Sanitize user-generated content in feedback and descriptions:**

```python
# Install: pip install bleach
import bleach

# In template (Django auto-escapes by default):
{{ submission.description|linebreaks }}  # Safe

# If rendering rich text or markdown:
import markdown
from bleach import clean

def render_safe_markdown(text):
    """Render markdown but strip dangerous HTML"""
    html = markdown.markdown(text)
    return clean(
        html,
        tags=['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'code', 'pre', 'a'],
        attributes={'a': ['href', 'title']},
        protocols=['http', 'https', 'mailto']
    )
```

### 10.5 CSRF Protection

**Django's CSRF protection is enabled by default. Ensure it's not bypassed:**

```python
# views.py - CSRF token required for all POST requests
def submit_quest(request, slug):
    if request.method == 'POST':
        # CSRF token automatically validated by Django middleware
        form = QuestSubmissionForm(request.POST, request.FILES)
        # ...

# For AJAX requests:
# templates/base.html
<script>
// Include CSRF token in AJAX requests
const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
fetch('/api/endpoint/', {
    method: 'POST',
    headers: {
        'X-CSRFToken': csrftoken
    },
    body: JSON.stringify(data)
});
</script>
```

### 10.6 SQL Injection Prevention

**Django ORM automatically parameterizes queries. Avoid raw SQL:**

✅ **Safe - Use Django ORM:**
```python
# Automatic parameterization
Team.objects.filter(name=user_input)
Submission.objects.filter(user__username=username)

# If raw SQL is necessary, use parameters:
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT * FROM submission WHERE id = %s", [submission_id])
```

❌ **Dangerous - DO NOT DO THIS:**
```python
# SQL injection vulnerability!
Team.objects.raw(f"SELECT * FROM team WHERE name = '{user_input}'")
cursor.execute(f"SELECT * FROM submission WHERE id = {submission_id}")
```

### 10.7 Rate Limiting

**Prevent abuse of submission endpoints:**

```python
# Install: pip install django-ratelimit
from django_ratelimit.decorators import ratelimit

@login_required
@ratelimit(key='user', rate='10/h', method='POST')  # 10 submissions per hour per user
def submit_quest(request, slug):
    """Rate-limited quest submission"""
    from django_ratelimit.exceptions import Ratelimited

    # If rate limit exceeded, django-ratelimit raises Ratelimited exception
    # Handle it globally or per-view
    pass

# settings.py
RATELIMIT_ENABLE = True  # Set to False in development
```

### 10.8 Authentication & Session Security

**Secure session configuration:**

```python
# settings/production.py
SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to cookies
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Password requirements
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
```

### 10.9 Logging & Monitoring

**Log security events for audit trails:**

```python
# settings/base.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'security': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['security'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# views.py
import logging
logger = logging.getLogger('django.security')

def verify_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)

    # Log verification action
    logger.info(f"User {request.user.id} verified submission {submission.id} with score {submission.score}")
```

### 10.10 Future: Webhook Security (Phase 3)

When adding automated webhook verification in Phase 3, implement:

**HMAC SHA-256 Signature Verification:**
```python
def verify_hmac_signature(payload_body: bytes, secret: str, signature: str) -> bool:
    """Verify webhook signature from GitHub Actions/GitLab CI"""
    import hmac
    import hashlib

    expected = hmac.new(
        key=secret.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)
```

**IP Whitelisting:**
```python
ALLOWED_WEBHOOK_IPS = [
    '140.82.112.0/20',  # GitHub Actions IP range
    # Add GitLab CI ranges
]
```

See `spec/future/git-integrate.md` for complete webhook security implementation.

---
