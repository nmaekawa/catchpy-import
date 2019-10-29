#!/bin/bash
#source dotenvfile
source ~/.venvs/catchpy/bin/activate

mkdir -p archive/batch3_convert

for f in `ls archive/batch3/fullset_annojs_course*`
do
    echo "***********************************************************"
    echo "*  processing ${f}"
    echo "*"
    course_name=$(basename $f | sed 's/fullset_annojs_//g')
    echo "* ${course_name}"
    ~/Documents/devo/catchpy/manage.py convert --filepath ${f} > archive/batch3_convert/catcha_${course_name}
    ~/Documents/devo/catchpy/manage.py convert --filepath archive/batch3/fullset_annojs_deleted_${course_name} > archive/batch3_convert/catcha_deleted_${course_name}
    echo "*"
    echo "***********************************************************"
done
