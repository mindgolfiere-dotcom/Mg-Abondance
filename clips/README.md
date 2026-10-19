# Clips verticaux MG Méditation — pipeline de clipping

Objectif : des Reels 9:16 de 60 à 90 s découpés dans les vidéos YouTube longues, avec la tête face caméra en haut, une animation dessinée à la main en bas, synchronisée mot à mot, des sous-titres à la jonction, le respect de la safe zone Instagram, et une conclusion sur un CTA mot-clé (ManyChat).

## Dossiers

| Dossier | Contenu |
|---|---|
| `clipping/` | scripts de clipping (passages retenus, logique hook → développement → CTA) |
| `storyboards/` | notes de mise en scène (les storyboards exécutables sont dans `compositions/<clip>/storyboard.json`) |
| `tools/` | outils Python du pipeline (voir ci-dessous) |
| `compositions/_shared/` | moteur d'animation (`engine.js`, `interpreter.js`), polices, effets sonores (non versionnés, voir `sfx/manifest.json`) |
| `compositions/<clip>/` | projet HyperFrames d'un clip : `storyboard.json`, `index.html` généré, `plan.json`, `captions.srt`, `assets/` |
| `manychat/` | fiche de build de l'automatisation ManyChat |
| `qc/` | rapports de contrôle qualité post-rendu |

## Étapes

```bash
# 0. Pré-requis (déjà faits dans la session cloud) : ffmpeg, python3 + faster-whisper, opencv-python-headless, scikit-image, node 22
# 1. Transcription mot à mot du master
python3 -I clips/tools/transcribe.py master.mp4 master_words.json
# 2. Localisation des passages + extraction des mezzanines (sans perte, toutes images clés, PCM) + re-transcription
python3 -I clips/tools/locate_segments.py --src master.mp4 --words master_words.json --spec spec.json --out-dir work/seg --transcribe
# 3. Cut list : ancres de texte → index d'images, coupe de toute pause > 0,25 s, sous-titres re-synchronisés
python3 -I clips/tools/build_cutlist.py work/seg/segments.json spec.json work/cutlist.json
# 4. Piste visage : coupes exactes, cadrage automatique sur le visage (YuNet), micro-fondus audio
python3 -I clips/tools/render_face.py --cutlist work/cutlist.json --out work/face.mp4 --out-size 1080x1000 --zoom 1.25
# 5. Composition HyperFrames (visage + tableau + sous-titres + SFX + CTA plein écran)
python3 -I clips/tools/build_composition.py --project clips/compositions/clip1-cerveau --cutlist work/cutlist.json --face work/face.mp4 --storyboard clips/compositions/clip1-cerveau/storyboard.json
cd clips/compositions/clip1-cerveau && npx hyperframes check && npx hyperframes render --quality delivery --output out/clip1.mp4
# 6. Contrôle qualité APRÈS rendu (images parasites, silences, durée, loudness, planche des cuts)
python3 -I clips/tools/qc.py all --cutlist work/cutlist.json --face work/face.mp4 --meta work/face.json --video out/clip1.mp4 --region 0,0,1080,1000 --out out/qc
```

`spec.json` décrit les segments par ancres de texte (voir l'en-tête de `build_cutlist.py`). `storyboard.json` décrit les scènes et actions avec des ancres `SEG:mot` (voir l'en-tête de `build_composition.py`). `fake_cutlist.py` fabrique un timing synthétique à partir du script pour travailler la mise en page avant d'avoir les masters.

## Règles appliquées

- Aucune pause de plus de 0,25 s : toute pause plus longue est ramenée à 0,18 s de son d'ambiance réel (jamais de silence numérique).
- Coupes sur la grille d'images des mezzanines ; le QC compare l'image avant et après chaque cut avec les images sources prévues (SSIM) et vérifie que l'image après le cut ne ressemble jamais à la première image supprimée.
- Détection d'images orphelines sur le rendu final (une image qui diffère fortement de ses deux voisines alors qu'elles se ressemblent).
- Safe zone Instagram : éléments critiques dans x 108-860 / y 270-1500 ; dégradés vers le noir masqués en douceur sur le bord droit et le bas ; l'outil de build avertit quand une action du storyboard sort de la zone.
- Déterminisme du rendu : aucune valeur aléatoire non seedée ; chaque tremblement de trait vient d'un générateur seedé.
- Aucune musique de fond ; effets sonores Epidemic Sound seulement, un par événement visuel.

## Rushs Shade (sources réelles)

Les rushs sont sur un partage public Shade (`https://app.shade.inc/publish/<share_id>/`). Deux outils :

- `python3 -I clips/tools/shade_links.py <url du partage> [--filter "Rush 8" ...] [--all] [--out liens.md]` : liste les fichiers et imprime des liens de téléchargement **SOURCE** signés (valables 24 h), plus les commandes `curl -C -` pour les gros fichiers. Aucune clé n'est nécessaire, le partage est public.
- `python3 -I clips/tools/shade_words.py <transcription Shade .json> <words.json> --media <url>` : convertit la transcription Shade (mots en ms, prises ratées incluses) au format `words.json` du pipeline. Elle sert à **localiser** les passages ; le minutage fin vient de la re-transcription Whisper de chaque mezzanine (`locate_segments.py --transcribe`).

`locate_segments.py` accepte une URL signée comme `--src` (ffmpeg lit par requêtes de plage, rien n'est téléchargé en entier), `--fps 30` pour ramener un rush 60 fps à 30 fps, et `--takes` : quand un passage a été refait plusieurs fois, la prise retenue est celle dont le texte est le plus proche du champ `expected` du spec (égalité → la dernière prise).

Rushs identifiés (transcriptions comparées) :

| Vidéo YouTube | Rush Shade | Détails |
|---|---|---|
| Comment fonctionne VRAIMENT la manifestation (VD3J4KMotWM) | `2026-09-25 09-51-23.mp4` (asset `0e0d6a23-…`) | OBS, 1920×1080 60 fps HEVC, 48 min, 15,4 Go ; + `Screenrecorder-…` (tableau blanc) |
| Manifestation Rapide : Possible en 24h ? (3ST8wdLa5pg) | `Rush 8.mp4` (asset `f30a0179-…`) | 1920×1080 60 fps HEVC, 53 min, 16,8 Go ; `Rush 8 cam2.mp4` = 2e angle 4K 30 fps |
