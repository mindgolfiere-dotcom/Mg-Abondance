# Automatisation ManyChat — mot-clé « ABONDANCE » (et routage Rencontre 4D)

L'API publique ManyChat ne crée pas de flows ni de déclencheurs par commentaire : cette fiche décrit l'automatisation bloc par bloc pour la construire dans l'interface (10 minutes), ou pour que je la construise moi-même si un navigateur est connecté à la session.

## Liens à renseigner

| Variable | Valeur |
|---|---|
| `SKOOL_URL` | page Skool MG Abondance (1re semaine gratuite) : **à fournir** |
| `R4D_URL` | page de vente Rencontre 4D : **à fournir** |
| Compte Instagram | @zakblanjardins (Zak \| MG Meditation), déjà relié à vidIQ |

## Règle de routage par sujet

| Sujet du clip | Mot-clé à commenter | Flow | Destination |
|---|---|---|---|
| Abondance, manifestation, argent, business | **ABONDANCE** | `IG · Commentaire ABONDANCE` | `SKOOL_URL` |
| Amour, rencontre, relationnel | **RENCONTRE** | `IG · Commentaire RENCONTRE` | `R4D_URL` |

Les deux clips de cette série (cerveau « un peu con », génie de la lampe) parlent de manifestation : ils utilisent **ABONDANCE**.

## Flow « IG · Commentaire ABONDANCE »

**Déclencheur** : Automation → New Automation → Instagram → *User comments on your Post or Reel*.
- Posts : *Specific posts* → sélectionner les deux Reels (ou *All posts* si tu veux réutiliser le mot-clé partout).
- Comment contains : `abondance` (ManyChat ignore la casse ; ajouter les variantes `abundance`, `abondanc`, `abondance!`).
- Exclude : rien.
- *Who can trigger* : Everyone. *Frequency* : Once per user per post.

**Réponse publique au commentaire** (Comment reply, aléatoire parmi 3) :
1. `Je t'ai envoyé l'accès en DM 📩`
2. `C'est parti, regarde tes messages 🙌`
3. `Envoyé ! Check tes DM 👀`

**DM 1 (Private reply, envoyé immédiatement)** :
> Hey {{first_name}} 👋 Tu as commenté ABONDANCE sous mon Reel.
> Je t'ouvre l'accès à MG Abondance : 1re semaine gratuite, tu regardes tout, zéro engagement.
> Clique ici pour que je te l'envoie 👇
>
> [Bouton] **Recevoir mon accès** → action : *Go to next step* (le clic ouvre la fenêtre de 24 h et autorise la suite)

**DM 2 (après le clic)** :
> Voici ton accès 👉 `SKOOL_URL`
> À l'intérieur : les exercices guidés visualisation + émotion, et les victoires des membres chaque jour.
> Commence par la vidéo « Bienvenue » (4 min), puis l'exercice du matin.
>
> [Bouton] **Ouvrir MG Abondance** → URL `SKOOL_URL` (tracking activé)

Actions à la fin de DM 2 : *Add tag* `lead-abondance`, *Add tag* `src-reel-{{nom du reel}}`, *Set custom field* `last_keyword = ABONDANCE`, *Set custom field* `last_offer = MG Abondance`.

**Relance 1** (Smart delay 6 h, condition : n'a pas cliqué le bouton « Ouvrir ») :
> Tu as vu le lien ? Pour que la semaine gratuite démarre, il faut juste cliquer ici 👇 `SKOOL_URL`
> Si tu as une question sur ce qu'il y a dedans, réponds-moi ici, je lis tout.

**Relance 2** (Smart delay 16 h après la relance 1, même condition, dernière dans la fenêtre de 24 h) :
> Dernier rappel : la semaine gratuite t'attend, ce message expire ce soir 🙂 `SKOOL_URL`

Si l'utilisateur ne clique jamais sur « Recevoir mon accès », aucune relance ne peut partir (règle Instagram des 24 h : seule la Private reply est autorisée sans interaction). C'est voulu : le bouton de DM 1 sert justement à obtenir l'interaction.

## Flow « IG · Commentaire RENCONTRE »

Identique, avec : mot-clé `rencontre` (variantes `amour`, `relation`), DM 1 orienté relationnel
(« Tu as commenté RENCONTRE… je t'envoie Rencontre 4D »), DM 2 vers `R4D_URL`, tags `lead-rencontre`, custom field `last_offer = Rencontre 4D`.

## Réglages globaux à vérifier

- Settings → Instagram : compte connecté, *Comment automation* activé, permission « messages » accordée lors de la reconnexion.
- Settings → Growth Tools : désactiver tout autre déclencheur sur les mêmes mots-clés pour éviter les doubles DM.
- Live Chat : prévoir une réponse humaine aux réponses libres (les gens répondent souvent « ABONDANCE » dans le DM lui-même : ajouter un *Keyword* « abondance » en DM qui renvoie DM 2).
- Default reply : désactivé pendant la campagne, ou réglé pour renvoyer vers DM 2.

## Test avant publication

1. Commenter « abondance » depuis un compte test sous le Reel (en brouillon privé ou juste après publication).
2. Vérifier : réponse publique, DM 1 reçu, bouton → DM 2 avec le lien correct, tags posés dans le contact.
3. Ne pas cliquer « Ouvrir » et vérifier la relance 1 au bout de 6 h.
4. Vérifier les stats du flow (Sent / Delivered / Clicked) après 24 h, puis le taux commentaire → clic Skool.

## Mesure

- Objectif de conversion suivi : commentaires ABONDANCE → clics `SKOOL_URL` (ManyChat) → inscriptions Skool (comparer avec le nombre de nouveaux membres sur la période).
- Les deux clips portent un tag `src-reel-…` distinct pour comparer la variante tableau noir et la variante papier.
