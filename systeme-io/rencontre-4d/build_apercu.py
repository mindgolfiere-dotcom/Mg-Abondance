"""Assemble apercu.html from the paste-ready blocks (run: python3 build_apercu.py).

The preview reproduces the systeme.io page structure (section > 7/5 row > columns,
raw-HTML wrappers with their centered text) so the blocks are tested as they will
render, and simulates the native order-form elements in the right column.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BLOCS = ROOT / 'blocs'


def block(name: str) -> str:
    return (BLOCS / name).read_text(encoding='utf-8').strip()


def slot(name: str, label: str | None = None) -> str:
    label = label or f'Code HTML · {name}'
    return (
        f'<div class="pv-slot" data-label="{label}">'
        f'<div class="sio-rawhtml">\n{block(name)}\n</div></div>'
    )


NATIVE_FORM = """
<div class="pv-slot pv-native" data-label="Éléments natifs systeme.io (champs, paiement, formule, bouton)">
  <div class="pv-form" aria-label="Simulation du formulaire de commande systeme.io">
    <p class="pv-label">Prénom*</p>
    <div class="pv-input">Ton prénom</div>
    <p class="pv-label">Email*</p>
    <div class="pv-input">Ton adresse email</div>

    <p class="pv-label">Méthode de paiement*</p>
    <div class="pv-pay">
      <div class="pv-pay-head">
        <span class="pv-radio is-on" aria-hidden="true"></span>
        <span>Carte de crédit</span>
        <span class="pv-brands" aria-hidden="true"><i>VISA</i><i>MC</i><i>AMEX</i></span>
      </div>
      <div class="pv-pay-body">
        <div class="pv-applepay">Apple&nbsp;Pay</div>
        <p class="pv-label pv-label-sm">Numéro de carte*</p>
        <div class="pv-input">1234 1234 1234 1234</div>
        <div class="pv-two">
          <div><p class="pv-label pv-label-sm">Date d’expiration*</p><div class="pv-input">MM / AA</div></div>
          <div><p class="pv-label pv-label-sm">Code de sécurité*</p><div class="pv-input">CVC</div></div>
        </div>
      </div>
    </div>

    <p class="pv-label">Choisis ta formule</p>
    <div class="pv-offer">
      <button type="button" class="pv-plan is-on" data-today="99,00 €" data-total="">
        <span class="pv-radio" aria-hidden="true"></span>
        <span class="pv-plan-name">Paiement en 1 fois</span>
        <span class="pv-plan-price">99,00 €</span>
      </button>
      <button type="button" class="pv-plan" data-today="55,00 €" data-total="110,00 €">
        <span class="pv-radio" aria-hidden="true"></span>
        <span class="pv-plan-name">Paiement en 2 fois</span>
        <span class="pv-plan-price">55,00 € chaque mois – 2 fois</span>
      </button>
      <div class="pv-sum"><span>À payer aujourd’hui</span><strong data-pv-today>99,00 €</strong></div>
      <div class="pv-sum pv-sum-total" data-pv-total-row hidden><span>Total après tous les paiements</span><strong data-pv-total>110,00 €</strong></div>
    </div>
    <p class="pv-hint">En 1 fois, tu économises 11&nbsp;€.</p>

    <div class="pv-paybtn">Acheter maintenant<small>Accès immédiat au programme</small></div>
    <p class="pv-cgv">En continuant, j’accepte les <u>termes et conditions</u></p>
    <p class="pv-contact">Des questions&nbsp;? Contactez <strong>contact@mgacademie.fr</strong></p>
  </div>
