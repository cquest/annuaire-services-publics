# Ecrit par Christian Quest le 24/2/2016
#
# ce code est sous licence WTFPL
# dernière version disponible sur https://github.com/cquest/annuaire-services-publics

from bs4 import BeautifulSoup
import requests
import sys
import re
import json

x = BeautifulSoup(sys.stdin,'lxml')

# si pas de date de mise à jou c'est qu'on est sur une liste
if x.organisme is None:
    sys.exit(0)

# id utilisé sur le site de la DILA que l'on conserve
f = dict(id=x.organisme.get('id'),nom=x.nom.string)
f.update(editeursource=x.editeursource.string)
f.update(codeinsee=x.organisme.get('codeinsee'))
f.update(update=x.organisme.get('datemiseajour'))
f.update(type=x.organisme.get('pivotlocal'))
if x.latitude is not None:
  f.update(latitude=x.latitude.string)
  f.update(longitude=x.longitude.string)
  f.update(geocode_pr=x.pr.string)
if x.accessibilit is not None:
  f.update(accessibilite_type=x.accessibilit.get('type'))
  f.update(accessibilite_text=x.accessibilit.string)

# nom de l'entité + coordonnées (fax, téléphone, email, formulaire contact, sites web)
if x.coordonn is not None:
  if x.coordonn.email is not None:
    f.update(contact_email = x.coordonn.email.string)
  if x.coordonn.url is not None:
    www = list()
    for w in x.find_all('url'):
      www.append(w.string)
    f.update(website=www)
  if x.coordonn.telephone is not None:
    f.update(contact_phone=x.coordonn.telephone.string)
  if x.coordonn.telecopie is not None:
    f.update(contact_fax=x.coordonn.telecopie.string)
  
# adresse postale
adresse = x.find(type='postale')
if adresse is None:
  adresse = x.find(type='géopostale')
if adresse is not None:
  if adresse.find_all('ligne') is not None:
    a = list()
    for l in adresse.find_all('ligne'):
      a.append(l.string)
  adr = dict(streetAddress=a)

  if adresse.codepostal is not None:
    adr.update(postalCode=adresse.codepostal.string.strip())
  if adresse.nomcommune is not None:
    adr.update(addressLocality=adresse.nomcommune.string.strip())

  f.update(writeAddress=adr)


# géocodage de l'adresse physique
adresse = x.find(type='physique')
if adresse is None:
  adresse = x.find(type='géopostale')
if adresse is not None:
  adr = ''
  if adresse.find_all('ligne') is not None:
    for a in adresse.find_all('ligne'):
      if a.string is not None:
        adr = adr + a.string + " "
    adr = adr + adresse.codepostal.string + ' ' + adresse.nomcommune.string
    adr = re.sub('  ',' ',adr).strip()
    if adr != '':
      # appel de l'API BAN
      r=requests.get('http://api-adresse.data.gouv.fr/search/',params={'q':adr, 'limit':'1','autocomplete':'0'})
      if len(json.loads(r.text)['features'])>0:
        geocode = json.loads(r.text)['features'][0]
        # extraction des champs utiles
        geo = dict(score=round(geocode['properties']["score"],2), latitude=geocode['geometry']['coordinates'][1], longitude=geocode['geometry']['coordinates'][0], address_found=geocode['properties']["label"], address_type=geocode['properties']["type"], address_id=geocode['properties']["id"], commune=geocode['properties']["city"], insee_comm=geocode['properties']["citycode"],source="BAN/ODbL 1.0", address_searched=adr)
        f.update(geo=geo)

if x.commentaire is not None:
  f.update(commentaire=x.commentaire.string)


print(json.dumps(f,sort_keys=True, separators=(',', ': ')))
