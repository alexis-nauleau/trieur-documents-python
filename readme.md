# Trieur de documents scannés

Range des scans (images et PDF) dans des dossiers (EDF, Médical, Voiture, Banque…)
selon leur contenu. Le texte est lu par OCR (Tesseract), puis comparé à des mots-clés.
Tout reste en local : rien n'est envoyé sur Internet.

## Installation

1. Installer Tesseract (version Windows : https://github.com/UB-Mannheim/tesseract/wiki),
   en cochant la langue française.
2. Installer Python, puis (pour les PDF) : `pip install pymupdf`

## Utilisation

    python trier_documents.py "python trier_documents.py "F:\Projets\python-bases\testrangementOCR""             # simulation
    python trier_documents.py "python trier_documents.py "F:\Projets\python-bases\testrangementOCR"" --appliquer   # déplace vraiment

La simulation affiche, pour chaque fichier, la catégorie choisie et les mots qui l'ont décidée.
Les mots-clés se règlent dans `CATEGORIES`. En cas de doute, le document va dans « Non reconnus ».

## Limites

- Tri par mots-clés, pas par compréhension du document.
- La qualité dépend de celle du scan.
- Tester sur une copie avant d'utiliser `--appliquer`.