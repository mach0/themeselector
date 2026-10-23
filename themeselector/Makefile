#/***************************************************************************
# ThemeSelector 
#
# This plugin brings the layer theme settings directly to the desktop
# ---------------------------------------------------------------------------
# Author: Werner Macho
# Email: werner.macho@gmail.com
# ***************************************************************************/

# Add iso code for any locales you want to support here (space separated)
LOCALES = de en

# lrelease binary name or path
LRELEASE ?= lrelease

PLUGINNAME = ThemeSelector

PY_FILES = \
	__init__.py \
	compat.py \
	selector.py \
	selector_dockwidget.py \
	theme_operations.py \
	theme_sync.py \
	utils.py

UI_FILES = selector_dockwidget_base.ui

EXTRAS = metadata.txt LICENSE

BUILD_DIR = build

# QGIS plugin deployment directory (QGIS 3 / QGIS 4 standard location)
QGIS_PLUGIN_DIR ?= $(HOME)/.local/share/QGIS/QGIS3/profiles/default/python/plugins

# Script helper paths (checks local first, then parent repo directory)
COMPILE_SCRIPT = $(shell test -f scripts/compile-strings.sh && echo scripts/compile-strings.sh || echo ../scripts/compile-strings.sh)
UPDATE_SCRIPT = $(shell test -f scripts/update-strings.sh && echo scripts/update-strings.sh || echo ../scripts/update-strings.sh)

default: transcompile

compile: transcompile

transup:
	@echo
	@echo "------------------------------------------------"
	@echo "Updating translation files with any new strings."
	@echo "------------------------------------------------"
	@chmod +x $(UPDATE_SCRIPT)
	@$(UPDATE_SCRIPT) $(LOCALES)

transcompile:
	@echo
	@echo "----------------------------------------"
	@echo "Compiling translation files to .qm files."
	@echo "----------------------------------------"
	@chmod +x $(COMPILE_SCRIPT)
	@$(COMPILE_SCRIPT) $(LRELEASE) $(LOCALES)

transclean:
	@echo
	@echo "------------------------------------"
	@echo "Removing compiled translation files."
	@echo "------------------------------------"
	rm -f i18n/*.qm

deploy: transcompile
	@echo
	@echo "------------------------------------------"
	@echo "Deploying plugin to $(QGIS_PLUGIN_DIR)/$(PLUGINNAME)"
	@echo "------------------------------------------"
	mkdir -p $(QGIS_PLUGIN_DIR)/$(PLUGINNAME)
	cp -vf $(PY_FILES) $(QGIS_PLUGIN_DIR)/$(PLUGINNAME)/
	cp -vf $(UI_FILES) $(QGIS_PLUGIN_DIR)/$(PLUGINNAME)/
	cp -vf $(EXTRAS) $(QGIS_PLUGIN_DIR)/$(PLUGINNAME)/
	cp -vfr img $(QGIS_PLUGIN_DIR)/$(PLUGINNAME)/
	mkdir -p $(QGIS_PLUGIN_DIR)/$(PLUGINNAME)/i18n
	cp -vf i18n/*.qm $(QGIS_PLUGIN_DIR)/$(PLUGINNAME)/i18n/
	@$(MAKE) dclean

dclean:
	@echo
	@echo "-----------------------------------"
	@echo "Removing compiled python files from deployment."
	@echo "-----------------------------------"
	find $(QGIS_PLUGIN_DIR)/$(PLUGINNAME) -iname "*.pyc" -delete 2>/dev/null || true
	find $(QGIS_PLUGIN_DIR)/$(PLUGINNAME) -type d -name "__pycache__" -delete 2>/dev/null || true

derase:
	@echo
	@echo "-------------------------"
	@echo "Removing deployed plugin."
	@echo "-------------------------"
	rm -Rf $(QGIS_PLUGIN_DIR)/$(PLUGINNAME)

zip: transcompile
	@echo
	@echo "---------------------------"
	@echo "Creating plugin zip bundle."
	@echo "---------------------------"
	rm -f $(PLUGINNAME).zip
	rm -rf $(BUILD_DIR)/$(PLUGINNAME)
	mkdir -p $(BUILD_DIR)/$(PLUGINNAME)
	cp -vf $(PY_FILES) $(BUILD_DIR)/$(PLUGINNAME)/
	cp -vf $(UI_FILES) $(BUILD_DIR)/$(PLUGINNAME)/
	cp -vf $(EXTRAS) $(BUILD_DIR)/$(PLUGINNAME)/
	cp -vfr img $(BUILD_DIR)/$(PLUGINNAME)/
	mkdir -p $(BUILD_DIR)/$(PLUGINNAME)/i18n
	cp -vf i18n/*.qm $(BUILD_DIR)/$(PLUGINNAME)/i18n/
	cp -vf i18n/*.ts $(BUILD_DIR)/$(PLUGINNAME)/i18n/
	find $(BUILD_DIR)/$(PLUGINNAME) -iname "*.pyc" -delete
	find $(BUILD_DIR)/$(PLUGINNAME) -type d -name "__pycache__" -delete
	find $(BUILD_DIR)/$(PLUGINNAME) -name ".env*" -delete
	find $(BUILD_DIR)/$(PLUGINNAME) -name "*old_icon*" -delete
	cd $(BUILD_DIR) && zip -9r $(CURDIR)/$(PLUGINNAME).zip $(PLUGINNAME)
	rm -rf $(BUILD_DIR)
	@echo "Created plugin package: $(CURDIR)/$(PLUGINNAME).zip"

package: zip

clean: transclean
	@echo
	@echo "------------------------------------"
	@echo "Removing temporary and build files."
	@echo "------------------------------------"
	rm -rf $(BUILD_DIR) $(PLUGINNAME).zip
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

test: transcompile
	@echo
	@echo "----------------------"
	@echo "Running Plugin Tests"
	@echo "----------------------"
	@PYTHONPATH=..:$(PYTHONPATH) python3 -m unittest discover -s ../test -v
