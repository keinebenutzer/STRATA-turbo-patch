#!/usr/bin/env bash
# apply_patch.sh [check|apply|revert] [strata|polystrata] [verzeichnis]
# Den einen Groß-Patch auf/ vom Arbeitsbaum. Vor update.sh: revert; danach: apply.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
MODE="${1:-check}"
KIND="${2:-strata}"
DIR="${3:-.}"
case "$KIND" in
  strata)     PATCH="$HERE/strata/strata_all.patch" ;;
  polystrata) PATCH="$HERE/polystrata/polystrata_all.patch" ;;
  *) echo "Basis: strata | polystrata"; exit 2 ;;
esac
[ -f "$PATCH" ] || { echo "Patch fehlt: $PATCH"; exit 2; }
cd "$DIR"
case "$MODE" in
  check)  git apply --check "$PATCH" && echo "KP: konfliktfrei auf diesem Stand." ;;
  apply)  git apply "$PATCH" && echo "KP: angewandt (nicht committet).";;
  revert) git apply -R "$PATCH" && echo "KP: zurueckgenommen." ;;
  *) echo "Modus: check | apply | revert"; exit 2 ;;
esac
