#!/usr/bin/env bash
# Full pipeline for one clip, from the extracted mezzanines to the QC report.
#   clips/tools/make_clip.sh <project dir> <variant paper|chalk> [title]
# Expects <project>/work/seg/segments.json (locate_segments.py) and <project>/work/spec.json.
set -euo pipefail
P=$(cd "$1" && pwd); VARIANT=${2:-paper}; TITLE=${3:-$(basename "$P")}
ROOT=$(cd "$(dirname "$0")/../.." && pwd); T=$ROOT/clips/tools
cd "$ROOT"
echo "### 1. cut list"
python3 -I "$T/build_cutlist.py" "$P/work/seg/segments.json" "$P/work/spec.json" "$P/work/cutlist.json"
echo "### 2. face track"
python3 -I "$T/render_face.py" --cutlist "$P/work/cutlist.json" --out "$P/work/face.mp4" --out-size 1080x1000 --zoom 0.93
echo "### 3. composition"
python3 -I "$T/build_composition.py" --project "$P" --cutlist "$P/work/cutlist.json" --face "$P/work/face.mp4" --storyboard "$P/storyboard.json" --variant "$VARIANT" --sfx-dir "$ROOT/clips/compositions/_shared/sfx" --title "$TITLE"
echo "### 4. hyperframes check"
(cd "$P" && npx --yes hyperframes@0.8.174 check)
echo "### 5. render"
mkdir -p "$P/out"
(cd "$P" && npx --yes hyperframes@0.8.174 render --quality delivery --output "out/$(basename "$P").mp4")
echo "### 6. QC"
python3 -I "$T/qc.py" all --cutlist "$P/work/cutlist.json" --face "$P/work/face.mp4" --meta "$P/work/face.json" --video "$P/out/$(basename "$P").mp4" --region 0,0,1080,1000 --out "$P/out/qc"
echo "### done: $P/out/$(basename "$P").mp4"
