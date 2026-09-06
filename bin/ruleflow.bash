#!/bin/bash

# Resolve the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Move to the project src directory relative to the script
cd "$SCRIPT_DIR/../src"

uv run python -m studio.view
