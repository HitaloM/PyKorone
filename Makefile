PROJECT_DIR := "sophie_bot"

# Use uv for package management - no need for explicit environment path
PYTHON := "uv"
ASS_PATH := $(shell uv run python -c "import ass_tg as _; print(_.__path__[0])" 2>/dev/null)

# Use uv run for pybabel
PYBABEL := "pybabel"

NUITKA := "python" "-m" "nuitka"
NUITKA_ARGS := "--prefer-source-code" "--plugin-enable=pylint-warnings" "--follow-imports" \
			   "--include-package=sophie_bot" "--include-package-data=babel" "--assume-yes-for-downloads" "--lto=yes" \
			   "--python-flag=no_annotations" "--python-flag=isolated" "--product-name=SophieBot" \
			   "--output-dir=output/"
LOCALES_DIR := $(CURDIR)/locales


all: fix_code_style locale test_all clean build_onefile
commit: fix_code_style extract_lang test_code_style test_codeanalysis run_tests gen_wiki api
test_all: test_code_style test_codeanalysis run_tests
locale: extract_lang update_lang compile_lang


# Build

pull_libs:
	@echo "Pulling latest libs..."
	mkdir -p libs
	if [ ! -d "libs/stf" ]; then \
		git clone https://gitlab.com/SophieBot/stf.git libs/stf; \
	else \
		cd libs/stf && git pull; \
	fi
	if [ ! -d "libs/ass" ]; then \
		git clone https://gitlab.com/SophieBot/ass.git libs/ass; \
	else \
		cd libs/ass && git pull; \
	fi

sync_libs: pull_libs
	uv sync --reinstall-package ass-tg
	uv sync --reinstall-package stf-tg

clean:
	@echo "Cleaning build directories..."
	rm -rf output/

build_onefile:
	@echo "Building onefile..."
	uv run python -m nuitka $(PROJECT_DIR) $(NUITKA_ARGS) --standalone --onefile --linux-onefile-icon=build/icon.png

build_standalone:
	@echo "Building standalone..."
	uv run python -m nuitka $(PROJECT_DIR) $(NUITKA_ARGS) --standalone

# Development with hot-reload
dev_bot:
	@echo "Starting bot with hot-reload..."
	DEV_RELOAD=true MODE=bot uv run python -m sophie_bot

dev_rest:
	@echo "Starting REST API with hot-reload..."
	DEV_RELOAD=true MODE=rest uv run python -m sophie_bot

dev_scheduler:
	@echo "Starting scheduler with hot-reload..."
	DEV_RELOAD=true MODE=scheduler uv run python -m sophie_bot

fix_code_style:
	uv run python -m pycln . -a
	uv run ruff check . --fix
	uv run ruff format sophie_bot/

test_code_style:
	uv run python -m pycln . -a -c
	uv run ruff format sophie_bot/ --check
	uv run ruff check .

test_codeanalysis:
	# uv run python -m bandit sophie_bot/ -r
	uv run ty check

run_tests:
	uv run python -m pytest tests/ -v --alluredir=allure_results -n auto

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
	uv run python tools/wiki_gen/start.py


# REST API
gen_openapi:
	uv run python tools/openapi_gen/generate.py

api:
	make gen_openapi
	cp openapi.json ../sdash
	cd ../sdash && bun run gen:api
