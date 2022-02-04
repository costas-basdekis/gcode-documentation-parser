#!/usr/bin/env bash

set -eo pipefail

poetry run ./update_documentation.py
rm -rf /tmp/output/
cp -r output/ /tmp/
git checkout output
git clean -f -d
rm -rf output/
mv /tmp/output .
git add output/
git commit -m "Update documentation output"
echo git push
