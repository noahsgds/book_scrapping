import json
import pandas as pd
import logging # <-- Ajout
from pathlib import Path

# Initialisation du logger pour ce fichier
logger = logging.getLogger(__name__)

def run(run_date):
    if not run_date:
        logger.warning("⚠️ Aucune donnée à transformer (run_date est vide).")
        return

    json_path = f"data/books_{run_date}.json"
    if not Path(json_path).exists():
        logger.error(f"❌ Fichier introuvable : {json_path}")
        return

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        logger.warning("⚠️ Le fichier JSON est vide. Transformation annulée.")
        return

    df = pd.DataFrame(data)
    df["run_date"] = run_date

    output = "data/books.csv"
    df.to_csv(output, mode='a', header=not Path(output).exists(), index=False, encoding="utf-8-sig")

    logger.info(f"📊 {len(df)} lignes ajoutées avec succès dans {output}")