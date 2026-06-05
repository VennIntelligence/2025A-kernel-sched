#!/bin/bash
# Build the paper PDF using latexmk
set -e
cd "$(dirname "$0")"
latexmk -pdf -interaction=nonstopmode main.tex
echo "✅ Paper built: main.pdf"
