# Sources de donnees et licences

Cette page doit etre verifiee avant tout usage commercial ou operationnel. Les licences peuvent evoluer.

## Meteo-France Donnees publiques

Usage prevu : observations, climatologie, AROME, ARPEGE, radar et vigilance officielle comme label/reference.

Acces : portail API Meteo-France avec compte. Les donnees publiques sont indiquees sans redevance sous Licence Ouverte d'Etalab/Open Licence 2.0 dans la documentation open data Meteo-France. La source a citer est `Meteo-France`.

Points d'attention :

- les paquets de prevision numerique ont une retention courte ; archiver les runs bruts des le premier jour ;
- ne jamais utiliser une vigilance officielle future comme feature ;
- la vigilance officielle peut etre un label, ou une reference de comparaison, selon l'experimentation.

References :

- https://www.data.gouv.fr/organizations/meteo-france/dataservices
- https://www.data.gouv.fr/dataservices/api-bulletin-vigilance
- https://www.data.gouv.fr/dataservices/api-modele-arome
- https://confluence-meteofrance.atlassian.net/wiki/spaces/OpenDataMeteoFrance/pages/618659848/Documentation%2Bsur%2Ble%2Bcontenu%2Bdes%2Bdonn%2Bes%2Bpubliques%2Bde%2BM%2Bt%2Bo-France

## BDIFF

Usage prevu : historique des incendies, surfaces brulees, frequence par commune/departement.

Acces : consultation publique et compte utilisateur selon les fonctions. La base diffuse des donnees jusqu'a l'annee anterieure, agregees a la commune.

Reference : https://bdiff.agriculture.gouv.fr/

## Copernicus CDS / ERA5

Usage prevu : reanalyse historique et backfill meteorologique lorsque les observations ou archives de runs ne suffisent pas.

Acces : compte CDS, cle API, acceptation de la licence de chaque dataset.

References :

- https://cds.climate.copernicus.eu/how-to-api
- https://cds.climate.copernicus.eu/licences/terms-of-use-cds

## Geometries departementales

Usage prevu : carte interactive et agregation spatiale. Utiliser une source ouverte officielle, par exemple IGN/Admin Express ou contours administratifs disponibles sur data.gouv.fr, en conservant l'attribution et la version.

## Donnees non incluses dans le depot

Les donnees meteo, vigilance, incendies et geometries lourdes ne sont pas versionnees dans Git. Les stocker dans :

```text
data/raw/<source>/<date>/...
data/processed/features.csv
data/predictions/latest.csv
```
