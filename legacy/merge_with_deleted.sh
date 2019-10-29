#!/bin/bash
source ~/.venvs/catchpy/bin/activate

mkdir -p archive/batch3_list

for f in `ls archive/batch3_convert/catcha_course*`
do
    echo "***********************************************************"
    echo "*  processing ${f}"
    echo "*"
    cat $f | jq .catcha_list > archive/batch3_list/list_$(basename $f)
    echo "*"
    echo "***********************************************************"
done

mkdir -p archive/batch3_to_import

for f in `ls archive/batch3_list/list_catcha_course*`
do
    echo "***********************************************************"
    course_name=$(basename $f | sed 's/list_catcha_//g')
    echo "*  MERGING ${course_name}"
    echo "*"
    jq -s add $f archive/batch3_list/list_catcha_deleted_$course_name > archive/batch3_to_import/import_$course_name
done
