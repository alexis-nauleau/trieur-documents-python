"""Trie des documents scannés (images ou PDF) dans des dossiers selon leur contenu.

Le texte est lu par OCR (Tesseract), puis comparé à des mots-clés par catégorie.
Tout reste sur ton ordinateur : rien n'est envoyé sur Internet.

Usage :
    python trier_documents.py "C:\\programmes\\dossier"             # simulation (ne déplace rien)
    python trier_documents.py "C:\\programmes\\dossier" --appliquer   # déplace vraiment
"""
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path


TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")

CATEGORIES = {
    "EDF": [
        "edf", "electricite", "facture d'electricite", "kwh", "kilowattheure", "compteur",
        "linky", "enedis", "abonnement", "puissance souscrite", "tarif bleu",
        "point de livraison", "mensualisation",
    ],
    "Medical": [
        "ordonnance", "medecin", "docteur", "mutuelle", "biochimie", "securite sociale",
        "eurofins", "ameli", "pharmacie", "consultation", "analyse",
        "radiologie", "assurance maladie", "arrêt maladie", "arrêt de travail",
        "laboratoire", "hematologie", "prelevement", "feuille de soins", "carte vitale",
        "cpam", "indemnites journalieres", "dentiste", "ophtalmologue", "echographie",
        "irm", "scanner", "resultats d'analyses",
    ],
    "Voiture": [
        "carte grise", "certificat d'immatriculation", "immatriculation", "assurance auto",
        "controle technique", "permis de conduire", "vehicule", "garage", "vidange",
        "Clio", "kilometrage", "carrosserie", "pneumatique", "carte verte",
        "constat amiable", "ants",
    ],
    "Antai": [
        "antai", "avis de contravention", "contravention", "amende", "amende forfaitaire",
        "amende majoree", "exces de vitesse", "radar", "centre national de traitement",
        "infraction",
    ],
    "Caf": [
        "caf", "caisse d'allocations familiales", "allocations", "attestation de paiement",
        "quotient familial", "prestations familiales", "apl", "aide au logement", "rsa",
        "prime d'activite",
    ],
    "Impots": [
        "impot sur le revenu", "avis d'imposition", "avis d'impot", "dgfip", "impots.gouv",
        "taxe fonciere", "taxe d'habitation", "declaration de revenus",
        "revenu fiscal de reference", "prelevement a la source", "numero fiscal",
        "direction generale des finances publiques",
    ],
    "Assurance": [
        "assurance habitation", "multirisque habitation", "assurance immobilier",
        "assurance immobiliere", "assurance emprunteur", "attestation d'assurance",
        "contrat d'assurance", "sinistre", "cotisation d'assurance",
    ],
    "Banque": [
        "banque", "releve de compte", "releve bancaire", "iban", "bic", "rib",
        "credit agricole", "bnp", "societe generale", "caisse d'epargne",
        "la banque postale", "credit mutuel", "lcl", "virement", "pret immobilier",
        "offre de pret", "tableau d'amortissement",
    ],
}

SCORE_MINIMUM = 2

DOSSIER_INCONNU = "Non reconnus"
IMAGES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}
PAGES_MAX = 2  


def normaliser(texte):
    """Minuscules, sans accents : 'Électricité' -> 'electricite'."""
    decompose = unicodedata.normalize("NFD", texte.lower())
    return "".join(c for c in decompose if unicodedata.category(c) != "Mn")


def trouver_tesseract():
    if TESSERACT.exists():
        return str(TESSERACT)
    trouve = shutil.which("tesseract")
    if trouve:
        return trouve
    raise RuntimeError("Tesseract est introuvable : vérifie le chemin TESSERACT en haut du fichier.")


def ocr_image(chemin):
    """Lit le texte d'une image avec Tesseract (en français)."""
    resultat = subprocess.run(
        [trouver_tesseract(), str(chemin), "stdout", "-l", "fra"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return resultat.stdout


def lire_pdf(chemin):
    """Texte d'un PDF : d'abord le texte intégré, sinon OCR des pages (scan)."""
    try:
        import pymupdf  
    except ImportError:
        raise RuntimeError("Pour lire les PDF, installe pymupdf : pip install pymupdf")
    texte = ""
    with pymupdf.open(chemin) as pdf:
        pages = list(pdf)[:PAGES_MAX]
        texte = "".join(page.get_text() for page in pages)
        if len(texte.strip()) < 30:  # presque rien : c'est un scan, on passe par l'OCR
            texte = ""
            with tempfile.TemporaryDirectory() as dossier:
                for numero, page in enumerate(pages):
                    image = Path(dossier) / f"page{numero}.png"
                    page.get_pixmap(dpi=200).save(str(image))
                    texte += ocr_image(image)
    return texte


def lire_texte(chemin):
    extension = chemin.suffix.lower()
    if extension in IMAGES:
        return ocr_image(chemin)
    if extension == ".pdf":
        return lire_pdf(chemin)
    return None  # type de fichier non géré


def classer(texte):
    """Renvoie (catégorie, mots trouvés). Catégorie = DOSSIER_INCONNU si rien de net."""
    texte = normaliser(texte)
    meilleur, meilleurs_mots = DOSSIER_INCONNU, []
    egalite = False
    for categorie, mots in CATEGORIES.items():
        trouves = [mot for mot in mots if mot in texte]
        if len(trouves) > len(meilleurs_mots):
            meilleur, meilleurs_mots, egalite = categorie, trouves, False
        elif trouves and len(trouves) == len(meilleurs_mots):
            egalite = True
    # Pas assez de mots, ou deux catégories à égalité : on ne devine pas.
    if len(meilleurs_mots) < SCORE_MINIMUM or egalite:
        return DOSSIER_INCONNU, meilleurs_mots
    return meilleur, meilleurs_mots


def nom_libre(destination):
    """Si le nom existe déjà, ajoute (1), (2)... plutôt que d'écraser."""
    if not destination.exists():
        return destination
    numero = 1
    while True:
        essai = destination.with_name(f"{destination.stem} ({numero}){destination.suffix}")
        if not essai.exists():
            return essai
        numero += 1


def trier(dossier, appliquer=False):
    dossier = Path(dossier)
    if not dossier.is_dir():
        print(f"Dossier introuvable : {dossier}")
        return 1

    total = 0
    for fichier in sorted(dossier.iterdir()):
        if not fichier.is_file():
            continue
        try:
            texte = lire_texte(fichier)
        except RuntimeError as erreur:
            print(erreur)
            return 1
        if texte is None:
            continue  # ni image ni PDF : on ne touche pas
        categorie, mots = classer(texte)
        cible = nom_libre(dossier / categorie / fichier.name)
        print(f"{fichier.name}  ->  {categorie}/   (mots : {', '.join(mots) or 'aucun'})")
        if appliquer:
            cible.parent.mkdir(exist_ok=True)
            shutil.move(str(fichier), str(cible))
        total += 1

    mode = "déplacés" if appliquer else "à déplacer (simulation, ajoute --appliquer)"
    print(f"\n{total} fichier(s) {mode}.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(trier(sys.argv[1], appliquer="--appliquer" in sys.argv))