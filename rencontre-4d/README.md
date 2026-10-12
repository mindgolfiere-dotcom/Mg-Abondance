# Rencontre 4D · page de vente, checkout et page merci

Tout est en blocs **Code HTML** à coller dans Systeme.io, avec la même direction artistique que la nouvelle page de vente (Anton + Montserrat + Caveat, prune foncé, orange-rouge, blanc).

```
rencontre-4d/
├── 1-page-de-vente/bloc-page-de-vente.html   → remplace le bloc de la page de vente
├── 2-checkout/bloc-1 … bloc-6                → la page de paiement (6 blocs)
├── 3-merci/bloc-merci.html                    → la page de remerciement
└── apercus/                                   → captures desktop et mobile
```

## Adresses

| Page | Adresse | Remarque |
|---|---|---|
| Checkout | `https://www.mgacademie.fr/rencontre4d-paiement` | les 9 boutons de la page de vente y mènent |
| Merci | `https://www.mgacademie.fr/rencontre4d-bienvenue` | étape suivante du tunnel, la redirection est automatique |

Tu préfères un autre chemin pour le checkout ? Remplace `rencontre4d-paiement` dans `bloc-page-de-vente.html` (9 occurrences, un rechercher/remplacer suffit).

## 1. Page de vente

Dans la page `test-rencontre4d-nouvelle-version`, ouvre l'élément Code HTML existant et remplace **tout** son contenu par `1-page-de-vente/bloc-page-de-vente.html`.

Ce qui change :
- tous les boutons pointent vers le checkout ;
- le prix « waw » dans le hero, la carte d'offre et la section de clôture : **297 € barré à la main** (le trait se dessine à l'écran), **99 € géant**, pastille **−67 %**, « Tu économises 198 € » et un **compte à rebours** jusqu'au dimanche 18 octobre 23h59 ;
- un reflet lumineux et un halo qui pulse sur les boutons principaux ;
- la barre collante mobile affiche ~~297 €~~ **99 €**.

## 2. Checkout (étape « Bon de commande »)

Dans le même tunnel, ajoute une étape **Bon de commande**, chemin `rencontre4d-paiement`, avec la même offre que l'actuelle :
- formule 1 : **99 €** paiement unique ;
- formule 2 : **2 × 55 €** (abonnement limité à 2 paiements) ;
- order bump : **La Vision Claire**.

Mets le fond de page en blanc, puis construis la page ainsi :

| Section | Contenu (dans cet ordre) |
|---|---|
| **1** · pleine largeur | Code HTML ← `bloc-1-haut.html` |
| **2** · une ligne, une colonne | Code HTML ← `bloc-2-entete-formulaire.html`<br>Champ **Prénom** (texte indicatif : « Ton prénom »)<br>Champ **Email** (« Ton adresse email »)<br>**Moyens de paiement**<br>**Prix de l'offre** (il est masqué à l'écran mais doit être présent)<br>**Order bump** : sa description = Code HTML ← `bloc-3-bump-vision-claire.html`<br>Code HTML ← `bloc-4-cgv-total.html`<br>**Bouton de paiement**<br>Code HTML ← `bloc-5-paiement-2-fois.html` |
| **3** · pleine largeur | Code HTML ← `bloc-6-bas.html` |

Textes à saisir dans les éléments natifs :
- **Bouton de paiement** : « Je rejoins Rencontre 4D · 99 € », sous-texte « Paiement unique · Accès à vie », texte de chargement « Paiement en cours… » ;
- **Titre de l'order bump** : « OUI ! J'ajoute La Vision Claire pour 9 € au lieu de 37 € » ;
- n'ajoute pas de titre texte dans la colonne du formulaire, le bloc 2 s'en charge.

Ce qui se fait tout seul :
- la ligne du formulaire devient une carte blanche (bordure orange, ombre), les champs, le bump et le bouton prennent le style de la page ;
- **pas de paiement sans la case CGV cochée** (bouton principal et bouton 2 ×) : la case tremble et passe en rouge ;
- le bouton principal choisit la formule **99 €**, le bouton « Ou payer en 2 × 55 € » choisit la formule **2 fois** (reconnue par son libellé « chaque mois / 2 fois ») puis lance le paiement ;
- le **total** passe de 99 € à 108 € quand le bump est coché, et le bouton 2 × rappelle les 9 € du bump ;
- le compte à rebours se masque après la date de fin.

## 3. Page merci (étape « Page de remerciement »)

Juste après le checkout dans le tunnel, chemin `rencontre4d-bienvenue`. Une section **pleine largeur**, fond blanc, un élément Code HTML ← `3-merci/bloc-merci.html`.

Contenu : « Paiement confirmé », petite pluie de confettis aux couleurs de la page, les 4 étapes d'accès (email, invitation Skool à ne pas traduire, spams / onglet Promotions, introduction avant le Jour 1) et le contact `contact@mgacademie.fr`.

## À vérifier avant la mise en ligne

- **Prix du bump** : 9 €, le prix actuel de La Vision Claire. Si tu en mets un autre, change-le dans `bloc-3` (affichage) et dans `bloc-4` et `bloc-5` (`BUMP = 9`).
- **Fin du prix de lancement** : `2026-10-18T23:59:59+02:00` dans `bloc-page-de-vente.html` et `bloc-1-haut.html`. Après cette date, les comptes à rebours disparaissent mais les prix restent affichés : pense à mettre les pages à jour.
- **Le 297 € barré** est présenté comme le prix après le 18 octobre. Il doit vraiment s'appliquer ensuite, sinon c'est un faux prix barré.
- **Page merci** : la phrase « Tu as aussi ajouté La Vision Claire ? Son accès t'arrive dans un email séparé » suppose que l'accès au mini-cours part dans un email à part. Ajuste-la si ce n'est pas le cas.

## Comment ça a été testé

Chaque bloc a été monté dans les vraies pages Systeme.io (la nouvelle page de vente, le formulaire de paiement actuel de `/rencontre4d` et la page merci actuelle), en desktop (1366 px) et en mobile (390 px), sans aucun débordement horizontal. Sur le formulaire, les clics vers le paiement étaient interceptés avant d'atteindre Systeme.io, donc aucun paiement n'a été lancé :

- clic sur le bouton sans la case CGV → bloqué, case en erreur ;
- case cochée + bouton principal → formule « 99,00 € » sélectionnée ;
- bouton 2 × → formule « 55,00 € chaque mois – 2 fois » sélectionnée ;
- bump coché → total 108 €, bump décoché → retour à 99 €.
