# Default target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  docs        - Build documentation"
	@echo "  live-docs   - Live preview of documentation"
	@echo "  clean-docs  - Remove built documentation"
	@echo "  i18n-extract - Extract translatable strings"
	@echo "  i18n-update - Update translation files"
	@echo "  i18n-compile - Compile translation files"
	@echo "  i18n-clean  - Remove compiled translation files"
	@echo "  news        - Build changelog with towncrier"
	@echo "  news-draft  - Preview changelog with towncrier"
	@echo "  all         - Build docs and compile translations"
	@echo "  clean       - Clean all build artifacts"

# Documentation targets
.PHONY: clean-docs build-docs docs live-docs
clean-docs:
	rm -rf docs/build

build-docs: clean-docs
	sphinx-build -b html docs/source docs/build

docs: build-docs

live-docs:
	sphinx-autobuild docs/source docs/build --watch src

# Localization targets
.PHONY: i18n-extract i18n-update i18n-compile i18n-clean
i18n-extract:
	pybabel extract --keywords='__ _' --input-dirs=. -o locales/bot.pot

i18n-update: i18n-extract
	pybabel update -i locales/bot.pot -d locales -D bot

i18n-compile:
	pybabel compile -d locales -D bot

i18n-clean:
	find . -name '*.mo' -type f -delete

# Changelog targets
.PHONY: news news-draft
news:
	towncrier build --yes

news-draft:
	towncrier build --draft

# Combined targets
.PHONY: all clean
all: docs i18n-compile

clean: clean-docs i18n-clean
