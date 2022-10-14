
ogr2ogr -f CSV /tmp/depts_bbox.csv /vsigzip//home/thomasg/git/contours-administratifs/dist/departements-5m.geojson.gz -dialect SQLite -sql 'SELECT code, ST_Miny(geometry) AS miny, ST_Minx(geometry) AS minx, ST_Maxy(geometry) AS maxy, ST_Maxx(geometry) AS maxx FROM "departements-5m.geojson"'

sed -i '1d' /tmp/depts_bbox.csv

while IFS=, read -r code miny minx maxy maxx;
do
    echo $code;
    echo '[out:json][timeout:60];(node["amenity"="fuel"]('${miny},${minx},${maxy},${maxx}');way["amenity"="fuel"]('${miny},${minx},${maxy},${maxx}');relation["amenity"="fuel"]('${miny},${minx},${maxy},${maxx}'););out;>;out skel qt;' | query-overpass >| "dept_"${code}".geojson";
    sleep 5;
done < /tmp/depts_bbox.csv;

remaining=$(ls --sort=size -l dept_*.geojson | grep '    0' | sed 's#\.geojson##g' | sed 's#^[a-z0-9:\.\ \-]*_#^#g')
myreg=$(echo $remaining | sed 's# #\\|#g')

grep $myreg /tmp/depts_bbox.csv >| /tmp/depts_bbox_remaining.csv;

while IFS=, read -r code miny minx maxy maxx;
do
    echo $code;
    echo '[out:json][timeout:60];(node["amenity"="fuel"]('${miny},${minx},${maxy},${maxx}');way["amenity"="fuel"]('${miny},${minx},${maxy},${maxx}');relation["amenity"="fuel"]('${miny},${minx},${maxy},${maxx}'););out;>;out skel qt;' | query-overpass >| "dept_"${code}".geojson";
    sleep 5;
done < /tmp/depts_bbox_remaining.csv;

jq -c .features[] dept_*.geojson | sort | uniq | jq --slurp '{"type":"FeatureCollection","features":.}' \
>| all_amenity_fuel.geojson

echo '[out:json][timeout:250];(node["ref:FR:prix-carburants"];way["ref:FR:prix-carburants"];relation["ref:FR:prix-carburants"];);out;>;out skel qt;' | query-overpass >| /tmp/all_prix_carburants.geojson
