#!/usr/bin/env bash
# apply_patch.sh [check|apply|revert] [strata|polystrata|split4] [verzeichnis]
# Den einen Groß-Patch auf/ vom Arbeitsbaum. Vor update.sh: revert; danach: apply.
# split4 = All-Cards-Split-Engine, andere Basis (7726f80c / 0.1.59.1), eigene LESEN.md.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
MODE="${1:-check}"
KIND="${2:-strata}"
DIR="${3:-.}"
case "$KIND" in
  strata)     PATCH="$HERE/strata/strata_all.patch" ;;
  polystrata) PATCH="$HERE/polystrata/polystrata_all.patch" ;;
  split4)     PATCH="$HERE/strata_split4/strata_split4_all.patch" ;;
  *) echo "Basis: strata | polystrata | split4"; exit 2 ;;
esac
[ -f "$PATCH" ] || { echo "Patch fehlt: $PATCH"; exit 2; }
cd "$DIR"
case "$MODE" in
  check)  git apply --check "$PATCH" && echo "KP: konfliktfrei auf diesem Stand." ;;
  apply)  git apply "$PATCH" && echo "KP: angewandt (nicht committet).";;
  revert) git apply -R "$PATCH" && echo "KP: zurueckgenommen." ;;
  *) echo "Modus: check | apply | revert"; exit 2 ;;
esac
