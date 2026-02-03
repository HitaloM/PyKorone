PROJECT_DIR := src/korone

PYTHON := uv run python
PYBABEL := uv run pybabel

ASS_PATH := $(shell $(PYTHON) -c "import ass_tg as _; print(_.__path__[0])")

LOCALES_DIR := $(CURDIR)/locales


locale: extract_lang update_lang compile_lang


new_lang:
	$(PYBABEL) init -i "$(LOCALES_DIR)/korone.pot" -d "$(LOCALES_DIR)" -D korone -l "$(LANG)"

extract_lang:
	$(PYBABEL) extract -k "pl_:1,2" -k "p_:1,2" -k "l_:1" \
	--add-comments="NOTE: " -o "$(LOCALES_DIR)/bot.pot" --omit-header --sort-by-file --no-wrap $(PROJECT_DIR)

	cd "$(ASS_PATH)" && \
	$(PYBABEL) extract -k "pl_:1,2" -k "p_:1,2" -k "l_:1" \
	--add-comments="NOTE: " -o "$(LOCALES_DIR)/ass.pot" --omit-header --sort-by-file --no-wrap .

	# Merge
	cp "$(LOCALES_DIR)/bot.pot" "$(LOCALES_DIR)/korone.pot"
	cat "$(LOCALES_DIR)/ass.pot" >> "$(LOCALES_DIR)/korone.pot"

update_lang:
	$(PYBABEL) update -d "$(LOCALES_DIR)" -D "korone" -i "$(LOCALES_DIR)/korone.pot" \
	--ignore-pot-creation-date --omit-header --no-wrap

compile_lang:
	$(PYBABEL) compile -d "$(LOCALES_DIR)" -D "korone" --use-fuzzy --statistics


new_locale:
	rm -rf locales/
	mkdir locales/

	make extract_lang
	make new_lang LANG=en_US
	make update_lang
	make compile_lang
