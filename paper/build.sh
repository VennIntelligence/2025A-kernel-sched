#!/bin/bash
# Build one of the four paper outputs with XeLaTeX.
#
# Usage:
#   bash paper/build.sh en_conf
#   bash paper/build.sh zh_conf
#   bash paper/build.sh en_supp
#   bash paper/build.sh zh_supp
#   bash paper/build.sh all
#   bash paper/build.sh clean
set -euo pipefail

cd "$(dirname "$0")"

targets=(en_conf zh_conf en_supp zh_supp)

clean() {
    rm -rf build dist
    echo "Cleaned paper/build and paper/dist"
}

ensure_dep() {
    local dep="$1"
    if [ ! -f "build/${dep}/${dep}.aux" ]; then
        echo "Building dependency ${dep} first (needed for xr cross-refs)..."
        build_one "${dep}"
    fi
}

build_one() {
    local target="$1"
    local src_dir="src/${target}"
    local out_dir="../../build/${target}"

    if [ ! -f "${src_dir}/main.tex" ]; then
        echo "Unknown paper target: ${target}" >&2
        echo "Valid targets: ${targets[*]} all clean" >&2
        exit 1
    fi

    case "$target" in
        zh_supp) ensure_dep zh_conf ;;
        en_supp) ensure_dep en_conf ;;
    esac

    mkdir -p "build/${target}" dist
    (
        cd "${src_dir}"
        latexmk -r ../../.latexmkrc -xelatex -jobname="${target}" -outdir="${out_dir}" main.tex
    )
    cp "build/${target}/${target}.pdf" "dist/${target}.pdf"
    echo "Built paper/dist/${target}.pdf"
}

case "${1:-}" in
    clean)
        clean
        ;;
    all)
        for target in "${targets[@]}"; do
            build_one "${target}"
        done
        ;;
    en_conf|zh_conf|en_supp|zh_supp)
        build_one "$1"
        ;;
    "")
        echo "Usage: bash paper/build.sh <en_conf|zh_conf|en_supp|zh_supp|all|clean>" >&2
        exit 1
        ;;
    *)
        echo "Unknown paper target: $1" >&2
        echo "Valid targets: ${targets[*]} all clean" >&2
        exit 1
        ;;
esac
