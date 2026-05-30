import logging
import sys
import os  # Indispensable pour lire les variables d'environnement de Docker
import requests  # Utilisation de la bibliothèque pour envoyer le Webhook
from logging.handlers import RotatingFileHandler
from pathlib import Path
from main import main
from transform import run

# 📝 LE MONITORING RÉCUPÈRE L'URL DE DOCKER DE MANIÈRE SÉCURISÉE
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def send_notification(title, message, success=True):
    """Envoie une notification Embed sur Discord"""
    if not WEBHOOK_URL:
        return
        
    color = 3066993 if success else 15158332  # Vert si succès, Rouge si erreur
    payload = {
        "username": "Scraper Monitor",
        "embeds": [{
            "title": title,
            "description": message,
            "color": color,
            "footer": {"text": "Pipeline Automatique Docker"}
        }]
    }
    try:
        # 🔒 verify=False pour éviter le bug de certificat SSL dans le conteneur Mac
        requests.post(WEBHOOK_URL, json=payload, timeout=5, verify=False)
    except Exception as e:
        logger.error(f"Impossible d'envoyer l'alerte de monitoring : {e}")

# --- Configuration des Logs ---
Path("data").mkdir(exist_ok=True)

log_formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_formatter)

file_handler = RotatingFileHandler(
    filename="data/erreurs.log",
    maxBytes=1024 * 1024, 
    backupCount=3,
    encoding="utf-8"
)
file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(log_formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler, file_handler]
)

logger = logging.getLogger(__name__)

# --- Lancement du Pipeline avec Monitoring ---
if __name__ == "__main__":
    logger.info("🚀 Démarrage du pipeline de scraping...")
    
    try:
        date_identifiant = main()
        
        if date_identifiant:
            run(date_identifiant)
            logger.info("🎉 Pipeline terminé avec succès.")
            
            # Alerte de succès sur Discord
            send_notification(
                title="✅ Scraper : Succès !",
                message=f"Le pipeline a tourné correctement.\nIdentifiant du run : `{date_identifiant}`.\nDonnées injectées dans le CSV.",
                success=True
            )
        else:
            logger.warning("🚫 Pipeline arrêté : le scraping n'a généré aucun résultat.")
            send_notification(
                title="⚠️ Scraper : Alerte",
                message="Le pipeline s'est arrêté car aucun livre n'a pu être récupéré (Vérifier le catalogue).",
                success=False
            )
            
    except (Exception, KeyboardInterrupt) as error:
        # On détermine si c'est un Ctrl+C ou un vrai plantage de code
        if isinstance(error, KeyboardInterrupt):
            err_msg = "Le script a été arrêté manuellement avec Ctrl+C."
        else:
            err_msg = str(error)

        logger.critical(f"💥 Le pipeline a été interrompu ! Erreur : {err_msg}", exc_info=True)
        
        # Envoi de l'alerte rouge sur Discord
        send_notification(
            title="💥 Scraper : INTERROMPU / CRASH !",
            message=f"Le pipeline s'est arrêté de manière inattendue :\n`{err_msg}`",
            success=False
        )