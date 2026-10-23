#!/bin/bash
LRELEASE=$1
shift 1
LOCALES="$*"

for LOCALE in ${LOCALES}
do
    echo "Processing: ${LOCALE}.ts"
    $LRELEASE i18n/${LOCALE}.ts
done
