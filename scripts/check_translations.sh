#!/bin/bash
# Translation Quality Check Script
# Run this before committing code with UI changes

set -e

echo "🔍 Translation Quality Check"
echo "=============================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Check 1: Find hardcoded Chinese in templates
echo "1. Checking for hardcoded Chinese in templates..."
HARDCODED_CHINESE=$(grep -r "[\u4e00-\u9fff]" templates/ --include="*.html" 2>/dev/null | grep -v "{% trans" | grep -v "{% blocktrans" | grep -v "{#" || true)

if [ -n "$HARDCODED_CHINESE" ]; then
    echo -e "${RED}❌ Found hardcoded Chinese text (not wrapped in {% trans %}):${NC}"
    echo "$HARDCODED_CHINESE"
    echo ""
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓ No hardcoded Chinese found${NC}"
fi
echo ""

# Check 2: Find empty translations in Chinese PO file
echo "2. Checking for untranslated strings in Chinese PO file..."
UNTRANSLATED=$(grep -A 1 'msgid "[^"]' locale/zh_Hans/LC_MESSAGES/django.po 2>/dev/null | grep 'msgstr ""$' || true)

if [ -n "$UNTRANSLATED" ]; then
    COUNT=$(echo "$UNTRANSLATED" | wc -l)
    echo -e "${YELLOW}⚠ Found $COUNT untranslated strings in locale/zh_Hans/LC_MESSAGES/django.po${NC}"
    echo "  Please translate these before committing."
    echo ""
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✓ All strings are translated${NC}"
fi
echo ""

# Check 3: Verify MO files exist
echo "3. Checking for compiled translation files..."
if [ ! -f "locale/zh_Hans/LC_MESSAGES/django.mo" ]; then
    echo -e "${RED}❌ Missing compiled Chinese translation file${NC}"
    echo "  Run: make compile-translations"
    echo ""
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓ Chinese MO file exists${NC}"
fi

if [ ! -f "locale/en/LC_MESSAGES/django.mo" ]; then
    echo -e "${YELLOW}⚠ Missing compiled English translation file${NC}"
    echo "  This is usually OK if English is the source language"
    echo ""
else
    echo -e "${GREEN}✓ English MO file exists${NC}"
fi
echo ""

# Check 4: Verify PO files are newer than MO files (or equal)
echo "4. Checking if translations need recompilation..."
if [ -f "locale/zh_Hans/LC_MESSAGES/django.po" ] && [ -f "locale/zh_Hans/LC_MESSAGES/django.mo" ]; then
    if [ "locale/zh_Hans/LC_MESSAGES/django.po" -nt "locale/zh_Hans/LC_MESSAGES/django.mo" ]; then
        echo -e "${YELLOW}⚠ PO file is newer than MO file${NC}"
        echo "  Run: make compile-translations"
        echo ""
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${GREEN}✓ Translation files are up to date${NC}"
    fi
fi
echo ""

# Check 5: Find Chinese msgid in PO files
echo "5. Checking for Chinese msgid (should use English)..."
CHINESE_MSGID=$(grep 'msgid ".*[\u4e00-\u9fff]' locale/*/LC_MESSAGES/django.po 2>/dev/null || true)

if [ -n "$CHINESE_MSGID" ]; then
    echo -e "${RED}❌ Found Chinese in msgid (must use English):${NC}"
    echo "$CHINESE_MSGID"
    echo ""
    echo "  Fix: Replace Chinese msgid with English equivalent"
    echo "  Example: msgid \"欢迎\" → msgid \"Welcome\""
    echo ""
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓ All msgid are in English${NC}"
fi
echo ""

# Check 6: Find hardcoded text in Python files
echo "6. Checking for hardcoded Chinese in Python files..."
PYTHON_CHINESE=$(grep -r "[\u4e00-\u9fff]" synnovator/ --include="*.py" 2>/dev/null | grep -v "migrations/" | grep -v "_(" | grep -v "gettext" | grep -v "# " | grep -v '"""' || true)

if [ -n "$PYTHON_CHINESE" ]; then
    echo -e "${YELLOW}⚠ Found potential hardcoded Chinese in Python files:${NC}"
    echo "$PYTHON_CHINESE"
    echo ""
    echo "  If these are user-facing strings, wrap them with _(\"...\")"
    echo ""
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✓ No hardcoded Chinese in Python files${NC}"
fi
echo ""

# Summary
echo "=============================="
echo "Summary"
echo "=============================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All translation checks passed!${NC}"
    echo ""
    echo "Safe to commit. Your translations are properly configured."
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS warning(s) found${NC}"
    echo ""
    echo "Consider fixing these before committing."
    exit 0
else
    echo -e "${RED}❌ $ERRORS error(s) and $WARNINGS warning(s) found${NC}"
    echo ""
    echo "Please fix errors before committing."
    echo ""
    echo "Quick fix commands:"
    echo "  1. Extract translations: make translate-ui"
    echo "  2. Edit Chinese PO file: locale/zh_Hans/LC_MESSAGES/django.po"
    echo "  3. Compile translations: make compile-translations"
    echo "  4. Run this check again: bash scripts/check_translations.sh"
    exit 1
fi
