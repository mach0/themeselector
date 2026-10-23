# ThemeSelector

[![QGIS Version](https://img.shields.io/badge/QGIS-3.00%20--%204.98-success.svg)](https://qgis.org)
[![Qt Compatibility](https://img.shields.io/badge/Qt-Qt5%20%2F%20Qt6-blue.svg)](https://www.qt.io)
[![License: GPL v2+](https://img.shields.io/badge/License-GPL%20v2%2B-blue.svg)](https://www.gnu.org/licenses/gpl-2.0.html)

**ThemeSelector** brings QGIS map layer theme management directly to your workspace. Switch between saved themes with a single click, cycle through them using keyboard shortcuts, and add, replace, duplicate, or rename themes right from a dockable widget without having to navigate deep nested menus.

---

## Features

- **Instant Theme Switching**: Quickly toggle any saved project map theme from a clean dropdown combo box.
- **Fast Keyboard Navigation**:
  - `Ctrl+Up` / Left Arrow: Switch to previous theme.
  - `Ctrl+Down` / Right Arrow: Switch to next theme.
- **Live Sync Indicator**:
  - Automatically compares current layer visibility against saved theme definitions.
  - Highlights the dropdown in red when canvas visibility differs from any saved theme, letting you know your map view has unsaved changes.
- **Theme Management at Your Fingertips**:
  - **Add**: Save current visible layers as a brand-new theme.
  - **Replace**: Update the active theme definition with whatever is currently visible on the map.
  - **Rename**: Rename the selected theme with instant layout refresh (automatically updates all print layouts using the theme).
  - **Duplicate**: Clone the selected theme as a starting point for variations.
  - **Remove**: Safely delete unwanted themes.
- **Engineered for Performance & Stability**:
  - Uses debounced event handling to eliminate event storms during project save, load, and bulk layer operations.
  - Fully compatible with both **QGIS 3.x (Qt5)** and **QGIS 4.x (Qt6)**.
  - Clean signal connection and disconnection on plugin unload.
- **Internationalization**: Full English and German (`de`) localization included.

---

## Installation

### Via QGIS Plugin Manager (Recommended)
1. In QGIS, navigate to **Plugins** -> **Manage and Install Plugins...**
2. Search for **ThemeSelector**.
3. Click **Install Plugin**.

### Manual Installation
1. Download `ThemeSelector.zip` from the latest release.
2. In QGIS, go to **Plugins** -> **Manage and Install Plugins...** -> **Install from ZIP**.
3. Select the downloaded ZIP file and click **Install Plugin**.

Alternatively, extract the `ThemeSelector` folder directly into your QGIS plugins directory:
- **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/ThemeSelector`
- **macOS**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/ThemeSelector`
- **Windows**: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\ThemeSelector`

---

## User Interface Overview

| Control | Description | Shortcut |
| :--- | :--- | :--- |
| **Prev Theme Button** | Selects previous theme in the list | `Ctrl+Up` |
| **Theme Dropdown** | Displays and selects available map themes | — |
| **Next Theme Button** | Selects next theme in the list | `Ctrl+Down` |
| **Replace** | Overwrites the selected theme with current map visibility | — |
| **Rename** | Renames the current theme and refreshes layout maps | — |
| **Remove** | Deletes the currently selected theme | — |
| **Duplicate** | Duplicates the currently selected theme (`<theme>_copy`) | — |
| **Add** | Creates a new theme from current layer visibility | — |

---

## Development & Build Automation

A comprehensive `Makefile` is provided in the `themeselector` directory for testing, compiling translations, local deployment, and packaging.

```bash
cd themeselector

# Compile translation files (.ts -> .qm)
make transcompile

# Extract translatable strings from all source and UI files into .ts
make transup

# Deploy plugin to local QGIS 3/4 plugin directory
make deploy

# Build release zip package for plugins.qgis.org
make zip

# Run the test suite
make test

# Clean compiled translation and build files
make clean
```

---

## Translations

ThemeSelector supports Qt's internationalization system (`.ts` and `.qm` files stored in `i18n/`).

To update or add translations:
1. Run `make transup` to update `.ts` files from source code.
2. Open the `.ts` file (e.g. `i18n/de.ts`) in [Qt Linguist](https://wiki.qt.io/Qt_Linguist) or a text editor and provide the translations.
3. Run `make transcompile` to compile `.ts` into `.qm` binary files.

---

## Changelog

See `metadata.txt` for the complete version history.

- **v4.0.1**:
  - Full Qt5 and Qt6 dual compatibility (QGIS 3.x and QGIS 4.x).
  - Robust locale detection fallback when `userLocale` is not set in settings.
  - Safe signal lifecycle management: prevented duplicate layer connections and guaranteed clean unload.
  - Fixed double-trigger on keyboard shortcut theme cycling.
  - Updated translation pipeline to extract all dialog strings; complete German translation update.
  - Streamlined Makefile with automated release packaging and modernized unit tests.
- **v4.0.0**:
  - QGIS 4 compatibility overhaul and debounced UI updates.

---

## License & Credits

- **Author**: Werner Macho für Wagner-IT ([werner.macho@gmail.com](mailto:werner.macho@gmail.com))
- **Homepage**: [https://github.com/mach0/themeselector](https://github.com/mach0/themeselector)
- **Bug Tracker**: [https://github.com/mach0/themeselector/issues](https://github.com/mach0/themeselector/issues)
- **License**: GNU General Public License Version 2 or later ([LICENSE](LICENSE))
