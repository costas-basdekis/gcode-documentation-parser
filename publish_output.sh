#!/usr/bin/env bash

set -eox pipefail

poetry run ./update_documentation.py
rm -rf /tmp/output/
cp -r output/ /tmp/
git fetch --depth=1
git switch output
git clean -f -d
rm -rf output/
mv /tmp/output .
git add output/
git commit -m "Update documentation output"
echo git push
