# récupération des pages HTML
wget -nc -nv -r -np https://lannuaire.service-public.fr/institutions-juridictions -R .js,.css,.png,.jpg,.html,.gif,*.txt --accept-regex 'institution|gouvernement|ambassade|autorite'

# extraction des données (HTML > json) + géocodage
rm annuaire.sjson 
for f in */*/*; do
  echo "$f"
  python extract.py "$f" >> annuaire.sjson
done

# conversion partielle en CSV
echo "id,source,name,update,type,parent_id,parent_name,contact_email,contact_form,contact_phone,contact_fax,website,streetAddress,postOfficeBoxNumber,postalCode,addressLocality,addressCountry,latitude,longitude" | sed 's/,/\t/g' > annuaire.csv
cat annuaire.sjson | jq --raw-output '"\(.id)\t\(.source)\t\(.name)\t\(.update)\t\(.type)\t\(.parent_id)\t\(.parent_name)\t\(.contact_email)\t\(.contact_form)\t\(.contact_phone)\t\(.contact_fax)\t\(.website[0])\t\(.writeAddress.streetAddress)\t\(.writeAddress.postOfficeBoxNumber)\t\(.writeAddress.postalCode)\t\(.writeAddress.addressLocality)\t\(.writeAddress.addressCountry)\t\(.geo.latitude)\t\(.geo.longitude)"' | sed 's/\tnull/\t/g' >> annuaire.csv

# conversion CSV vers GeoJSON (avec csvkit)
grep "[0-9e]$" annuaire.csv  | csvjson --lat latitude --lon longitude -k id -t > annuaire.geojson

# extraction des URL des sites web
cat annuaire.sjson | jq .website | grep http | sort -u | sed 's/ "//;s/"//;s/,$//' | sort -u > websites.txt

