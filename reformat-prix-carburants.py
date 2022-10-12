import csv
import os
import json
import sys
import ssl
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from itertools import groupby, chain
from shapely.geometry import Point, shape
import argparse
try:
    from lxml import etree
except ImportError:
    try:
        print("Failed to import etree from lxml. Fall to default Python lib")
        from xml.etree import ElementTree as etree
    except ImportError:
        print("Failed to import etree from native Python")

# Todo: loop on each xml file
# local_path = 'PrixCarburants_annuel_2022.xml'
# local_path = 'PrixCarburants_quotidien_20221009_utf8.xml'
parser = argparse.ArgumentParser()
parser.add_argument("path", type=str,
                    help="Provide path to xml file")
args = parser.parse_args()

local_path = args.path

with open(local_path, encoding="utf-8") as req:
    xml_content = etree.parse(req)

def getJSON(urlData):
    webURL = urllib.request.urlopen(urlData)
    data = webURL.read()
    encoding = webURL.info().get_content_charset('utf-8')
    return json.loads(data.decode(encoding))


all_services = []

features = []
contents = []
for pdv in xml_content.findall('/pdv'):
    content = {}
    csv_output_content = {}
    # print(pdv)
    try:
        pdv_attribs = dict(pdv.attrib)
        pdv_attribs['adresse'] = pdv.find('adresse').text
        pdv_attribs['ville'] = pdv.find('ville').text
        longitude_original = pdv_attribs['longitude']
        latitude_original = pdv_attribs['latitude']
        longitude = pdv_attribs['longitude']
        latitude = pdv_attribs['latitude']
        if pdv_attribs['longitude'] in ('', '0'):
            longitude = None
        else:
            longitude = float(pdv_attribs['longitude']) / 100000

        if pdv_attribs['latitude'] in ('', '0'):
            latitude = None
        else:
            latitude = float(pdv_attribs['latitude']) / 100000

        if pdv_attribs["cp"][0:2] not in ['97', '98'] and latitude is not None and -4.7240000000000002 < latitude < 9.5480378609999992 and longitude is not None and 41.3900000000000006 < longitude < 51.0659999999999954:
            temp = longitude
            longitude = latitude
            latitude = temp

        if pdv_attribs["cp"][0:2] not in ['97', '98'] and latitude_original is not None and latitude_original != '' and -4.7240000000000002 < float(latitude_original) < 9.5480378609999992 and longitude_original is not None and longitude_original != '' and 41.3900000000000006 < float(longitude_original) < 51.0659999999999954:
            longitude = float(latitude_original) if latitude_original != '' else None
            latitude = float(longitude_original) if longitude_original != '' else None

        if pdv_attribs["cp"][0:2] not in ['97', '98'] and longitude is not None and not -4.7240000000000002 < longitude < 9.5480378609999992:
            print('Longitude issue')
            print(f"{pdv_attribs.get('longitude', '')},{pdv_attribs.get('latitude', '')}")
            print(f"Original: {longitude_original}, {latitude_original}")
            print(pdv_attribs)
            bbox_response = getJSON(f"https://geo.api.gouv.fr/communes?nom={urllib.parse.quote(pdv_attribs.get('ville'))}&codePostal={urllib.parse.quote(pdv_attribs.get('cp'))}&boost=population&limit=5&geometry=bbox&fields=nom,code,codeDepartement,siren,codeEpci,codeRegion,codesPostaux,population,bbox")
            bbox_response = bbox_response[0].get('bbox')
            # Create Point objects
            p_ordered = Point(float(longitude_original)/100000.0, float(latitude_original)/100000.0)
            p_reversed = Point(float(latitude_original)/100000.0, float(longitude_original)/100000.0)
            # Create a Polygon
            poly = shape(bbox_response)
            print(f'Point within commune bbox {p_ordered.within(poly)}')
            print(f'Point reversed within commune bbox {p_reversed.within(poly)}')
            print("")

        if pdv_attribs["cp"][0:2] not in ['97', '98'] and latitude is not None and not 41.3900000000000006 < latitude < 51.0659999999999954:
            print('Latitude issue')
            print(f"{pdv_attribs.get('longitude', '')},{pdv_attribs.get('latitude', '')}")
            print(f"Original: {longitude_original}, {latitude_original}")
            print(pdv_attribs)
            bbox_response = getJSON(f"https://geo.api.gouv.fr/communes?nom={urllib.parse.quote(pdv_attribs.get('ville'))}&codePostal={urllib.parse.quote(pdv_attribs.get('cp'))}&boost=population&limit=5&geometry=bbox&fields=nom,code,codeDepartement,siren,codeEpci,codeRegion,codesPostaux,population,bbox")
            bbox_response = bbox_response[0].get('bbox')
            # Create Point objects
            p_ordered = Point(float(longitude_original)/100000.0, float(latitude_original)/100000.0)
            p_reversed = Point(float(latitude_original)/100000.0, float(longitude_original)/100000.0)
            # Create a Polygon
            poly = shape(bbox_response)
            print(f'{latitude}, {longitude}')
            print(f'Point within commune bbox {p_ordered.within(poly)}')
            print(f'Point reversed within commune bbox {p_reversed.within(poly)}')
            print("")

        if longitude_original == '0' or latitude_original == '0':
            print("Coordonnées à 0")
            print(pdv_attribs)

        pdv_attribs['longitude'] = longitude
        pdv_attribs['latitude'] = latitude

        # print(pdv_attribs)
        horaires = pdv.find('horaires')
        # print(horaires.attrib)
        if horaires is not None:
            jours = horaires.getchildren()
            jour_and_horaires = [{**jour.find('horaire').attrib, **jour.attrib} if jour.find('horaire') is not None else jour.attrib for jour in jours]
            # jour_and_horaires = [{"station_id": pdv_attribs.get('id'), "id": d.get('id'), "nom": d.get('nom'), "ferme": d.get('ferme'), "ouverture": d.get('ouverture'), "fermeture": d.get('fermeture')} for d in jour_and_horaires]
            # print(jour_and_horaires)
            horaires_attrib = horaires.attrib
            content["jour_and_horaires"] = jour_and_horaires
        else:
            horaires_attrib = {}
        if pdv.findall('ouverture') is not None:
            ouvertures = [ouverture.attrib for ouverture in pdv.findall('ouverture') if bool(ouverture.attrib)]
            content["ouvertures"] = ouvertures
        content = {**pdv_attribs,**horaires_attrib}
        services_text = [service.text for service in pdv.findall('services/service')]
        all_services += services_text
        content["services_text"] = services_text
        
        # print(services_text)
        prix = [service.attrib for service in pdv.findall('prix') if bool(service.attrib)]
        prix = sorted(prix, key=lambda d: datetime.fromisoformat(d['maj']).timestamp())

        content["prix"] = prix
        ruptures = [rupture.attrib for rupture in pdv.findall('rupture') if bool(rupture.attrib)]
        content["ruptures"] = ruptures
        fermetures = [fermeture.attrib for fermeture in pdv.findall('fermeture') if bool(fermeture.attrib)]
        content["fermetures"] = fermetures
        geojson_content = {
          "type": "Feature",
          "properties": content,
          "geometry": {
            "type": "Point",
            "coordinates": [
              pdv_attribs['longitude'],
              pdv_attribs['latitude']
            ] if pdv_attribs['longitude'] != '' else None
          }
        }
        features.append(geojson_content)

        csv_output_content["services_text"] = [{'station_id': pdv_attribs.get('id'), "service": service} for service in services_text]
        if horaires is not None:
            csv_output_content["jour_and_horaires"] = [dict(item, **{'station_id': content.get('id')}) for item in jour_and_horaires]
        else:
            csv_output_content["jour_and_horaires"] = []
        if pdv.findall('ouverture') is not None:
            csv_output_content["ouvertures"] = [dict(item, **{'station_id': content.get('id')}) for item in ouvertures]
        else:
            csv_output_content["ouvertures"] = []
        csv_output_content["fermetures"] = [dict(item, **{'station_id': content.get('id')}) for item in fermetures]
        csv_output_content["ruptures"] = [dict(item, **{'station_id': content.get('id')}) for item in ruptures]
        csv_output_content["prix"] = [dict(item, **{'station_id': content.get('id')}) for item in prix]
        csv_output_content["stations"] = pdv_attribs

        contents.append(csv_output_content)
        
    except Exception as e:
        raise e


