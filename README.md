Source de données:

- https://www.data.gouv.fr/fr/datasets/prix-des-carburants-en-france/

## Aperçu de la structure des XML

```
# Utilisation de Trang pour avoir un aperçu rapide de la structure des XML
# Fichier sur https://github.com/relaxng/jing-trang/releases
wget https://github.com/relaxng/jing-trang/releases/download/V20181222/trang-20181222.zip
unzip -j trang-20181222.zip
for i in $(seq 2007 2022);
  do wget -N --content-disposition "https://donnees.roulez-eco.fr/opendata/annee/${i}";
done;
for i in PrixCarburants_annuel_20*.zip;
  do unzip -o $i;
done;

for i in PrixCarburants_annuel_20*.xml;
  do java -jar trang.jar "$i" ${i%%.*}.xsd;
done;

java -jar trang.jar PrixCarburants_annuel_20*.xml schema.xsd
```

## Génération du GeoJSON imbriqué sur 2022

Attention, si vous utilisez la donnée instantanée (https://donnees.roulez-eco.fr/opendata/instantane), vous n'aurez pas les ruptures de carburant (constaté et remonté dans les discussions (https://www.data.gouv.fr/fr/datasets/prix-des-carburants-en-france-flux-instantane/#discussion-633af25db3442f9b2b7951ab). Il faut prendre la donnée du jour (https://donnees.roulez-eco.fr/opendata/jour).

```
rm PrixCarburants_quotidien_*.zip PrixCarburants_quotidien_*.xml
wget --content-disposition https://donnees.roulez-eco.fr/opendata/jour
unzip PrixCarburants_quotidien_*.zip
rm *.zip
filename=$(ls *.xml)

# Problème d'encoding réglé indirectement (déclaré comme ISO-9958-1 mais accent détruit quand lu avec cet encoding...)
iconv -f iso-8859-1 -t utf-8 $filename >| PrixCarburants_quotidien_20221011_utf8.xml
python reformat-prix-carburants.py PrixCarburants_quotidien_20221011_utf8.xml
```

Cela donne le fichier `stations_with_info.geojson` ainsi que des fichiers CSV

## Intégration en base SQLite/Geopackage des données CSV dont les stations

```
python load_data.py
```

Sortie de `ogrinfo -so carburants.gpkg`

```
INFO: Open of `carburants.gpkg'
      using driver `GPKG' successful.
1: stations (Point)
2: fermetures (None)
3: jour_and_horaires (None)
4: ouvertures (None)
5: prix (None)
6: ruptures (None)
7: services_text (None)
```

## TODO:

- rattachement station avec nom et autres informations de contact
- check en comparant à adresse
- certaines données sont mal géolocalisées: hors de France (voir remontée perso sur https://www.data.gouv.fr/fr/datasets/prix-des-carburants-en-france-flux-instantane/#discussion-634311f440cddf4700d4ec76 mais je n'ai pas testé tous les cas seul les plus évidents en terme de coordonnées)
- disparitions stations surtout sur anciennes années?
- cas foireux sur les ouvertures (exemple https://map.bp.com/fr-FR/FR/station-essence/cergy/bp-cergy-st-christophe/820954193 vs ROND POINT DES CHENES (BD DE LOISE) CERGY ou pas même horaire le samedi)
