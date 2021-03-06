#! /bin/bash

mkdir /data/
if [ $# -eq 0 ]
  then
    echo "Arquivo ou json de entrada nao informado. Executando coleta com arquivo de entrada padrao."
    cp exemplos/input_instagram.json /data/
    docker run -v "/data:/var/instagram-crawler" --rm instagram_mp_v1 python3 /home/mp/coletor-instagram/main.py input_instagram.json
fi
if [ $# -eq 1 ]
  then
    docker run -v "/data:/var/instagram-crawler" --rm instagram_mp_v1 python3 /home/mp/coletor-instagram/main.py "$1"
fi
if [ $# -eq 2 ]
  then
    docker run -v "/data:/var/instagram-crawler" --rm instagram_mp_v1 python3 /home/mp/coletor-instagram/main.py -d "$2"
fi
