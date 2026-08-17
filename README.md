# IA Vigilance Feux

Systeme IA de prediction de la vigilance feux de foret pour les departements francais.

Ce depot pose un MVP production-ready par etapes : ingestion de donnees reelles, feature engineering departemental, entrainement temporel sans fuite de donnees, backtest, API FastAPI et carte web.

## Principes non negociables

- Aucune donnee simulee n'est utilisee lorsqu'une source reelle est disponible.
- La vigilance officielle Meteo-France peut servir de label/reference, jamais de variable d'entree future.
- Chaque prediction est rattachee a un `available_at` pour verifier ce qui etait connu au moment de la decision.
- Un nouveau modele ne passe en production que s'il bat le modele courant sur une validation independante.
- Les sorties du modele sont clairement marquees comme predictions IA, jamais comme vigilance officielle.

## Sources prevues

- Meteo-France API : observations, climatologie, AROME, ARPEGE, radar, vigilance.
- BDIFF : historique des incendies de foret jusqu'a l'annee anterieure.
- Copernicus CDS / ERA5 : reanalyse et backfill lorsque les licences dataset sont acceptees.
- IGN/Admin Express ou equivalent open data : geometries departementales.

Voir `docs/data_sources.md` avant toute mise en production.

## Installation

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

## Variables d'environnement

Copier `.env.example` vers `.env` puis renseigner les cles reelles :

```bash
METEOFRANCE_API_KEY=...
CDSAPI_URL=https://cds.climate.copernicus.eu/api
CDSAPI_KEY=...
DATABASE_URL=sqlite:///data/fire_vigilance.db
```

## Donnees attendues pour le MVP

Le backtest MVP accepte un fichier CSV de features deja construites, issu de sources reelles :

```text
department_code,target_date,horizon,available_at,label_level,tmax,rh_min,wind_gust,precip_7d,dry_days,soil_moisture
```

`label_level` vaut `0,1,2,3` pour vert, jaune, orange, rouge.

## Commandes

```bash
# Entrainer et backtester sur un CSV historique reel
ia-feux train --features data/processed/features.csv --model-dir models

# Lancer l'API
uvicorn ia_vigilance_feux.api:app --reload
```

Endpoints principaux :

- `GET /forecast`
- `GET /forecast/{department_code}`
- `GET /history/{department_code}`
- `GET /model/performance`
- `POST /training/start`
- `GET /training/status`
- `GET /training/results`
- `GET /departments`

## Structure

```text
docs/                 Architecture, licences, schema SQL
frontend/             Carte interactive consommatrice de l'API
src/ia_vigilance_feux Pipeline ML et API
tests/                Tests unitaires du coeur metier
```

## Etat actuel

Ce premier commit initialise le socle technique et les garde-fous anti-fuite. Les connecteurs Meteo-France/CDS sont volontairement stricts : ils exigent des cles et/ou exports reels avant ingestion.