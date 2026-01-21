# Language Switcher Implementation

## Overview

A language switcher has been added to the header navigation, allowing users to switch between English and Chinese (Simplified) on all pages.

## What Was Implemented

### 1. Language Switcher Component
**File:** `templates/components/language-switcher.html`

- Displays available languages as buttons
- Shows only languages different from the current language
- Uses Django's i18n framework for language detection and switching
- Styled with Tailwind CSS to match the site design
- Supports dark mode

### 2. Header Integration
**File:** `templates/navigation/header.html`

The language switcher is integrated in two locations:

- **Desktop navigation:** Between the search button and theme toggle
- **Mobile menu:** Below the search field

### 3. URL Configuration
**File:** `synnovator/urls.py`

Added Django's `set_language` view at `/i18n/setlang/` to handle language switching POST requests.

## How It Works

1. **Display Logic:**
   - If current language is English → Shows "中文" button
   - If current language is Chinese → Shows "EN" button

2. **Switching Process:**
   - User clicks language button
   - Form submits to `/i18n/setlang/` with target language
   - Django's `LocaleMiddleware` processes the request
   - User is redirected to the same page in the new language
   - Language preference is stored in session

3. **URL Structure:**
   - English pages: `/en/`, `/en/blog/`, `/en/search/`
   - Chinese pages: `/zh-hans/`, `/zh-hans/blog/`, `/zh-hans/search/`

## Testing

### 1. Start Development Server
```bash
uv run python manage.py runserver
```

### 2. Visit Homepage
```
http://127.0.0.1:8000/en/
```

### 3. Look for Language Switcher
You should see a button labeled "中文" in the header navigation (desktop) or mobile menu.

### 4. Test Language Switching
1. Click the "中文" button
2. URL changes to `http://127.0.0.1:8000/zh-hans/`
3. Button now shows "EN" to switch back
4. Click "EN" to return to English

### 5. Test on Different Pages
- Homepage: `/en/` → `/zh-hans/`
- Blog: `/en/blog/` → `/zh-hans/blog/`
- Search: `/en/search/` → `/zh-hans/search/`

## Creating Translated Content

To provide translated content for the language switcher to work with:

### Via Wagtail Admin

1. Navigate to **Wagtail Admin** → any page
2. Click **"..." menu** → **"Translate"**
3. Select **"简体中文"**
4. Edit the translated content
5. **Publish**
6. Test the language switcher on that page

### Via Locale Sync

1. Configure locale synchronization:
   - **Settings** → **Locales** → **zh-hans (简体中文)**
   - Set **Sync from:** English
   - **Save**

2. When you edit English pages, they'll be marked for sync
3. Use the translation interface to sync content

## Styling

The language switcher uses these Tailwind CSS classes:

```css
/* Button base styles */
text-sm font-semibold font-codepro
px-3 py-1.5 rounded border

/* Light mode */
border-mackerel-200
hover:border-mackerel-300
hover:bg-mackerel-50

/* Dark mode */
dark:border-mackerel-700
dark:hover:border-mackerel-600
dark:hover:bg-mackerel-800

/* Transitions */
transition-colors
```

## Customization

### Change Language Display Names

Edit `templates/components/language-switcher.html`:

```django
{% if lang_code == 'en' %}
    English  {# Changed from EN #}
{% elif lang_code == 'zh-hans' %}
    简体中文  {# Already full name #}
{% endif %}
```

### Change Button Styling

Modify the CSS classes in the `<button>` element:

```django
<button
    type="submit"
    class="your-custom-classes-here"
>
```

### Add More Languages

1. Update `synnovator/settings/base.py`:
```python
LANGUAGES = [
    ("en", "English"),
    ("zh-hans", "简体中文"),
    ("fr", "Français"),  # Add French
]
```

2. Create the locale in Wagtail admin
3. Update language display logic in `language-switcher.html`

### Change Switcher Position

Move the `{% include "components/language-switcher.html" %}` line in `templates/navigation/header.html` to a different position in the `<ul>` list.

## Files Modified

| File | Changes |
|------|---------|
| `templates/components/language-switcher.html` | **New** - Language switcher component |
| `templates/navigation/header.html` | Added language switcher to desktop nav and mobile menu |
| `synnovator/urls.py` | Added `set_language` URL pattern |

## Technical Details

### Django i18n Tags Used

- `{% load i18n %}` - Load internationalization template tags
- `{% get_current_language %}` - Get current language code
- `LANGUAGES` - List of available languages from settings
- `{% url 'set_language' %}` - URL for language switching view

### Session Storage

Language preference is stored in the user's session via Django's `LocaleMiddleware`. This means:

- Language persists across page navigation
- Clears when session expires
- Works for both authenticated and anonymous users

### CSRF Protection

The language switch form includes `{% csrf_token %}` for security.

## Troubleshooting

### Language Switcher Not Appearing

1. Check template loading:
```bash
uv run python manage.py shell -c "
from django.template.loader import get_template
template = get_template('components/language-switcher.html')
print('Template loads successfully')
"
```

2. Verify settings:
```bash
uv run python manage.py shell -c "
from django.conf import settings
print('LANGUAGES:', settings.LANGUAGES)
print('USE_I18N:', settings.USE_I18N)
"
```

### Language Not Switching

1. Check middleware order in `settings/base.py`:
```python
MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',  # Must be before LocaleMiddleware
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    # ...
]
```

2. Verify URL is registered:
```bash
uv run python manage.py show_urls | grep setlang
```

### Translated Content Not Showing

1. Check page locale:
```bash
uv run python manage.py shell -c "
from wagtail.models import Page
page = Page.objects.get(id=YOUR_PAGE_ID)
print('Page locale:', page.locale.language_code)
"
```

2. Verify translation exists:
```bash
uv run python manage.py shell -c "
from wagtail.models import Page, Locale
zh = Locale.objects.get(language_code='zh-hans')
page = Page.objects.get(id=YOUR_PAGE_ID)
print('Has Chinese translation:', page.has_translation(zh))
"
```

## Related Documentation

- [Wagtail Localize Integration](../spec/wagtail-localize-implementation.md)
- [i18n Best Practices](.claude/skills/wagtail-builder/rules/i18n.md)
- [Django i18n Documentation](https://docs.djangoproject.com/en/5.2/topics/i18n/)
- [Wagtail Localize Documentation](https://wagtail-localize.org/)

## Summary

✅ Language switcher component created
✅ Integrated into header navigation (desktop + mobile)
✅ URL routing configured
✅ System checks pass
✅ Templates load successfully
✅ Ready to use on all pages

The language switcher is now live and functional across the entire site!
