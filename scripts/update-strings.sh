#!/bin/bash
LOCALES=$*

# Get newest .py and .ui files so we don't update strings unnecessarily
CHANGED_FILES=0
PYTHON_FILES=$(find . -maxdepth 2 -regex ".*\(ui\|py\)$" -not -path "*/.*" -type f | sort)
for PYTHON_FILE in $PYTHON_FILES
do
  CHANGED=$(stat -c %Y "$PYTHON_FILE")
  if [ "${CHANGED}" -gt "${CHANGED_FILES}" ]
  then
    CHANGED_FILES=${CHANGED}
  fi
done

# Qt translation update
UPDATE=false
for LOCALE in ${LOCALES}
do
  TRANSLATION_FILE="i18n/$LOCALE.ts"
  if [ ! -f "${TRANSLATION_FILE}" ]
  then
    touch "${TRANSLATION_FILE}"
    UPDATE=true
    break
  fi

  MODIFICATION_TIME=$(stat -c %Y "${TRANSLATION_FILE}")
  if [ "${CHANGED_FILES}" -gt "${MODIFICATION_TIME}" ]
  then
    UPDATE=true
    break
  fi
done

if [ "${UPDATE}" = true ]
then
  echo "Translatable sources found:"
  echo "${PYTHON_FILES}"
  echo "Updating translation files:"
  for LOCALE in ${LOCALES}
  do
    echo "Updating i18n/${LOCALE}.ts"
    pylupdate6 --no-obsolete ${PYTHON_FILES} -ts "i18n/${LOCALE}.ts"
  done
else
  echo "Translation files (.ts) are already up to date with sources."
fi
