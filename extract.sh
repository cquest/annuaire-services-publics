wget -nc -nv -r -np https://lannuaire.service-public.fr/institutions-juridictions -R .js,.css,.png,.jpg,.html,.gif,*.txt --accept-regex 'juridiction|gouvernement|ambassade|autorite'

rm annuaire.sjson 
for f in */*/*; do
  echo "$f"
  python extract.py "$f" >> annuaire.sjson
done

