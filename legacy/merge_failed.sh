#!/bin/bash
source dotenvfile

for course_id in `cat archive/clean_courses_id.txt`
do
    echo "***********************************************************"
    echo "*  processing ${annojs}"
    echo "*"
    course_id_clean=$(echo $course_id | sed -e 's/[^a-zA-Z0-9]/_/g')
    echo "*   course_id_clean is ${course_id_clean}"
    cat archive/batch1_convert2/fullset_annojs_$course_id_clean.json | jq .annojs_failed_list > archive/batch1_complete/failed_annojs.json
    cat archive/batch1_convert2_deleted/converted_fullset_annojs_deleted_$course_id_clean.json >> archive/batch1_complete/failed_annojs.json
    echo "*"
    echo "***********************************************************"
done
