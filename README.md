# Books Scraper - Pipeline Automatise

Pipeline de scraping automatise qui collecte les donnees du catalogue [books.toscrape.com](https://books.toscrape.com), les transforme en CSV et envoie des notifications de monitoring sur Discord. Le tout est containerise avec Docker et planifie via cron pour une execution nocturne sans intervention manuelle.

---

## Sommaire

- [Fonctionnalites](#fonctionnalites)
- [Architecture du pipeline](#architecture-du-pipeline)
- [Structure du projet](#structure-du-projet)
- [Donnees collectees](#donnees-collectees)
- [Prerequis](#prerequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [Planification automatique](#planification-automatique-cron)
- [Monitoring et alertes Discord](#monitoring-et-alertes-discord)
- [Logs](#logs)
- [Technologies](#technologies)

---

## Fonctionnalites

- Scraping complet du catalogue `books.toscrape.com` : 1000 livres sur 50 pages
- Arret automatique intelligent : detection de la fin du catalogue via reponse HTTP 404
- Resilience reseau : 3 tentatives automatiques par URL avec delai de 2 secondes entre chaque
- Transformation automatique : conversion JSON vers CSV cumulatif (append a chaque run)
- Notifications Discord en temps reel avec embeds colores (succes, alerte, crash)
- Logs structures : console (niveau INFO) et fichier rotatif (niveau WARNING, max 1 Mo)
- Execution planifiee chaque nuit a 03h00 via cron (heure creuse)
- Donnees persistees dans un volume Docker partage avec l'hote
- Securite : aucune variable sensible hardcodee, tout passe par les variables d'environnement

---

## Architecture du pipeline

Le pipeline se deroule en trois etapes orchestrees par `scraper.py` :

```
[main.py]          [transform.py]          [scraper.py]
Scraping Web  -->  JSON vers CSV  -->  Monitoring Discord
                   Append cumulatif    Logs + Orchestration
     |                   |
     v                   v
books_<date>.json    books.csv
```

### Fonctionnement detaille

**Etape 1 - Scraping (`main.py`)**

1. La fonction `get_books_links()` parcourt les pages de `page-1.html` jusqu'a obtenir un `404`
2. Pour chaque page, les URLs des livres sont extraites via un selecteur CSS
3. La fonction `scrape_book(url)` visite chaque fiche livre et extrait les donnees via BeautifulSoup
4. En cas d'echec reseau : 3 tentatives automatiques avec `time.sleep(2)` entre chaque
5. Resultat : fichier JSON horodate `data/books_YYYY-MM-DD_HH-MM-SS.json`

**Etape 2 - Transformation (`transform.py`)**

1. Chargement du fichier JSON genere a l'etape precedente
2. Conversion en DataFrame `pandas`
3. Ajout de la colonne `run_date` pour tracer chaque execution
4. Ecriture en mode **append** dans `data/books.csv` (l'en-tete n'est ecrit qu'a la premiere execution)

**Etape 3 - Monitoring (`scraper.py`)**

1. Orchestration des deux etapes ci-dessus
2. Configuration des handlers de logs (console + fichier rotatif)
3. Envoi de notifications Discord selon le resultat (succes / alerte / crash)
4. Gestion des exceptions globales (y compris `KeyboardInterrupt`)

---

## Structure du projet

```
books-scraper/
|
|-- src/
|   |-- main.py             # Scraping : parcours pages + extraction donnees
|   |-- scraper.py          # Point d'entree : orchestration + logs + Discord
|   +-- transform.py        # Transformation JSON vers CSV avec pandas
|
|-- data/                   # Genere automatiquement (persiste via volume Docker)
|   |-- books_<date>.json   # Donnees brutes horodatees
|   |-- books.csv           # CSV cumulatif de tous les runs
|   |-- erreurs.log         # Logs des erreurs (rotatif, max 1 Mo)
|   +-- cron.log            # Logs de chaque execution planifiee
|
|-- Dockerfile              # Image Docker python:3.11-slim + cron
|-- docker-compose.yml      # Services, volumes et variables d'env
|-- crontab.sh              # Regle cron : execution tous les jours a 03h00
|-- requirements.txt        # Dependances Python
|-- .env.example            # Template du fichier d'environnement
+-- README.md               # Ce fichier
```

---

## Donnees collectees

Pour chaque livre, les champs suivants sont extraits et stockes :

| Champ | Type | Description | Exemple |
|---|---|---|---|
| `upc` | string | Identifiant unique du livre | `2587c54f5530dafc` |
| `title` | string | Titre complet du livre | `Cravings: Recipes for What You Want to Eat` |
| `category` | string | Categorie du catalogue | `Food and Drink` |
| `rating` | int (1-5) | Note en nombre d'etoiles | `3` |
| `price` | float | Prix en GBP | `20.5` |
| `stock` | int | Quantite disponible en stock | `11` |
| `description` | string | Description du livre | `Though she is best known as...` |
| `nb_reviews` | int | Nombre d'avis lecteurs | `0` |
| `link` | string | URL complete de la fiche livre | `https://books.toscrape.com/...` |
| `run_date` | string | Horodatage de l'execution | `2026-05-29_03-22-40` |

---

## Prerequis

- [Docker](https://www.docker.com/) ou [Rancher Desktop](https://rancherdesktop.io/) (alternative sans droits administrateur)
- [Docker Compose](https://docs.docker.com/compose/)
- Un Webhook Discord (optionnel, pour les notifications de monitoring)
- Git avec une connexion SSH configuree (recommande)

> **Note :** Si Docker Desktop ne peut pas etre installe sur votre poste (restrictions de droits), **Rancher Desktop** est une alternative open-source qui supporte les memes commandes Docker et docker-compose sans necessite de droits administrateur.

---

## Installation

### 1. Cloner le depot

```bash
# Via SSH (recommande si HTTPS est bloque)
git clone git@github.com:<votre-user>/books-scraper.git
cd books-scraper

# Via HTTPS
git clone https://github.com/<votre-user>/books-scraper.git
cd books-scraper
```

### 2. Creer le fichier d'environnement

```bash
cp .env.example .env
```

Editez le fichier `.env` avec votre URL de Webhook Discord :

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/XXXX/YYYY
```

> Le fichier `.env` est ignore par Git. Ne committez jamais vos variables sensibles.

### 3. Builder et lancer le conteneur

```bash
# Construire l'image et demarrer le conteneur
docker-compose up --build

# En arriere-plan (mode detache)
docker-compose up --build -d
```

---

## Configuration

### Variables d'environnement

| Variable | Description | Obligatoire |
|---|---|---|
| `DISCORD_WEBHOOK_URL` | URL du Webhook Discord pour les notifications | Non (alertes desactivees si absent) |

### Exemple de `.env.example`

```env
# URL du webhook Discord pour le monitoring
# Laisser vide pour desactiver les notifications
DISCORD_WEBHOOK_URL=
```

---

## Utilisation

### Avec Docker Compose (recommande)

```bash
# Demarrer le conteneur (le cron tourne automatiquement a 03h00)
docker-compose up -d

# Arreter le conteneur
docker-compose down

# Voir les logs du conteneur en temps reel
docker-compose logs -f
```

### Lancer le pipeline manuellement depuis le conteneur

```bash
# Ouvrir un shell dans le conteneur en cours d'execution
docker exec -it scrapper_book.launch bash

# Lancer le pipeline manuellement
python3 /app/src/scraper.py
```

### En local sans Docker (developpement)

```bash
# Installer les dependances
pip install -r requirements.txt

# Lancer le pipeline
python src/scraper.py
```

### Consulter les donnees generees

```bash
# Voir le CSV cumulatif
cat data/books.csv

# Voir les dernieres entrees du CSV
tail -20 data/books.csv

# Voir les erreurs loguees
cat data/erreurs.log

# Voir les logs d'execution cron
cat data/cron.log
```

---

## Planification automatique (cron)

Le fichier `crontab.sh` configure une execution automatique **tous les jours a 03h00** :

```cron
# min  heure  jour_mois  mois  jour_semaine  commande
  0     3       *          *       *          cd /app && python3 -u src/scraper.py >> /app/data/cron.log 2>&1
```

Pour modifier la frequence, editez `crontab.sh` avant de reconstruire l'image :

```cron
# Toutes les 6 heures
0 */6 * * * cd /app && python3 -u src/scraper.py ...

# Toutes les heures
0 * * * * cd /app && python3 -u src/scraper.py ...

# Tous les lundis a 08h00
0 8 * * 1 cd /app && python3 -u src/scraper.py ...
```

---

## Monitoring et alertes Discord

Le script envoie automatiquement des messages Embed Discord colores selon le resultat du pipeline :

| Statut | Couleur | Declencheur | Message |
|---|---|---|---|
| Succes | Vert | Pipeline termine avec succes | Identifiant du run + confirmation injection CSV |
| Alerte | Orange | Aucun livre collecte | Invitation a verifier le catalogue |
| Crash | Rouge | Exception ou interruption inattendue | Message d'erreur complet |

### Configurer un Webhook Discord

1. Ouvrez les **Parametres** de votre serveur Discord
2. Allez dans **Integrations > Webhooks > Nouveau Webhook**
3. Donnez-lui un nom (ex: `Scraper Monitor`) et choisissez le channel
4. Copiez l'URL et collez-la dans votre fichier `.env`

---

## Logs

Le projet genere deux types de logs :

**Console (niveau INFO)** - Affiche en temps reel dans le terminal ou Docker :

```
2026-05-29 03:00:01 | INFO     | main    | Scan de la page : https://books.toscrape.com/catalogue/page-1.html
2026-05-29 03:00:02 | INFO     | main    | A Light in the Attic
2026-05-29 03:22:40 | INFO     | scraper | Pipeline termine avec succes.
```

**Fichier `data/erreurs.log` (niveau WARNING)** - Conserve les erreurs et avertissements uniquement. Fichier rotatif : max 1 Mo, 3 backups conserves :

```
2026-05-19 10:03:01 | WARNING  | main | Tentative 1/3 echouee pour https://... Erreur: Read timed out.
2026-05-19 10:03:05 | WARNING  | main | Tentative 2/3 echouee pour https://...
```

---

## Technologies

| Technologie | Usage |
|---|---|
| Python 3.11 | Langage principal |
| `requests` | Requetes HTTP avec gestion du timeout et retry |
| `beautifulsoup4` | Parsing HTML et extraction des donnees |
| `pandas` | Transformation des donnees et export CSV |
| `logging` | Logs structures avec handlers multiples |
| Docker / Rancher Desktop | Containerisation et isolation |
| `cron` | Planification automatique nocturne |
| Discord Webhook | Monitoring et alertes en temps reel |
| GitHub (SSH) | Versionnage et partage du code |

---

## Licence

Projet realise dans le cadre de la formation **Data Engineer - Eugenia School**.
Auteur : **Noah Segonds** - nsegonds@eugeniaschool.com
