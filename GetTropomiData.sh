#!/bin/bash


#design:
#input: should be a date
#1-run a API query to figure out the first 3 uuid's are sorted by clouds
#2-check if the .nc files associated with the uuid's are already downloaded
#3-if they aren't, download them.


#wget --no-check-certificate --user=s5pguest --password=s5pguest --output-document=query_results.txt "https://s5phub.copernicus.eu/dhus/search?q=ingestiondate:[NOW-1DAY TO NOW] AND producttype:L2__NO2___&rows=100&start=0&format=json"

#cat query_results.txt | jq '.feed.entry|.[]|.id'

#UUID = "b776e767-1004-40ed-b1f8-b50f0cfc83d4"

wget --content-disposition --continue --user=s5pguest --password=s5pguest "https://s5phub.copernicus.eu/dhus/odata/v1/Products('b776e767-1004-40ed-b1f8-b50f0cfc83d4')/\$value"

