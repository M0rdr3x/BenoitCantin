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
    "Je comprends que cette réservation n’est pas encore un achat",
):
    require(public_page, token, "page publique de précommande")

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

print("OK — SINJIRA V24.5.3 précommandes sans paiement validées.")
