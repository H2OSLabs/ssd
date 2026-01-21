## Section 6: Manual Verification System

### 6.1 Philosophy

For MVP, use a **manual verification workflow** where COO or judges review submissions via Wagtail admin and enter scores directly. This approach:
- **Works well for < 100 participants** - manageable workload
- **No external dependencies** - no webhooks, no CI/CD integration
- **Simple and reliable** - fewer failure points
- **Faster to implement** - no complex automation needed
- **Flexible** - judges can apply subjective criteria

Automated webhook verification will be added in Phase 3 for scale (see `spec/future/git-integrate.md`).

### 6.2 Verification Flow

**MVP Workflow:**
1. User completes quest or hackathon submission
2. User uploads file OR provides public repository URL
3. Submission appears in Wagtail admin with status "Pending Review"
4. COO/judge opens submission in admin interface
5. COO reviews work (downloads file, visits URL, evaluates quality)
6. COO enters score (0-100) and feedback via admin
7. System updates `Submission.verification_status` to "Verified" or "Rejected"
8. System awards XP automatically if score ≥ passing_score
9. Leaderboard updates automatically

**Key Benefit:** Complete control and transparency - humans make final decisions.

### 6.3 Submission Model

The Submission model has already been detailed in Section 2.7. Key features for manual verification:

**Simplified verification statuses:**
- `pending` - Awaiting review
- `verified` - Approved by reviewer
- `rejected` - Did not meet criteria

**Manual score entry:**
- Score field: 0-100 (entered by COO)
- Feedback field: Text comments for participant
- verified_by: FK to staff member who reviewed
- verified_at: Timestamp when verified

**Submission methods:**
- File upload: `submission_file` (FileField)
- OR URL: `submission_url` (URLField for public repos/demos)
- Description: Participant's notes about their work

### 6.4 Wagtail Admin Integration

**File:** `synnovator/hackathons/admin.py`

```python
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from django.utils.html import format_html
from .models import Submission


class SubmissionAdmin(ModelAdmin):
    model = Submission
    menu_icon = 'doc-full'
    menu_label = 'Submissions'
    add_to_settings_menu = False
    list_display = (
        'get_submitter',
        'get_target',
        'get_status_badge',
        'score',
        'submitted_at',
        'get_actions'
    )
    list_filter = ('verification_status', 'submitted_at')
    search_fields = ('user__username', 'team__name', 'quest__title', 'hackathon__title')
    ordering = ['-submitted_at']

    def get_submitter(self, obj):
        if obj.team:
            return format_html('<strong>{}</strong> (Team)', obj.team.name)
        elif obj.user:
            return obj.user.get_full_name() or obj.user.username
        return "Unknown"
    get_submitter.short_description = 'Submitter'

    def get_target(self, obj):
        if obj.quest:
            return format_html('Quest: <em>{}</em>', obj.quest.title)
        elif obj.hackathon:
            return format_html('Hackathon: <em>{}</em>', obj.hackathon.title)
        return "Unknown"
    get_target.short_description = 'Target'

    def get_status_badge(self, obj):
        colors = {
            'pending': 'warning',
            'verified': 'success',
            'rejected': 'error'
        }
        color = colors.get(obj.verification_status, 'secondary')
        return format_html(
            '<span class="status-tag {}">{}</span>',
            color,
            obj.get_verification_status_display()
        )
    get_status_badge.short_description = 'Status'

    def get_actions(self, obj):
        """Show download/view links for submission content"""
        if obj.submission_file:
            return format_html(
                '<a href="{}" target="_blank" class="button button-small">Download</a>',
                obj.submission_file.url
            )
        elif obj.submission_url:
            return format_html(
                '<a href="{}" target="_blank" class="button button-small">View URL</a>',
                obj.submission_url
            )
        return "-"
    get_actions.short_description = 'Actions'


modeladmin_register(SubmissionAdmin)
```

### 6.5 Score Processing & XP Awarding

**File:** `synnovator/hackathons/scoring.py`

