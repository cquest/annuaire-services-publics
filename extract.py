# Ecrit par Christian Quest le 13/2/2016
#
# ce code est sous licence WTFPL
# dernière version disponible sur https://github.com/cquest/annuaire-services-publics

from bs4 import BeautifulSoup
import requests
import sys
import re
import json

html = BeautifulSoup(open(sys.argv[1]),'lxml')

# si pas de date de mise à jou c'est qu'on est sur une liste
if html.find(id='contentLastUpdate') is None:
    sys.exit(0)

# id utilisé sur le site de la DILA que l'on conserve
f = dict(id=re.sub(r"^.*_", "", sys.argv[1]), source="http://"+sys.argv[1])

# type d'entité
f.update(type=re.sub('.*/(.*)_.*','\\1',sys.argv[1]))

# date de mise à jour des informations
u = re.sub(' - .*$','',html.find(id='contentLastUpdate').string)
# transforme "01 octobre 2015" en "2015-octobre-01"
u = re.sub('(.*) (.*) (.*)','\\3-\\2-\\1',u)
# remplacement mois texte et numérique ("2015-octobre-01" -> "2015-10-01")
mois = {'janvier':'01','février':'02','mars':'03','avril':'04','mai':'05','juin':'06','juillet':'07','août':'08','septembre':'09','octobre':'10','novembre':'11','décembre':'12'}
for t, n in mois.items():
    u = u.replace(t, n)
f.update(update=u)

# nom de l'entité + coordonnées (fax, téléphone, email, formulaire contact, sites web)
f.update(name=html.find(id='contentTitle').string)
if html.find(id="contentFax_1") is not None:
  f.update(contact_fax=html.find(id="contentFax_1").string)
if html.find(id="contentPhone_1") is not None:
  f.update(contact_phone = html.find(id="contentPhone_1").string)
if html.find(id="contentContactEmail") is not None:
  f.update(contact_email = html.find(id="contentContactEmail").string.replace(' [ à ] ','@').replace('\n',''))
if html.find(id="contentContactForm") is not None:
  f.update(contact_form = html.find(id="contentContactForm").get("href"))
if html.find_all(id=re.compile("website")) is not None:
  www = list()
  for w in html.find_all(id=re.compile("website")):
    www.append(w.get("href"))
  f.update(website=www)

# adresse postale
a = ""
adresse = html.find(attrs={"data-test":"writeAddress"})
if adresse is not None:
  if adresse.find_all(itemprop="streetAddress") is not None:
    for l in adresse.find_all(itemprop="streetAddress"):
      a = a+l.string
      if l.string.strip()==l.string:
        a = a + ", "
  adr = dict(streetAddress=re.sub(', $','',a))

  if adresse.find(itemprop="postOfficeBoxNumber") is not None:
    adr.update(postOfficeBoxNumber=adresse.find(itemprop="postOfficeBoxNumber").string)
  if adresse.find(itemprop="postalCode") is not None:
    if adresse.find(itemprop="postalCode").string is not None:
      adr.update(postalCode=adresse.find(itemprop="postalCode").string.strip())
  if adresse.find(itemprop="addressLocality") is not None:
    adr.update(addressLocality=adresse.find(itemprop="addressLocality").string)
  if adresse.find(itemprop="addressCountry") is not None:
    adr.update(addressCountry=adresse.find(itemprop="addressCountry").string)

  f.update(writeAddress=adr)

# lien avec parent
bc = html.find(class_="breadcrumb")
if bc is not None:
  bc = bc.find_all("span")
  f.update(parents=int((len(bc))/2)-1)
  parents = list()
  for parent in bc[2:]:
    if parent.find("a") is not None:
      parents.append(parent.find("a").string)
  f.update(parents_name=parents)
  parent = bc[len(bc)-2].find("a")
  f.update(parent_name=parent.string)
  f.update(parent_id=re.sub(r"[^0-9]*", "",parent.get("href")))

# responsables (ordre, nom, titre, fonction, email, téléphone, fax)
if html.find(class_="list-responsable") is not None:
    resp_noms = html.find(class_="list-responsable").find_all(id=re.compile("accountable"))
    p = list()
    num = 0
    for resp in resp_noms:
        personne = resp.find_parent("div")
        people = dict(role=personne.find("h3").string.strip())
        num = num+1
        people.update(order=num)
        nom=re.sub('[, ] .*$','',personne.find(id=re.compile("accountable")).string)
        people.update(name=nom)
        t=personne.find(id=re.compile("accountable")).string
        t=t[t.find(',')+1:].strip()
        if t != nom:
            people.update(title=t)
        for contact in personne.find_all("span"):
            contact_type = contact.string
            c = contact.find_parent("p")
            c.span.decompose()
            if (contact_type == "Courriel : "):
                people.update(email=c.string.replace(' [ à ] ','@'))
            if (contact_type == "Téléphone : "):
                people.update(phone=c.string)
        p.append(people)
    if False: # pas de sortie des données nominatives par défaut
      f.update(people=p)

# géocodage de l'adresse physique
if html.find("div",itemprop='address') is not None:
  adr = ''
  if html.find("div",itemprop='address').find(id="contentCountry") is None:
    for a in html.find("div",itemprop='address').find_all(id="contentAddressName"):
      if a.string is not None:
        adr = adr + a.string + " "
    adr = re.sub('  ',' ',adr).strip()
    if adr != '':
      # appel de l'API BAN
      r=requests.get('http://api-adresse.data.gouv.fr/search/',params={'q':adr, 'limit':'1','autocomplete':'0'})
      if len(json.loads(r.text)['features'])>0:
        geocode = json.loads(r.text)['features'][0]
        # extraction des champs utiles
        geo = dict(score=round(geocode['properties']["score"],2), latitude=geocode['geometry']['coordinates'][1], longitude=geocode['geometry']['coordinates'][0], address_found=geocode['properties']["label"], address_type=geocode['properties']["type"], address_id=geocode['properties']["id"], commune=geocode['properties']["city"], insee_comm=geocode['properties']["citycode"],source="BAN/ODbL 1.0", address_searched=adr)
        f.update(geo=geo)

# texte de référence
if html.find(id=re.compile("contentReferences")) is not None:
  textes = list()
  for t in html.find_all(id=re.compile("contentReferences")):
    t.span.extract()
    textes.append({ 'title': t.string, 'url': re.sub(' .*','',t.get("href"))})
  f.update(ref=textes)

# texte d'introduction
if html.find(id="contentIntroduction") is not None:
  f.update(intro=html.find(id="contentIntroduction").strong.replace_with("").string)

print(json.dumps(f,sort_keys=True, separators=(',', ': ')))