configs = [
    {'name': 'ouvertures', 'fieldnames': ['debut', 'fin', 'saufjour', 'station_id']},
    {'name': 'jour_and_horaires', 'fieldnames': ['id', 'nom', 'ouverture', 'fermeture', 'ferme', 'station_id']},
    {'name': 'services_text', 'fieldnames': ['service', 'station_id']},
    {'name': 'prix', 'fieldnames': ['id', 'nom', 'maj', 'valeur', 'station_id']},
    {'name': 'ruptures', 'fieldnames': ['id', 'nom', 'debut', 'fin', 'station_id']},
    {'name': 'fermetures', 'fieldnames': ['debut', 'fin', 'type', 'station_id']}
]
configs = [conf for conf in configs if conf.get('name') in csv_output_content.keys()]
# import ipdb;ipdb.set_trace()

for config in configs:
    with open(f'{config.get("name")}.csv', 'w', newline='') as csvfile:
        all_content = [i.get(f'{config.get("name")}') for i in contents]
        all_content = list(chain(*all_content))
        writer = csv.DictWriter(csvfile, fieldnames=config.get("fieldnames"))
        writer.writeheader()
        writer.writerows(all_content)

# import ipdb;ipdb.set_trace()
with open(f'stations.csv', 'w', newline='') as csvfile:
    all_content = [i.get(f'stations') for i in contents]
    writer = csv.DictWriter(csvfile, fieldnames=['id', 'latitude', 'longitude', 'cp', 'pop', 'adresse', 'ville'])
    writer.writeheader()
    writer.writerows(all_content)

out_geojson = {
  "type": "FeatureCollection",
  "features": features
}

with open('stations_with_info.geojson', 'w') as outfile: 
    json.dump(out_geojson, outfile)

# print(set(all_services))
    
# Si API
# Infos par station
# Recherche prix par date
# Recherche si ouvert
# Recherche Géo (soit dedans soir à proximité)
# Recherche par dispo carburant
# Recherche date disparition carburant
# Recherche par type de service
# Recherche si rupture
