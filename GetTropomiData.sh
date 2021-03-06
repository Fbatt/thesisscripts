#!/bin/bash


#design:
#input: should be a date
#1-run a API query to figure out the first 3 uuid's are sorted by clouds
#2-check if the .nc files associated with the uuid's are already downloaded
#3-if they aren't, download them.


wget --no-check-certificate --user=s5pguest --password=s5pguest --output-document=query_results.txt "https://s5phub.copernicus.eu/dhus/search?q=ingestiondate:[NOW-1DAY TO NOW] AND producttype:L2__NO2___&rows=1&start=0&format=json"

mytmp=$(cat query_results.txt | jq -r '.feed.entry|.id')
#note the -r switch makes the output a bash-readable string which echo's out as e.g. 3432525 instead of a json string like "3432525"

#(DEBUG)echo "NOTICE ME. this is the uuid:"$mytmp
#(DEBUG)example UUID = "b776e767-1004-40ed-b1f8-b50f0cfc83d4"

bigstring='https://s5phub.copernicus.eu/dhus/odata/v1/Products('"'"${mytmp}"'"')/$value'
#how to get this to format correctly: it needs to be https://s5phub....Products('2342-242')/$Value  note he single quotes around the number, and absence of \ before $ when not feeding it directly as string to command but rather through a variable
#thus I've inserted single quotes in two double quotes, which simplify to single quotes

#(DEBUG)echo "formatting check, im passing along: ${bigstring}"

wget --content-disposition --continue --user=s5pguest --password=s5pguest ${bigstring}
#wget --content-disposition --continue --user=s5pguest --password=s5pguest "https://s5phub.copernicus.eu/dhus/odata/v1/Products('b776e767-1004-40ed-b1f8-b50f0cfc83d4')/\$value"

