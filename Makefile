PROJECT_DIR := src/korone

PYTHON := uv run python
PYBABEL := uv run pybabel
ALEMBIC := uv run alembic

ASS_PATH := $(shell $(PYTHON) -c "import ass_tg as _; print(_.__path__[0])")
BABEL_PROJECT := Korone
BABEL_VERSION := $(shell $(PYTHON) -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
BABEL_COPYRIGHT_HOLDER := Hitalo M.
BABEL_MSGID_BUGS_ADDRESS := https://github.com/HitaloM/PyKorone/issues

LOCALES_DIR := $(CURDIR)/locales


locale: extract_lang update_lang compile_lang


new_lang:
	$(PYBABEL) init -i "$(LOCALES_DIR)/korone.pot" -d "$(LOCALES_DIR)" -D korone -l "$(LANG)"

extract_lang:
	$(PYBABEL) extract -k "pl_:1,2" -k "p_:1,2" -k "l_:1" \
	--add-comments="NOTE: " \
	--project "$(BABEL_PROJECT)" \
	--version "$(BABEL_VERSION)" \
	--copyright-holder "$(BABEL_COPYRIGHT_HOLDER)" \
	--msgid-bugs-address "$(BABEL_MSGID_BUGS_ADDRESS)" \
	-o "$(LOCALES_DIR)/bot.pot" --sort-by-file --no-wrap $(PROJECT_DIR)

	cd "$(ASS_PATH)" && \
	$(PYBABEL) extract -k "pl_:1,2" -k "p_:1,2" -k "l_:1" \
	--add-comments="NOTE: " \
	--project "$(BABEL_PROJECT)" \
	--version "$(BABEL_VERSION)" \
	--copyright-holder "$(BABEL_COPYRIGHT_HOLDER)" \
	--msgid-bugs-address "$(BABEL_MSGID_BUGS_ADDRESS)" \
	-o "$(LOCALES_DIR)/ass.pot" --sort-by-file --no-wrap .

	# Merge
	msgcat --use-first --sort-by-file --no-wrap \
		-o "$(LOCALES_DIR)/korone.pot" "$(LOCALES_DIR)/bot.pot" "$(LOCALES_DIR)/ass.pot"

update_lang: extract_lang
	$(PYBABEL) update -d "$(LOCALES_DIR)" -D "korone" -i "$(LOCALES_DIR)/korone.pot" \
	--ignore-pot-creation-date --no-wrap

compile_lang:
	$(PYBABEL) compile -d "$(LOCALES_DIR)" -D "korone" --use-fuzzy --statistics


new_locale:
	rm -rf locales/
	mkdir locales/

	make extract_lang
	make new_lang LANG=en_US
	make update_lang
	make compile_lang


db_upgrade:
	$(ALEMBIC) upgrade head

db_downgrade:
	$(ALEMBIC) downgrade -1

db_revision:
	$(ALEMBIC) revision --autogenerate -m "$(m)"

db_stamp:
	$(ALEMBIC) stamp "$(rev)"
