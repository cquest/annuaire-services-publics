rm -f all_latest.tar.bz2
rm -rf locales
wget http://lecomarquage.service-public.fr/donnees_locales_v2/all_latest.tar.bz2
tar -jxf all_latest.tar.bz2
rm all_latest.tar.bz2
mv all_* locales

cd locales/organismes
for d in *; do
  rm -f ../../annuaire-$d.sjson
  for f in $d/*.xml; do
    sed 's/ début=/ debut=/g;s/<Télé/<tele/g;s/<\/Télé/<\/tele/g' "$f" | python3 ../../convert-locales.py >> ../../annuaire-$d.sjson
  done
done

