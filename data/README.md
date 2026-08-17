# Donnees et mode demonstration

Le depot demarre avec `DEMO_MODE=true` pour que l'interface Vercel soit immediately utilisable et affiche les 101 departements ainsi que J0 a J+7.

Les valeurs du mode demonstration sont deterministes et fictives. Elles ne representent ni la vigilance officielle Meteo-France ni une observation meteorologique.

Pour passer en mode reel :

1. Importer les donnees Meteo-France, BDIFF et les autres sources documentees dans `data/processed/features.csv`.
2. Entrainer et backtester le modele avec `ia-feux train --features data/processed/features.csv --model-dir models`.
3. Produire `data/predictions/latest.csv` avec les colonnes de prediction attendues par l'API.
4. Definir `DEMO_MODE=false` dans l'environnement Vercel et redeployer.

Sans predictions reelles, l'API conserve le mode demonstration pour eviter une page vide.
