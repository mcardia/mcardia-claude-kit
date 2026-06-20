#!/usr/bin/env sh
# Snapshot the SDD generators into a target project's _generators/ directory.
#
# Usage: ./bootstrap.sh /path/to/project
#
# Copies the numbered generator prompts (01-..08-) into <project>/_generators/.
# The project gets a frozen snapshot; this repo keeps evolving independently.
# Remember to add '_generators/' to the project's .gitignore.

set -eu

target="${1:?usage: bootstrap.sh /path/to/project}"
src="$(cd "$(dirname "$0")" && pwd)"
dest="$target/_generators"

mkdir -p "$dest"
cp "$src"/[0-9][0-9]-*.md "$dest"/

echo "Copied SDD generators to $dest"
echo "If it is not already there, add '_generators/' to $target/.gitignore"
