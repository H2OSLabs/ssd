.PHONY: init start load-data dump-data reset-db translate-ui translate-content compile-translations translations

init: load-data start

start:
	uv run python manage.py runserver

load-data:
	uv run python manage.py createcachetable
	uv run python manage.py migrate
	uv run python manage.py load_initial_data
	uv run python manage.py collectstatic --noinput

dump-data:
	uv run python manage.py dumpdata --natural-foreign --indent 2 -e auth.permission -e contenttypes -e wagtailcore.GroupCollectionPermission -e wagtailimages.rendition -e images.rendition -e sessions -e wagtailsearch.indexentry -e wagtailsearch.sqliteftsindexentry -e wagtailcore.referenceindex -e wagtailcore.pagesubscription > fixtures/demo.json

reset-db:
	rm -f db.sqlite3
	uv run python manage.py createcachetable
	uv run python manage.py migrate
	uv run python manage.py load_initial_data

# Extract UI strings (Django templates + Python code)
translate-ui:
	@echo "Extracting translatable UI strings..."
	uv run python manage.py makemessages --all --ignore=.venv --ignore=node_modules
	@echo "✓ UI translation files generated in locale/*/LC_MESSAGES/django.po"
	@echo "  Edit these files to add translations, then run: make compile-translations"

# Export Wagtail content translations
translate-content:
	@echo "Exporting Wagtail content translations..."
	uv run python manage.py export_translations --locale=zh-hans --verbose
	@echo "✓ Content translations exported to translations/exports/"

# Compile all translations (.po -> .mo)
compile-translations:
	@echo "Compiling translation files..."
	uv run python manage.py compilemessages
	@echo "✓ Translations compiled successfully"
	@echo "  Restart server to see changes: make start"

# Complete translation workflow (extract + compile)
translations: translate-ui compile-translations
	@echo "✓ Translation workflow complete"
