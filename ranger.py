"""Range les fichiers d'un dossier dans des sous-dossiers selon leur extension.

Usage :
    python ranger.py "C:\\Users\\Utilisateur\\Downloads"            # simulation (ne déplace rien)
    python ranger.py "C:\\Users\\Utilisateur\\Downloads" --appliquer  # déplace vraiment
"""

import shutil  # sait déplacer des fichiers
import sys     # donne accès à ce qu'on a tapé dans le terminal
from pathlib import Path  # manipule des chemins de dossiers et de fichiers


CATEGORIES = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"},
    "Documents": {".pdf", ".docx", ".txt", ".xlsx", ".pptx", ".md"},
    "Archives": {".zip", ".rar", ".7z"},
    "Code": {".py", ".js", ".ts", ".html", ".css", ".json"},
    "Installateurs": {".exe", ".msi"},
}


def categorie(fichier):
    """Renvoie le nom du sous-dossier pour ce fichier ('Autres' si inconnu)."""
    # .suffix donne l'extension (".PDF"), .lower() la met en minuscules (".pdf"),
    # pour que "photo.JPG" et "photo.jpg" soient traités pareil.
    extension = fichier.suffix.lower()
    # .items() donne chaque paire (nom, extensions) du dictionnaire, une par une.
    for nom, extensions in CATEGORIES.items():
        if extension in extensions:  # "in" : l'extension est-elle dans cet ensemble ?
            return nom
    return "Autres"  # on n'arrive ici que si aucune catégorie ne correspondait


def nom_libre(destination):
    """Si le fichier existe déjà, ajoute (1), (2)... plutôt que d'écraser."""
    if not destination.exists():  # le nom est libre : on le garde
        return destination
    numero = 1
    while True:
        # .stem = nom sans extension ("cv"), .suffix = l'extension (".pdf")
        # On fabrique donc "cv (1).pdf", puis "cv (2).pdf"...
        essai = destination.with_name(f"{destination.stem} ({numero}){destination.suffix}")
        if not essai.exists():
            return essai
        numero += 1


def ranger(dossier, appliquer=False):
    # Path(...) transforme le texte en "chemin" avec lequel on peut travailler.
    dossier = Path(dossier)
    if not dossier.is_dir():  # si ce n'est pas un dossier existant, on s'arrête
        print(f"Dossier introuvable : {dossier}")
        return 1  # 1 = "il y a eu un problème"

    total = 0
    # .iterdir() liste le contenu du dossier ; sorted(...) le met dans l'ordre alphabétique.
    for fichier in sorted(dossier.iterdir()):
        if not fichier.is_file():  # on ignore les sous-dossiers
            continue  # "passe directement à l'élément suivant"
        # dossier / "Images" / "photo.jpg" : le "/" assemble les morceaux d'un chemin.
        cible = nom_libre(dossier / categorie(fichier) / fichier.name)
        print(f"{fichier.name}  ->  {cible.parent.name}/{cible.name}")
        if appliquer:  # SEULEMENT si on a demandé --appliquer
            cible.parent.mkdir(exist_ok=True)  # crée le sous-dossier s'il n'existe pas
            shutil.move(str(fichier), str(cible))  # déplace le fichier
        total += 1

    mode = "déplacés" if appliquer else "à déplacer (simulation, ajoute --appliquer)"
    print(f"\n{total} fichier(s) {mode}.")
    return 0  # 0 = "tout s'est bien passé"


if __name__ == "__main__":
    # sys.argv est la liste de ce qui a été tapé : ["ranger.py", "le dossier", "--appliquer"]
    if len(sys.argv) < 2:  # pas de dossier donné : on affiche le mode d'emploi
        print(__doc__)
        sys.exit(2)
    # "--appliquer" in sys.argv : vrai si le mot a été tapé dans la commande
    sys.exit(ranger(sys.argv[1], appliquer="--appliquer" in sys.argv))