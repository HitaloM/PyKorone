PROJECT_DIR := "sophie_bot"

# Use uv for package management - no need for explicit environment path
PYTHON := "uv"
ASS_PATH := $(shell uv run python -c "import ass_tg as _; print(_.__path__[0])")

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

sync_libs:
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
	uv run python -m pytest tests/ -v --alluredir=allure_results

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


dev_deps:
	# For uv, we need to edit the packages directly in the environment
	# This is a placeholder - uv doesn't have the same editable install pattern as poetry
	@echo "dev_deps target needs to be updated for uv workflow"
	@echo "Consider using 'uv add --editable ../ass' and 'uv add --editable ../stf' instead"

# -----------------------------
# AI-assisted development setup
# -----------------------------

# Source guidelines file
GUIDELINES_SRC := ai_dev/AI_GUIDELINES.md

# List of destinations to copy guidelines to (extendable)
GUIDELINES_DESTS := \
	./.junie/guidelines.md \
	./AI_GUIDELINES.md \
	./AGENTS.md \
	./.kilocode/rules/guidelines.md \
	./.github/AI_GUIDELINES.md

# MCP configuration
MCP_TEMPLATE := ai_dev/mcp.example.json
MCP_DESTS := \
	./.junie/mcp/mcp.json \
	./.kilocode/mcp.json

# MCP keys to inject (format: placeholder -> jq_path)
MCP_KEYS := \
	__CONTEXT7_API_KEY__:.context7.apiKey \
	__TAVILY_API_KEY__:.tavily.apiKey

.PHONY: ai_dev
ai_dev:
	@echo "Setting up AI development environment..."
	@if [ ! -f "$(GUIDELINES_SRC)" ]; then \
		echo "ERROR: $(GUIDELINES_SRC) not found. Please add it and re-run 'make ai_dev'." >&2; \
		exit 1; \
	fi
	@if [ ! -f "data/ai_dev.json" ]; then \
		echo "ERROR: data/ai_dev.json not found. Please create it with your MCP API keys and re-run 'make ai_dev'." >&2; \
		exit 1; \
	fi
	@echo "Copying AI guidelines to destinations..."
	@for dest in $(GUIDELINES_DESTS); do \
		echo " - $$dest"; \
		mkdir -p "$$(dirname "$$dest")"; \
		cp -f "$(GUIDELINES_SRC)" "$$dest"; \
	done
	@echo "Configuring MCP client configurations..."
	@for dest in $(MCP_DESTS); do \
		echo " - $$dest"; \
		mkdir -p "$$(dirname "$$dest")"; \
		cp -f "$(MCP_TEMPLATE)" "$$dest"; \
		# Inject credentials from data/ai_dev.json using MCP_KEYS list \
		sed_args=""; \
		for key_pair in $(MCP_KEYS); do \
			placeholder=$$(echo "$$key_pair" | cut -d: -f1); \
			jq_path=$$(echo "$$key_pair" | cut -d: -f2); \
			value=$$(jq -r "$$jq_path // empty" data/ai_dev.json); \
			if [ -z "$$value" ] || [ "$$value" = "null" ]; then \
				echo "ERROR: data/ai_dev.json missing $$jq_path"; exit 1; \
			fi; \
			sed_args="$$sed_args -e s|$$placeholder|$$value|g"; \
		done; \
		sed -i $$sed_args "$$dest"; \
	done
