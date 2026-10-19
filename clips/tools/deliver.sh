#!/usr/bin/env bash
# Package a rendered clip for delivery: a lighter H.264 encode (Instagram re-encodes anyway), its SRT, the QC report
# and the contact sheet, under clips/deliveries/<name>/.
#   clips/tools/deliver.sh <project dir> <delivery name>
set -euo pipefail
P=$(cd "$1" && pwd); NAME=$2
ROOT=$(cd "$(dirname "$0")/../.." && pwd); D="$ROOT/clips/deliveries/$NAME"; mkdir -p "$D"
SRC="$P/out/$(basename "$P").mp4"
ffmpeg -y -v error -i "$SRC" -c:v libx264 -preset slow -crf 19 -pix_fmt yuv420p -profile:v high -level 4.1 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$D/$NAME.mp4"
cp "$P/captions.srt" "$D/$NAME.srt"
cp "$P/out/qc/qc_report.md" "$D/$NAME-qc.md"
cp "$P/out/qc/cuts_sheet.png" "$D/$NAME-cuts.png" 2>/dev/null || true
python3 -I "$ROOT/clips/tools/preview_grid.py" "$D/$NAME.mp4" "$D/$NAME-planche.png" --every 4 --cols 6 --width 240 >/dev/null
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate:format=duration,size -of default=nw=1 "$D/$NAME.mp4" | tr '\n' ' '; echo
ls -la "$D"
