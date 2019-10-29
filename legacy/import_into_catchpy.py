#!/bin/bash
source ~/.venvs/catchpy/bin/activate

mkdir -p archive/batch3_convert

for f in `ls archive/batch3_to_import/import_*`
do
    echo "***********************************************************"
    echo "*  processing ${f}"
    echo "*"
    course_name=$(basename $f | sed 's/import_//g')
    echo "* ${course_name}"
    ~/Documents/devo/catchpy/manage.py import --filepath ${f} > archive/batch3_to_import/log_${course_name}
    echo "*"
    echo "***********************************************************"
done
