# Synthèse Formations 2026 — Maroc

`Synthese_Formations_2026.pptx` : 2 slides de synthèse pour le MBR.

| Slide | Contenu |
|---|---|
| 1 | Bilan Formations YTD — Janvier à Août 2026 |
| 2 | Plan de Formation Q4 2026 — Septembre à Décembre |

## Chiffres et provenance

Les compteurs YTD sont consolidés mois par mois depuis `MBR_YTD_SEPT_2026.pptx` :

| Mois | Formations partenaires | Visites ophtalmologues | Formations internes |
|---|---|---|---|
| Janvier | 19 | 4 | 2 |
| Février | 14 | 4 | 2 |
| Mars | 19 | 6 | 2 |
| Avril | 18 | 13 | 4 |
| Mai | 13 | 2 | 8 |
| Juin | 16 | 4 | 2 |
| Juillet-Août | 38 | 18 | 4 |
| **Total** | **137** | **51** | **24** |

Soit **212 actions de formation** sur 8 mois.

Les indicateurs non recalculables depuis le MBR (183+ ophtalmologues au Congrès SMO,
8 villes couvertes, 6 Roadshows Kodak, comptes Leonardo) reprennent le bilan
consolidé DOP de `Bilan_et_Plan_Formation_2026.pptx`.

Le plan Q4 (10 sessions : 5 formations internes + 5 webinaires, 7 groupes
partenaires ciblés, challenge Leonardo) reprend également ce même fichier.

## Régénérer le fichier

Le deck est reconstruit dans le template EssilorLuxottica d'origine, ce qui
préserve le masque, le logo, la pagination et la mention de confidentialité.

```bash
pip install python-pptx
# placer Bilan_et_Plan_Formation_2026.pptx dans le dossier, renommé formation.pptx
python3 build_synthese_formations.py
```

Les données sont en haut du script (`PARTENAIRES`, `INTERNES`, `OPHTAS`,
`Q4_INTERNES`, `Q4_WEBINAIRES`, `THEMES`) : il suffit de les mettre à jour pour
régénérer les slides.
