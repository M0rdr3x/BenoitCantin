from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    target = ROOT / path
    if not target.exists():
        raise SystemExit(f"Fichier requis absent: {path}")
    return target.read_text(encoding="utf-8")


def require(text: str, token: str, label: str) -> None:
    if token not in text:
        raise SystemExit(f"Contrat V24.5.3 absent dans {label}: {token}")


migration_path = "supabase/migrations/20260822165140_sinjira_v24_5_3_livre_1_preorder_reservations.sql"
migration = read(migration_path)
public_page = read("projets/sinjira/romans/precommande.html")
romans_page = read("projets/sinjira/romans/index.html")
account_page = read("compte/mes-achats.html")
client = read("assets/js/sinjira-preorders-v24-5-3.js")
canon = read("PRECOMMANDES_ROMAN_V24_5_3.md")
account_architecture = read("ARCHITECTURE_COMPTE_UNIVERSEL.md")
paid_policy = read("SERVICES_EXTERNES_PAYANTS.md")
ledger = read("supabase/production-migration-ledger.txt")

for token in (
    "create table if not exists public.product_preorders",
    "payment_status text not null default 'not_collected'",
    "check (payment_status = 'not_collected')",
    "financial_commitment boolean not null default false",
    "check (financial_commitment = false)",
    "product_preorder_reserve",
    "product_preorder_cancel",
    "product_preorder_my_status",
    "sinjira-livre-01-la-cendre-du-jugement",
):
    require(migration, token, migration_path)

for token in (
    "Aucun paiement aujourd’hui",
    "data-preorder-root",
    "data-preorder-form",
    "data-preorder-cancel",
):
    require(public_page, token, "page publique de précommande")

# V24.5.3 exigeait déjà une compréhension explicite que la réservation n'est pas un achat.
# V24.5.31 conserve cet invariant avec un texte plus complet (commande, livraison, taxes, total final).
if not (
    "Je comprends que cette réservation n’est pas encore un achat" in public_page
    or (
        "data-preorder-disclosure" in public_page
        and "une réservation n’est pas une commande" in public_page.lower()
        and "aucun paiement n’est prélevé aujourd’hui" in public_page.lower()
    )
):
    raise SystemExit("Contrat V24.5.3 absent dans page publique de précommande: compréhension explicite réservation ≠ achat/commande")

for token in (
    'href="precommande.html"',
    "Précommandes ouvertes",
    "Réservation sans paiement",
):
    require(romans_page, token, "page Littérature")

for token in (
    'id="precommandes"',
    "Mes achats et précommandes",
    "data-preorder-root",
    "Aucune donnée bancaire",
):
    require(account_page, token, "Mes achats")

for token in (
    "product_preorder_reserve",
    "product_preorder_cancel",
    "product_preorder_my_status",
    "Aucun paiement n’a été prélevé",
):
    require(client, token, "client précommandes")

for token in (
    "Réserver aujourd’hui ne signifie jamais consentir à payer demain.",
    "payment_status = not_collected",
    "financial_commitment = false",
):
    require(canon, token, "canon précommandes")

for token in (
    "Mes achats et précommandes",
    "payment_status = not_collected",
    "financial_commitment = false",
    "Une réservation ne peut jamais être transformée automatiquement en vente",
):
    require(account_architecture, token, "architecture du Compte")

for token in (
    "Précommandes du Livre I",
    "payment_status = not_collected",
    "financial_commitment = false",
    "ne doit jamais être convertie automatiquement en commande payante",
):
    require(paid_policy, token, "politique services payants")

require(
    ledger,
    "20260822165140 sinjira_v24_5_3_livre_1_preorder_reservations",
    "ledger production",
)

# La présence de ces intégrations dans le nouveau runtime de précommande serait une
# activation commerciale prématurée. Les mentions documentaires ne sont pas testées ici.
for forbidden in (
    "stripe.com",
    "checkout.stripe.com",
    "paypal.com",
    "RESEND_API_KEY",
    "OPENAI_API_KEY",
    "card_number",
    "payment_method",
    "billing_address",
):
    if forbidden.lower() in (client + public_page + account_page + migration).lower():
        raise SystemExit(f"Intégration payante interdite dans la V24.5.3: {forbidden}")

# Les étapes publiques de réservation restent navigables sans JavaScript.
# Ne jamais masquer une étape, ses conditions ou la navigation derrière une session.
ux_css = read("assets/css/sinjira-preorder-steps-ux-v1.css")
browser_tests = read("tests/e2e/test_literature_site.py")
require(public_page, 'data-preorder-page="livre-1"', "périmètre précommande")
require(public_page, '/assets/css/sinjira-preorder-steps-ux-v1.css?v=1.0.0', "CSS des étapes")
require(public_page, 'aria-label="Étapes de la réservation du Livre I"', "nom du sommaire")
for fragment in ("prix-livre-1", "reception-livre-1", "reservation-livre-1"):
    if public_page.count(f'id="{fragment}"') != 1:
        raise SystemExit(f"Étape {fragment} manquante ou dupliquée")
    require(public_page, f'href="#{fragment}"', f"ancre publique {fragment}")
    require(public_page, f'aria-labelledby="{fragment}-titre"', f"titre accessible {fragment}")
for status in ("data-preorder-status", "data-pf-preference-status", "data-pf-estimate-result"):
    require(public_page, status + ' role="status" aria-live="polite"', f"annonce {status}")
for selector in (".sinjira-preorder-steps", "overflow-x:auto", "min-height:48px",
                 ":focus-visible", "prefers-reduced-motion:reduce", "scroll-margin-top"):
    require(ux_css, selector, "CSS ergonomique précommande")
if "style=" in public_page:
    raise SystemExit("Un style HTML intégré subsiste sur la précommande")
require(browser_tests, "assert_preorder_public_steps_responsive(browser)",
        "recette Playwright précommande")
require(browser_tests, "(240, 320, 390, 768, 1024, 1440)",
        "six résolutions Playwright précommande")

print("OK — SINJIRA V24.5.3 précommandes sans paiement validées, y compris le texte de transparence renforcé V24.5.31.")