```python
from django.db import transaction
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def process_verification(submission):
    """
    Process a verified submission:
    - Award XP to user for quest completions
    - Update team score for hackathon submissions
    - Log the transaction

    This is called automatically when submission.verification_status
    changes to 'verified' (see Submission.save() method).
    """
    try:
        with transaction.atomic():
            # Quest submission - award XP to individual user
            if submission.quest and submission.user:
                if submission.score and submission.score >= submission.quest.passing_score:
                    xp_to_award = submission.quest.xp_reward
                    submission.user.award_xp(
                        xp_to_award,
                        reason=f"Completed quest: {submission.quest.title}"
                    )
                    logger.info(
                        f"Awarded {xp_to_award} XP to {submission.user.username} "
                        f"for quest '{submission.quest.title}' (score: {submission.score})"
                    )

            # Hackathon final submission - update team score
            elif submission.hackathon and submission.team:
                submission.team.final_score = submission.score
                submission.team.status = 'verified'
                submission.team.save()
                logger.info(
                    f"Updated team '{submission.team.name}' score to {submission.score} "
                    f"for hackathon '{submission.hackathon.title}'"
                )

    except Exception as e:
        logger.error(f"Error processing verification for submission {submission.id}: {e}")
        raise


def calculate_team_leaderboard(hackathon):
    """
    Get team leaderboard for a hackathon.
    Returns QuerySet ordered by final_score descending.
    """
    return hackathon.teams.filter(
        status__in=['submitted', 'verified']
    ).order_by('-final_score')


def calculate_user_leaderboard(limit=100):
    """
    Global user leaderboard by XP points.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    return User.objects.filter(
        xp_points__gt=0
    ).order_by('-xp_points')[:limit]
```

### 6.6 COO Verification Workflow

**Step-by-step guide for verifying submissions:**

1. **Access Submissions Dashboard**
   - Log into Wagtail admin (`/admin/`)
   - Click "Submissions" in sidebar
   - See list of all submissions with filterable status

2. **Filter Pending Submissions**
   - Use filter dropdown: "Verification status" → "Pending Review"
   - Sort by "Submitted at" (most recent first)
   - See count of pending submissions

3. **Open Submission for Review**
   - Click on submission row to open detail view
   - View submitter info (user or team name)
   - See target (quest title or hackathon title)
   - Read participant's description

4. **Review Submission Content**
   - **If file upload:** Click "Download" button → Open file locally
     - Review code, documents, presentations
     - Run code if needed (in safe environment)
   - **If URL provided:** Click "View URL" → Opens repository or demo
     - Review README, code structure, commits
     - Test demo if publicly hosted

5. **Evaluate Based on Criteria**
   - Technical: Code quality, functionality, tests
   - Commercial: Business value, market fit
   - Operational: Documentation, maintainability, UX
   - Creativity: Innovation, approach

6. **Enter Score & Feedback**
   - Scroll to verification fields
   - **Change status:** "Pending Review" → "Verified" (or "Rejected")
   - **Enter score:** 0-100 (e.g., 85.5)
   - **Write feedback:** Constructive comments
     ```
     Excellent work! Your solution demonstrates:

     Strengths:
     ✅ Functional AI implementation with good accuracy
     ✅ Clean, well-structured code
     ✅ Comprehensive documentation

     Areas for improvement:
     - Add error handling for edge cases (missing input validation)
     - Consider optimizing API call efficiency (currently 500ms avg)

     Overall: Strong submission. Score: 85/100
     ```

7. **Save & Automatic Actions**
   - Click "Save" button
   - System automatically:
     - Sets `verified_at` timestamp
     - Records `verified_by` (your user account)
     - Awards XP if quest submission and score ≥ passing threshold
     - Updates team final_score if hackathon submission
     - Triggers leaderboard recalculation
   - Participant receives notification (if notifications enabled)

**Time per submission:** 5-10 minutes for thorough review

**Efficiency tips:**
- Use browser tabs to review multiple submissions simultaneously
- Create feedback templates for common issues
- Batch similar submissions (same quest) together

### 6.7 Scalability Considerations

**Manual verification works well for:**
- **Quests:** Up to 50 submissions per day
- **Hackathons:** Up to 20-30 teams per event
- **Total:** < 100 participants per event

**When manual verification becomes bottleneck:**
- > 100 submissions per hackathon
- Multiple concurrent hackathons
- Daily quest submissions exceed 50
- COO spends > 4 hours/day on verification

**Trigger for automated verification (Phase 3):**
- Platform reaches 100+ active participants per event
- Need objective, repeatable scoring
- Want to support daily/continuous challenges
- See `spec/future/git-integrate.md` for automation implementation

