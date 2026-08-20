#!/bin/bash
shopt -s dotglob
AMPY="$(getent passwd "${SUDO_USER:-$(logname)}" | cut -d: -f6)/.local/bin/ampy"
for f in *; do
  if [ $f != "put.sh" ] && [ $f != "run.sh" ] && [ $f != "README.md" ] && [ $f != ".gitignore" ] && [ $f != ".git" ] && [ $f != ".config-template" ]; then
    "$AMPY" --port /dev/$1 put "$f"
  fi
done
