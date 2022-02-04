#!/usr/bin/env bash

set -eo pipefail

DOCS_PREFIX="https://raw.githubusercontent.com/costas-basdekis/gcode-documentation-parser/main/"
README_FILE="README.md"
BUILD_NAME="gcode-documentation-parser-$(poetry version --short)"
TAR_FILE="${BUILD_NAME}.tar"
TAR_GZ_FILE="${TAR_FILE}.gz"

poetry build
cp ./dist/${TAR_GZ_FILE} /tmp/${TAR_GZ_FILE}
cd /tmp
gunzip /tmp/${TAR_GZ_FILE} --force
tar -xvf /tmp/${TAR_FILE} ${BUILD_NAME}/${README_FILE}
sed -i -E 's$(\()(docs/)$\1'"$DOCS_PREFIX"'\2$g' /tmp/${BUILD_NAME}/${README_FILE}
tar -vf /tmp/${TAR_FILE} --delete ${BUILD_NAME}/${README_FILE}
tar -rf /tmp/${TAR_FILE} ${BUILD_NAME}/${README_FILE}
gzip /tmp/${TAR_FILE}
cd -
cp /tmp/${TAR_GZ_FILE} ./dist/${TAR_GZ_FILE}
poetry publish --username costas-basdekis