### 6.8 Submission Forms & Frontend

**File:** `synnovator/hackathons/forms.py`

```python
from django import forms
from .models import Submission


class QuestSubmissionForm(forms.ModelForm):
    """Form for quest submissions"""

    class Meta:
        model = Submission
        fields = ['submission_file', 'submission_url', 'description']
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Describe your solution, approach, challenges, and any notes for reviewers...',
                'class': 'w-full'
            }),
            'submission_url': forms.URLInput(attrs={
                'placeholder': 'https://github.com/yourname/project',
                'class': 'w-full'
            })
        }
        help_texts = {
            'submission_file': 'Upload your solution (ZIP, PDF, code files) - Max 50MB',
            'submission_url': 'Or provide a public link to your repository or demo',
        }

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('submission_file')
        url = cleaned_data.get('submission_url')

        # Require at least one submission method
        if not file and not url:
            raise forms.ValidationError(
                "Please provide either a file upload OR a URL to your submission."
            )

        return cleaned_data
```

**File:** `synnovator/hackathons/views.py`

```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Quest, Submission
from .forms import QuestSubmissionForm


@login_required
def submit_quest(request, slug):
    """Handle quest submission"""
    quest = get_object_or_404(Quest, slug=slug, is_active=True)

    # Check if user already has pending submission
    existing = Submission.objects.filter(
        user=request.user,
        quest=quest,
        verification_status='pending'
    ).first()

    if existing:
        messages.warning(
            request,
            "You already have a pending submission for this quest. "
            "Please wait for it to be reviewed before submitting again."
        )
        return redirect('quest_detail', slug=slug)

    if request.method == 'POST':
        form = QuestSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.user = request.user
            submission.quest = quest

            # Calculate attempt number
            attempt_count = Submission.objects.filter(
                user=request.user,
                quest=quest
            ).count()
            submission.attempt_number = attempt_count + 1

            submission.save()

            messages.success(
                request,
                f"✅ Submission received! (Attempt #{submission.attempt_number}). "
                "You'll be notified via email when it's reviewed."
            )
            return redirect('quest_detail', slug=slug)
    else:
        form = QuestSubmissionForm()

    # Get user's previous attempts for this quest
    previous_attempts = Submission.objects.filter(
        user=request.user,
        quest=quest
    ).order_by('-submitted_at')

    return render(request, 'hackathons/submit_quest.html', {
        'quest': quest,
        'form': form,
        'previous_attempts': previous_attempts
    })
```

### 6.9 Security Considerations

**File Upload Security:**

1. **File Size Limits:**
   ```python
   # settings/base.py
   HACKATHON_MAX_SUBMISSION_SIZE = 50 * 1024 * 1024  # 50 MB
   ```

2. **Allowed File Types:**
   ```python
   HACKATHON_ALLOWED_EXTENSIONS = [
       '.zip', '.tar', '.tar.gz',
       '.pdf', '.md', '.txt',
       '.py', '.js', '.java', '.go', '.rs'
   ]
   ```

3. **Virus Scanning** (optional, for production):
   - Integrate ClamAV or cloud antivirus API
   - Scan uploaded files before saving
   - Quarantine suspicious files

4. **Storage:**
   - Store uploads outside web root
   - Use Django's FileField with upload_to pattern
   - Example: `submissions/2026/02/user123_quest456_20260215.zip`

### 6.10 Future: Automated Verification (Phase 3)

When the platform scales beyond manual verification capacity, add automated webhook-based verification:

**Features to add:**
- External CI/CD systems (GitHub Actions, GitLab CI) run automated tests
- POST results to webhook endpoint with HMAC signature verification
- Automatic score calculation based on test results, code quality metrics
- Manual review only for edge cases or appeals

**Implementation guide:**
See `spec/future/git-integrate.md` for complete webhook implementation including:
- HMAC SHA-256 signature verification code
- VerificationLog model for audit trails
- GitHub Actions workflow examples
- Webhook endpoint implementation
- Security best practices

**Trigger criteria for Phase 3:**
- Platform consistently has > 100 submissions per hackathon
- Manual verification takes > 4 hours daily
- Need for objective, repeatable scoring
- Want to support real-time verification during "sprints"

---
