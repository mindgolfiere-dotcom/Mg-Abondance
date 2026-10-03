# Rencontre 4D : nouvelle page de vente + commande (version claire)

Refonte de [mgacademie.fr/rencontre4d](https://www.mgacademie.fr/rencontre4d) au format des pages de Maria Wendt : **le texte de vente et le formulaire de paiement sont sur la même page**. Sur ordinateur, le formulaire est visible dès l'arrivée, à droite. Sur mobile, il arrive juste après le texte, et une barre « Accéder au programme » y mène à tout moment.

La direction artistique ne change pas : titres Oswald en capitales, rose `#FF4371`, badge « Manifestation amoureuse », vidéo encadrée de rose et photos de Zak. Seul le fond passe en clair, un blanc cassé beige `#FAF6F0`.

## Ce qui change

| | Page actuelle | Nouvelle page |
|---|---|---|
| Hauteur sur ordinateur (1440 px) | ~10 460 px | ~4 000 px |
| Hauteur sur mobile (390 px) | ~14 870 px | ~6 500 px |
| Pour payer | page de vente → clic → 2ᵉ page (bon de commande) | formulaire directement sur la page |
| Paiement en 2 fois | bon de commande séparé | choix « 1 fois / 2 fois » dans le même formulaire |

Section par section :

| Page actuelle | Nouvelle page |
|---|---|
| Hero (badge, titre, sous-titre, bouton) | Gardé. Le prix est annoncé dès le haut, comme chez Maria |
| Vidéo « Regarde cette vidéo » (11 min) | Gardée : c'est le visuel principal |
| « Comment ça marche » (3 phases, ~15 paragraphes) | Condensé en 3 puces + 1 puce bonus communauté |
| Bandeau chiffres (1.500+, 28 jours, 4.9, 15 min) | Gardé, en version compacte |
| « Ce que les 28 jours vont changer en toi » (6 cartes) | Supprimé (redit les 3 phases) |
| « Commence dès aujourd'hui » (99 € / 55 € ×2) | Remplacé par le formulaire intégré |
| Témoignages (6) | Gardés, en extraits courts mot pour mot (`[…]` = passage coupé) |
| Avant / Après | Supprimé (couvert par les puces) |
| « Qui est derrière le programme ? » | Gardé, en version courte |
| 2ᵉ bloc de prix « Rejoins Rencontre 4D » | Supprimé : le formulaire est déjà là |
| FAQ (5 questions) | 4 questions repliées + mention « résultats / non remboursable » visible |

Les textes viennent de ta page actuelle, raccourcis. Quelques phrases sont nouvelles : l'accroche avec le prix (« Remplis tes infos et accède immédiatement… »), les pastilles sous le programme, la question « Combien de temps ça me prend ? », l'entête du formulaire et la ligne « En 1 fois, tu économises 11 € ». Elles ne reprennent que des infos déjà présentes sur la page : prix, 28 jours, 15 min par jour, accès à vie, communauté.

## Fichiers

- **`apercu.html`** : la page complète. Ouvre-la dans ton navigateur et réduis la fenêtre pour voir la version mobile. Le bouton « Afficher les repères systeme.io » encadre chaque morceau : en bleu les blocs Code HTML à coller, en vert les éléments natifs de systeme.io (simulés dans l'aperçu).
- **`blocs/`** : un fichier = un élément « Code HTML » à coller dans systeme.io.
- **`build_apercu.py`** : regénère `apercu.html` après la modification d'un bloc (`python3 build_apercu.py`).

| Bloc | Où | Contenu |
|---|---|---|
| `01-hero.html` | colonne gauche | badge, titre, accroche + prix, vidéo, bouton |
| `02-programme.html` | colonne gauche | les 3 phases + bonus, pastilles « débutant / en couple / 15 min » |
| `03-chiffres.html` | colonne gauche | bandeau rose des chiffres |
| `04-temoignages.html` | colonne gauche | les 6 témoignages |
| `05-zak.html` | colonne gauche | « Hello, c'est Zak ! » |
| `06-faq.html` | colonne gauche | 4 questions + mention résultats / remboursement |
| `10-commande-entete.html` | carte formulaire, en haut | « Rejoins Rencontre 4D » + ce qui est inclus. **Porte l'ancre des boutons**, il est obligatoire |
| `11-commande-reassurance.html` | carte formulaire, en bas | paiement sécurisé + mini-témoignage |
| `20-barre-mobile.html` | n'importe où (optionnel) | barre rose en bas de l'écran, sur mobile uniquement |

## Montage dans systeme.io (≈ 30 min)

### 1. Sauvegarde

Dans le tunnel Rencontre 4D, duplique la page de vente actuelle. Tu pourras revenir en arrière en un clic.

### 2. Un seul bon de commande avec les 2 formules

1. Ouvre l'étape **Bon de commande** qui suit `/rencontre4d` (celle du plan à 99 €).
2. Dans ses plans tarifaires, ajoute le plan **2 × 55 €** (paiement en plusieurs fois : 55 € par mois, 2 paiements), à côté du plan **99 €** (paiement unique). Mets le plan 99 € en premier : c'est en général le premier plan qui est coché par défaut (à vérifier à l'étape 7).
3. Change le nom affiché sur le bon de commande des deux plans : « Paiement en 1 fois » et « Paiement en 2 fois ».

> Si systeme.io n'accepte pas les deux plans sur la même étape, garde ta page « 2 fois » actuelle et ajoute sous le bouton de paiement un texte avec un lien : « Tu préfères payer en 2 fois ? Clique ici ».

### 3. Réglages de la page

- Couleur de fond de la page : `#FAF6F0`
- Police du texte : Inter

### 4. Structure de la page

```
Section ─ largeur « large » (1120 px), fond transparent
│         marges internes : 48 / 40 / 72 / 40 px (ordinateur) · 24 / 16 / 40 / 16 px (mobile)
└── Ligne à 2 colonnes : 7 / 5
    ├── Colonne gauche (7)
    │   ├── Code HTML  ←  blocs/01-hero.html
    │   ├── Code HTML  ←  blocs/02-programme.html
    │   ├── Code HTML  ←  blocs/03-chiffres.html
    │   ├── Code HTML  ←  blocs/04-temoignages.html
    │   ├── Code HTML  ←  blocs/05-zak.html
    │   └── Code HTML  ←  blocs/06-faq.html
    └── Colonne droite (5)
        └── Ligne « carte » ─ fond #FFFFFF · bordure 1 px #ECE4D8 · arrondi 20 px
            │                 marges internes 28 / 26 px (mobile 22 / 16 px) · marge gauche 20 px (ordinateur)
            ├── Code HTML  ←  blocs/10-commande-entete.html
            ├── Texte « Prénom* »                  + Champ Prénom        (natif)
            ├── Texte « Email* »                   + Champ Email         (natif)
            ├── Texte « Méthode de paiement* »     + Méthode de paiement (natif)
            ├── Texte « Choisis ta formule »       + Récapitulatif / prix de l'offre (natif, les 2 plans)
            ├── Texte « En 1 fois, tu économises 11 €. »  (rose #D42A5B, 13 px)
            ├── Bouton de paiement                                       (natif)
            ├── Texte « En continuant, j'accepte les termes et conditions »
            ├── Texte « Des questions ? Contactez contact@mgacademie.fr »
            └── Code HTML  ←  blocs/11-commande-reassurance.html

Section pied de page ─ Texte « Copyright © 2022-2026 Tous droits réservés | MG Academy »
                      (gris #6E6668, 13 px, centré) + Code HTML ← blocs/20-barre-mobile.html (optionnel)
```

Pour coller un bloc : glisse un élément **Code HTML**, ouvre ses paramètres, clique sur **Modifier le code**, colle tout le contenu du fichier puis enregistre.

Le plus rapide pour la colonne droite : copie les éléments natifs (Prénom, Email, Méthode de paiement, Récapitulatif, Bouton) depuis ton bon de commande « 2 fois » actuel. Ils sont déjà configurés, il ne reste qu'à changer leurs couleurs (étape 5).

### 5. Couleurs des éléments natifs (version claire)

| Élément | Réglage | Valeur |
|---|---|---|
| Textes au-dessus des champs | couleur, police | `#141213`, Inter 600, 14 px |
| Champs Prénom / Email | fond | `#FFFFFF` |
| | bordure | 1 px `#DCD3C6`, arrondi 10 px |
| | texte / texte indicatif | `#141213` / `#9A918A` |
| Méthode de paiement | couleur du texte | `#141213` |
| Récapitulatif / prix de l'offre | nom du plan | `#141213`, Oswald 700 |
| | montant / description | `#3D3739` / `#6E6668` |
| Bouton de paiement | fond | `#FF4371` |
| | texte | `#FFFFFF`, Oswald 700, 22 px (mobile 18 px), arrondi 12 px |
| | libellé | « ACHETER MAINTENANT » |
| | sous-texte (si l'option existe) | « Accès immédiat au programme » |
| Textes CGV / contact | couleur | `#6E6668` / `#3D3739`, 13 px, centré |

> Garde un verbe d'achat sur le bouton de paiement (« Acheter maintenant »). En Europe, le bouton de commande doit dire clairement que le clic engage à payer, et un simple « Je rejoins » ne suffit pas.

### 6. Garder l'adresse `/rencontre4d`

1. Renomme le chemin d'URL de l'ancienne page de vente, par exemple `rencontre4d-ancienne`.
2. Donne le chemin `rencontre4d` au bon de commande.

Tous tes liens existants (YouTube, emails, bio) arrivent alors directement sur la nouvelle page. Pense à recopier dans le bon de commande les codes de suivi de l'ancienne page (pixel Meta, etc.), dans Paramètres > Tracking.

### 7. Vérifications avant de lancer

- [ ] Les blocs Code HTML ne s'affichent pas dans l'aperçu de l'éditeur, c'est normal : vérifie sur la page publiée.
- [ ] Sur mobile, l'ordre est : titre → vidéo → programme → chiffres → témoignages → Zak → FAQ → formulaire.
- [ ] Les boutons « Accéder au programme » descendent bien jusqu'au formulaire.
- [ ] Sur mobile, la barre rose apparaît quand on descend et disparaît quand le formulaire est à l'écran.
- [ ] « Paiement en 1 fois » est coché par défaut. « Paiement en 2 fois » affiche bien 55 € à payer aujourd'hui.
- [ ] Achat test (mode test Stripe ou coupon à 100 %) : la page de remerciement et l'accès au programme fonctionnent.
- [ ] La vidéo se lance.
- [ ] Le pixel et les codes de suivi sont présents.

## Pour convertir encore plus (optionnel)

1. **Bon de commande en 2 étapes** (élément « two-step order form ») : le prénom et l'email sont enregistrés même si la personne ne paie pas. Ajoute une règle d'automatisation sur « Inscription sur la page » pour lui envoyer un email de relance.
2. **Offre complémentaire (order bump)**, comme Maria : une case à cocher juste avant le bouton, avec un petit produit lié à Rencontre 4D.
3. **Captures d'écran de vrais messages** de la communauté à la place des témoignages tapés : c'est ce que fait Maria, et c'est plus crédible.
4. **Images plus légères** : les PNG actuels pèsent 400–550 Ko. En JPG ou WebP (~80 Ko), la page s'affiche plus vite sur mobile.
5. **Mesurer** : compare ventes ÷ visites de `/rencontre4d` sur 7–14 jours avant et après la mise en ligne.

> Remboursements : en Europe, pour refuser le remboursement d'un produit numérique, le client doit accepter expressément de renoncer à son droit de rétractation au moment de l'achat (souvent une case à cocher). Vérifie que tes CGV et ton bon de commande le prévoient.

## Modifier un texte plus tard

Ouvre le Code HTML concerné, clique sur **Modifier le code** et change le texte entre les balises, sans toucher au bloc `<style>`. Les couleurs sont définies en haut de chaque bloc (`--r4d-pink`, `--r4d-ink`…). Si tu en changes une, change-la dans tous les blocs.
