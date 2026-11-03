
#!/usr/bin/env python3
"""Sauvegarde la base, lance l'échéancier Django et ouvre le navigateur."""
import subprocess
import sys
import time
import webbrowser
from datetime import date
from pathlib import Path

PROJET = Path(__file__).resolve().parent
PYTHON = PROJET / "venv" / "bin" / "python"
URL = "http://127.0.0.1:8000/"

DOSSIER_SAUVEGARDES = Path.home() / "Documents" / "Echéanciers" / "sauvegardes"

if not PYTHON.exists():
    sys.exit(f"Python du venv introuvable : {PYTHON}")

# 1. Sauvegarde datée (une par jour : relancer le même jour l'écrase)
DOSSIER_SAUVEGARDES.mkdir(parents=True, exist_ok=True)
sauvegarde = DOSSIER_SAUVEGARDES / f"echeancier_{date.today()}.json"
resultat = subprocess.run(
    [str(PYTHON), "manage.py", "dumpdata", "--indent", "2",
     "-e", "contenttypes", "-e", "auth.permission",
     "-o", str(sauvegarde)],
    cwd=PROJET,
)
if resultat.returncode == 0:
    print(f"Sauvegarde : {sauvegarde.name}")
else:
    print("Attention : la sauvegarde a échoué (le serveur démarre quand même).")

# 2. Serveur Django
serveur = subprocess.Popen(
    [str(PYTHON), "manage.py", "runserver", "--noreload"],
    cwd=PROJET,
)

# 3. Navigateur
time.sleep(3)
webbrowser.open(URL)

try:
    serveur.wait()      # Ctrl+C ou fermeture du terminal pour arrêter
except KeyboardInterrupt:
    serveur.terminate()
