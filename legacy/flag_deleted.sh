#!/bin/bash
#source dotenvfile
source ~/.venvs/catchpy/bin/activate

mkdir -p archive/batch3_list

for f in `ls archive/batch3_convert/catcha_deleted*`
do
    echo "***********************************************************"
    echo "*  processing ${f}"
    echo "*"
    echo "* ${f}"
    cat $f | jq .catcha_list | ./set_deleted.py > archive/batch3_list/list_$(basename $f)
    echo "*"
    echo "***********************************************************"
done
