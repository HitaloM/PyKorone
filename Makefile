PROJECT_DIR := "sophie_bot"

PYTHON := $(shell poetry env info --path)
#PYTHON := $(subst \,/,$(PYTHON))
PYTHON := "$(PYTHON)/scripts/python"

ASS_PATH := $(shell poetry run python -c "import ass_tg as _; print(_.__path__[0])")

NUITKA := "python" "-m" "nuitka"
NUITKA_ARGS := "--prefer-source-code" "--plugin-enable=pylint-warnings" "--follow-imports" \
			   "--include-package=sophie_bot" "--include-package-data=babel" "--assume-yes-for-downloads" "--lto=yes" \
			   "--python-flag=no_annotations" "--python-flag=isolated" "--product-name=SophieBot" \
			   "--output-dir=output/"
LOCALES_DIR := $(CURDIR)/locales


all: fix_code_style locale test_all clean build_onefile
commit: fix_code_style locale test_code_style test_codeanalysis
test_all: test_code_style test_codeanalysis
locale: extract_lang update_lang compile_lang


# Build

clean:
	@echo "Cleaning build directories..."
	rm -rf output/

build_onefile:
	@echo "Building onefile..."
	poetry run python -m nuitka $(PROJECT_DIR) $(NUITKA_ARGS) --standalone --onefile --linux-onefile-icon=build/icon.png

build_standalone:
	@echo "Building standalone..."
	poetry run python -m nuitka $(PROJECT_DIR) $(NUITKA_ARGS) --standalone


fix_code_style:
	poetry run python -m pycln . -a
	poetry run python -m isort .
	poetry run python -m black --preview --color sophie_bot/

test_code_style:
	poetry run python -m pycln . -a -c
	poetry run python -m black --preview --check sophie_bot/
	poetry run python -m isort . -c
	poetry run python -m flake8

test_codeanalysis:
	# poetry run python -m bandit sophie_bot/ -r
	poetry run mypy -p sophie_bot
	# python -m pytest tests -v --alluredir=allure_results

# Locale

new_lang:
	pybabel init -i "$(LOCALES_DIR)/bot.pot" -d "$(LOCALES_DIR)" -D bot -l "$(LANG)"
	pybabel init -i "$(LOCALES_DIR)/ass.pot" -d "$(LOCALES_DIR)" -D ass -l "$(LANG)"

extract_lang:
	pybabel extract -k "pl_:1,2" -k "p_:1,2" -k "l_:1" \
	--add-comments="NOTE: " -o "$(LOCALES_DIR)/bot.pot" -w 120 --omit-header $(PROJECT_DIR)

	cd "$(ASS_PATH)" && \
	pybabel extract -k "pl_:1,2" -k "p_:1,2" -k "l_:1" \
	--add-comments="NOTE: " -o "$(LOCALES_DIR)/ass.pot" -w 120 --omit-header .

update_lang:
	pybabel update -d "$(LOCALES_DIR)" -D "bot" -i "$(LOCALES_DIR)/bot.pot" --omit-header
	pybabel update -d "$(LOCALES_DIR)" -D "ass" -i "$(LOCALES_DIR)/ass.pot" --omit-header

compile_lang:
	pybabel compile -d "$(LOCALES_DIR)" -D "bot" --use-fuzzy --statistics


new_locale:
	rm -rf locales/
	mkdir locales/

	make extract_lang
	make new_lang LANG=en_US
	make update_lang
	make compile_lang



# Test things for locales

#test_extract:
#	locales_dir='tests/unit/middlewares/locales'
#	rm -rf tests/unit/middlewares/locales/*
#	pybabel extract --input-dirs=tests -k "__:1,2" --add-comments=NOTE -o "$locales_dir/bot.pot"
#	pybabel init -i "$locales_dir/bot.pot" -d "$locales_dir" -D bot -l en
#	pybabel init -i "$locales_dir/bot.pot" -d "$locales_dir" -D bot -l ru
#
#test_compile():
#	locales_dir='tests/unit/middlewares/locales'
#	pybabel compile -d "$locales_dir" -D "bot"


# Database migration things

db_drop_migrations:
	# Deletes all current migrations and create a new one
	rm -rf migrations/

	aerich init-db
	aerich upgrade

db_migrate:
	aerich upgrade

db_new_migrate:
	aerich migrate