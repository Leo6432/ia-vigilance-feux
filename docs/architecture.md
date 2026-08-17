# Architecture complete

## Objectif

Predire chaque jour, pour les 101 departements francais, un niveau IA de risque feux de foret sur 4 classes : vert, jaune, orange, rouge. La sortie inclut un score 0-100, des probabilites par classe, une confiance et des facteurs explicatifs.

## Flux general

```text
Sources reelles
  -> stockage raw horodate
  -> normalisation
  -> agregation spatiale departementale
  -> feature store temporel
  -> entrainement/backtest
  -> registre de modeles
  -> API de prediction
  -> carte interactive
```

## Garde-fous anti-fuite

Chaque ligne de feature contient :

- `target_date` : jour predit.
- `horizon` : 0 a 7 jours.
- `available_at` : date/heure a laquelle la donnee etait effectivement disponible.
- `source_run_id` : run meteo ou observation source.

Regle stricte : aucune feature dont `available_at` est posterieur a la date de decision ne peut entrer dans l'entrainement ou le backtest.

## Modes

### Entrainement / backtest

1. Selectionner une periode historique.
2. Reconstituer uniquement les donnees disponibles a chaque date de prediction.
3. Entrainer sur le passe, valider sur une annee independante, tester sur une annee posterieure.
4. Calculer accuracy, balanced accuracy, precision/recall/F1 par classe, matrice de confusion, taux de fausses alertes, detection orange/rouge, Brier score.
5. Enregistrer le modele et ses seuils.
6. Promouvoir seulement si les metriques critiques progressent.

### Prevision actuelle

1. Recuperer les derniers runs meteo et observations disponibles.
2. Construire les features J0 a J+7 par departement.
3. Produire les probabilites, score, niveau, confiance et facteurs.
4. Exposer les resultats via API et carte.

## Modeles

Priorite MVP :

- baseline interpretable : HistGradientBoosting scikit-learn ;
- production candidate : LightGBM, CatBoost, XGBoost ;
- calibration probabiliste : isotonic ou sigmoid ;
- explicabilite : SHAP quand le modele final le supporte.

Le deep learning est exclu du MVP sauf justification empirique.

## Carte

La carte frontend consomme :

- `GET /departments` pour la liste ;
- `GET /forecast?date=YYYY-MM-DD` pour les predictions ;
- `GET /forecast/{department_code}` pour le detail.

Les geometries GeoJSON doivent venir d'une source open data officielle et etre stockees dans `frontend/assets/departments.geojson` ou servies par l'API.
