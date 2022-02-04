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
if git diff --cached --exit-code >/dev/null ; then
  echo "No changes to commit"
  exit 0
fi
git commit -m "Update documentation output"
git push
