PROJECT_DIR := "sophie_bot"

ENV := $(shell poetry env info --path)

# Replace \ with \\ for windows
# ENV := $(shell cygpath "${ENV}")

#PYTHON := $(subst \,/,$(PYTHON))
PYTHON := "$(ENV)/scripts/python"

ASS_PATH := $(shell poetry run python -c "import ass_tg as _; print(_.__path__[0])")

ifneq ("$(wildcard $(ENV)/scripts/pybabel)","")
	PYBABEL := "$(ENV)/scripts/pybabel"
else ifneq ("$(wildcard $(ENV)/bin/pybabel)","")
	PYBABEL := "$(ENV)/bin/pybabel" 
else
	PYBABEL := "pybabel"
endif

NUITKA := "python" "-m" "nuitka"
NUITKA_ARGS := "--prefer-source-code" "--plugin-enable=pylint-warnings" "--follow-imports" \
			   "--include-package=sophie_bot" "--include-package-data=babel" "--assume-yes-for-downloads" "--lto=yes" \
			   "--python-flag=no_annotations" "--python-flag=isolated" "--product-name=SophieBot" \
			   "--output-dir=output/"
LOCALES_DIR := $(CURDIR)/locales


all: fix_code_style locale test_all clean build_onefile
commit: fix_code_style extract_lang test_code_style test_codeanalysis run_tests gen_wiki
test_all: test_code_style test_codeanalysis run_tests
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
	poetry run ruff check . --fix
	poetry run ruff format sophie_bot/

test_code_style:
	poetry run python -m pycln . -a -c
	poetry run ruff format sophie_bot/ --check
	poetry run ruff check .

test_codeanalysis:
	# poetry run python -m bandit sophie_bot/ -r
	poetry run mypy -p sophie_bot

run_tests:
	poetry run python -m pytest tests/ -v --alluredir=allure_results

# Locale

new_lang:
	$(PYBABEL) init -i "$(LOCALES_DIR)/sophie.pot" -d "$(LOCALES_DIR)" -D sophie -l "$(LANG)"

extract_lang:
	$(PYBABEL) extract -k "pl_:1,2" -k "p_:1,2" -k "l_:1" \
	--add-comments="NOTE: " -o "$(LOCALES_DIR)/bot.pot" --omit-header --sort-by-file --no-wrap $(PROJECT_DIR)

	cd "$(ASS_PATH)" && \
	$(PYBABEL) extract -k "pl_:1,2" -k "p_:1,2" -k "l_:1" \
	--add-comments="NOTE: " -o "$(LOCALES_DIR)/ass.pot" --omit-header --sort-by-file --no-wrap .

	# Merge
	cp "$(LOCALES_DIR)/bot.pot" "$(LOCALES_DIR)/sophie.pot"
	cat "$(LOCALES_DIR)/ass.pot" >> "$(LOCALES_DIR)/sophie.pot"

update_lang:
	$(PYBABEL) update -d "$(LOCALES_DIR)" -D "sophie" -i "$(LOCALES_DIR)/sophie.pot" \
	--ignore-pot-creation-date --omit-header --no-wrap

compile_lang:
	$(PYBABEL) compile -d "$(LOCALES_DIR)" -D "sophie" --use-fuzzy --statistics


new_locale:
	rm -rf locales/
	mkdir locales/

	make extract_lang
	make new_lang LANG=uk_UA
	make update_lang
	make compile_lang

# Wiki

gen_wiki:
	poetry run python tools/wiki_gen/start.py


dev_deps:
	rm -rf "$(ENV)/lib/site-packages/ass_tg"
	rm -rf "$(ENV)/lib/site-packages/stfu_tg"

	ln -s "$(realpath ../ass/ass_tg)" "$(ENV)/lib/site-packages/"
	ln -s "$(realpath ../stf/stfu_tg)" "$(ENV)/lib/site-packages/"
