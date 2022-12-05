
if [ "$1" == "zamknij_swoje" ]; then
  runner --send mission --send medic --credits-range 15k-100k --shared-mission
fi

if [ "$1" == "zamknij_sojusz" ]; then
  runner --send mission --send medic --credits-range 0-100k --alliance=True --own=False --only-new-missions=False
fi

moje
 runner --send mission --send medic --credits-range 0-100k --sleep=0