</div>
"""

SHELL = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Rencontre 4D — Aperçu</title>
<meta name="description" content="Aperçu de la nouvelle page de vente-commande Rencontre 4D (version claire), assemblée à partir des blocs Code HTML systeme.io.">
<style>
/* --- Reset global repris de systeme.io --- */
html{box-sizing:border-box;scroll-behavior:smooth;-webkit-text-size-adjust:100%;text-size-adjust:100%}
body{margin:0;background:#FAF6F0}
*,*:before,*:after{box-sizing:inherit}
a{text-decoration:none}
p{margin:0}
h1,h2,h3,h4,h5,h6{margin:0;font-weight:normal}
ul{margin:0}

/* --- Structure systeme.io : section > ligne 12 colonnes > colonnes 7/5 --- */
.sio-section{display:flex;position:relative;padding:48px 40px 72px}
.sio-container{max-width:1120px;width:100%;margin:auto}
.sio-row{display:grid;grid-template-columns:repeat(12,1fr);column-gap:20px;padding:0 10px}
.sio-col-left{grid-column:1 / 8;align-self:flex-start;display:flex;flex-direction:column;min-width:0}
.sio-col-right{grid-column:8 / 13;align-self:flex-start;display:flex;flex-direction:column;min-width:0}
.sio-rawhtml{min-height:20px;text-align:center}   /* wrapper que systeme.io met autour de chaque Code HTML */
.sio-card{margin-left:20px;padding:28px 26px;background:#fff;border:1px solid #ECE4D8;border-radius:20px;box-shadow:0 1px 2px rgba(20,18,19,.04),0 24px 48px -30px rgba(20,18,19,.28);display:flex;flex-direction:column;gap:22px}
.sio-footer{padding:22px 16px 28px;border-top:1px solid #ECE4D8;text-align:center;font-family:'Inter',system-ui,sans-serif;font-size:13px;color:#6E6668}
@media only screen and (max-width:800px){
  .sio-section{padding:24px 16px 40px}
  .sio-row{display:flex;flex-direction:column;padding:0}
  .sio-col-left,.sio-col-right{align-self:unset;width:100%}
  .sio-card{margin-left:0;padding:22px 16px}
  .sio-footer{padding-bottom:96px}
}

/* --- Simulation des éléments natifs du bon de commande --- */
.pv-form{font-family:'Inter',system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;color:#141213;text-align:left;display:flex;flex-direction:column}
.pv-label{margin:16px 0 7px;font-size:14px;font-weight:600;line-height:1.3;color:#141213}
.pv-form > .pv-label:first-child{margin-top:0}
.pv-label-sm{margin-top:12px;font-size:13px;font-weight:500;color:#3D3739}
.pv-input{display:flex;align-items:center;height:50px;padding:0 14px;background:#fff;border:1px solid #DCD3C6;border-radius:10px;font-size:16px;color:#9A918A}
.pv-pay{border:1px solid #DCD3C6;border-radius:10px;overflow:hidden}
.pv-pay-head{display:flex;align-items:center;gap:10px;padding:14px;border-bottom:1px solid #ECE4D8;font-size:15px;font-weight:500}
.pv-brands{display:flex;gap:4px;margin-left:auto}
.pv-brands i{padding:3px 5px;border:1px solid #E3DACD;border-radius:4px;font-size:9px;font-style:normal;font-weight:800;letter-spacing:.3px;color:#3D3739}
.pv-pay-body{padding:14px}
.pv-applepay{display:flex;align-items:center;justify-content:center;height:44px;border-radius:8px;background:#000;color:#fff;font-size:16px;font-weight:600}
.pv-two{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.pv-radio{flex:none;display:inline-block;width:18px;height:18px;border:2px solid #CFC5B8;border-radius:50%;background:#fff}
.pv-radio.is-on,.pv-plan.is-on .pv-radio{border-color:#FF4371;box-shadow:inset 0 0 0 3px #fff;background:#FF4371}
.pv-offer{display:flex;flex-direction:column;gap:8px;padding:10px;background:#FBF8F4;border:1px solid #ECE4D8;border-radius:12px}
.pv-plan{display:grid;grid-template-columns:auto 1fr;grid-template-areas:"r n" "r p";column-gap:12px;row-gap:2px;align-items:center;width:100%;padding:12px 14px;text-align:left;background:#fff;border:1.5px solid #E3DACD;border-radius:10px;cursor:pointer;font:inherit;color:inherit}
.pv-plan .pv-radio{grid-area:r}
.pv-plan-name{grid-area:n;font-family:'Oswald',Impact,sans-serif;font-size:16px;font-weight:700;letter-spacing:.4px;text-transform:uppercase;color:#141213}
.pv-plan-price{grid-area:p;font-size:14px;font-weight:600;color:#3D3739}
.pv-plan.is-on{border-color:#FF4371;background:#FFF6F8}
.pv-plan:focus-visible{outline:3px solid #141213;outline-offset:2px}
.pv-sum{display:flex;justify-content:space-between;gap:12px;padding:4px 6px 0;font-size:14px;font-weight:600}
.pv-sum[hidden]{display:none}
.pv-sum-total{padding-top:0;font-size:13px;font-weight:500;color:#6E6668}
.pv-hint{margin-top:8px;font-size:12.5px;font-weight:600;color:#D42A5B}
.pv-paybtn{display:flex;flex-direction:column;align-items:center;gap:4px;margin-top:22px;padding:16px;border-radius:12px;background:#FF4371;color:#fff;font-family:'Oswald',Impact,sans-serif;font-size:22px;font-weight:700;letter-spacing:.8px;line-height:1.2;text-transform:uppercase;box-shadow:0 14px 28px -12px rgba(255,67,113,.8)}
.pv-paybtn small{font-family:'Inter',system-ui,sans-serif;font-size:13px;font-weight:500;letter-spacing:0;text-transform:none;color:rgba(255,255,255,.92)}
.pv-cgv{margin-top:12px;font-size:12.5px;text-align:center;color:#6E6668}
.pv-contact{margin-top:6px;font-size:13px;text-align:center;color:#3D3739}

/* --- Repères : montre quel morceau est un bloc Code HTML et lequel est natif --- */
.pv-slot{position:relative}
.pv-guides .pv-slot{outline:2px dashed #2F6FEB;outline-offset:4px}
.pv-guides .pv-native{outline-color:#16A34A}
.pv-guides .pv-slot::before{content:attr(data-label);position:absolute;z-index:5;top:-2px;right:-2px;max-width:92%;padding:3px 8px;border-radius:0 0 0 8px;background:#2F6FEB;color:#fff;font:600 11px/1.4 'Inter',system-ui,sans-serif;text-align:right;pointer-events:none}
.pv-guides .pv-native::before{background:#16A34A}
.pv-bar{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px 16px;padding:10px 16px;background:#EFE7DB;border-bottom:1px dashed #CFC5B8;font:500 12.5px/1.4 'Inter',system-ui,sans-serif;color:#3D3739}
.pv-bar b{display:inline-block;margin-right:8px;padding:3px 8px;border-radius:999px;background:#141213;color:#fff;font-size:10.5px;font-weight:700;letter-spacing:1px;text-transform:uppercase}
.pv-toggle{display:inline-flex;align-items:center;gap:8px;padding:7px 12px;border:1px solid #CFC5B8;border-radius:999px;background:#fff;font:600 12px/1 'Inter',system-ui,sans-serif;color:#141213;cursor:pointer}
.pv-toggle::before{content:"";width:10px;height:10px;border-radius:50%;background:#CFC5B8}
.pv-toggle[aria-pressed="true"]::before{background:#2F6FEB}
.pv-toggle:focus-visible{outline:3px solid #2F6FEB;outline-offset:2px}
</style>
</head>
<body>
<div class="pv-bar"><p><b>Aperçu</b>Rencontre 4D · page de vente + commande en 1 étape (version claire)</p><button class="pv-toggle" type="button" aria-pressed="false">Afficher les repères systeme.io</button></div>

<section class="sio-section">
  <div class="sio-container">
    <div class="sio-row">
      <div class="sio-col-left">
__LEFT__
      </div>
      <div class="sio-col-right">
        <div class="sio-card">
__RIGHT__
        </div>
      </div>
    </div>
  </div>
</section>
<div class="sio-footer">Copyright © 2022-2026 Tous droits réservés | MG Academy</div>

__STICKY__

<script>
(function () {
  var toggle = document.querySelector('.pv-toggle');
  toggle.addEventListener('click', function () {
    var on = document.body.classList.toggle('pv-guides');
    toggle.setAttribute('aria-pressed', on ? 'true' : 'false');
    toggle.textContent = on ? 'Masquer les repères systeme.io' : 'Afficher les repères systeme.io';
  });
  var plans = document.querySelectorAll('.pv-plan');
  var today = document.querySelector('[data-pv-today]');
  var totalRow = document.querySelector('[data-pv-total-row]');
  var total = document.querySelector('[data-pv-total]');
  plans.forEach(function (plan) {
    plan.addEventListener('click', function () {
      plans.forEach(function (p) { p.classList.toggle('is-on', p === plan); });
      today.textContent = plan.dataset.today;
      totalRow.hidden = !plan.dataset.total;
      if (plan.dataset.total) total.textContent = plan.dataset.total;
    });
  });
})();
</script>
</body>
</html>
"""

left = '\n'.join(slot(n) for n in [
    '01-hero.html', '02-programme.html', '03-chiffres.html',
    '04-temoignages.html', '05-zak.html', '06-faq.html',
])
right = '\n'.join([
    slot('10-commande-entete.html'),
    NATIVE_FORM,
    slot('11-commande-reassurance.html'),
])
sticky = (
    '<div class="pv-slot" data-label="Code HTML · 20-barre-mobile.html">'
    f'<div class="sio-rawhtml">\n{block("20-barre-mobile.html")}\n</div></div>'
)

html = SHELL.replace('__LEFT__', left).replace('__RIGHT__', right).replace('__STICKY__', sticky)
out = ROOT / 'apercu.html'
out.write_text(html, encoding='utf-8')
print('wrote', out, len(html), 'bytes')
