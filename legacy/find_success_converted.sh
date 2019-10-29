#!/bin/bash

data_dir="archive/batch3_convert"

for course in `cat archive/courses_to_import.txt`
do
    echo "***********************************************************"
    echo "*  processing ${course}"
    echo "*"

    course_clean=$(echo $course | sed -e 's/[^a-zA-Z0-9]/_/g')
    cat $data_dir/catcha_${course_clean}.json | jq '.catcha_list[].id' >> all_converted_ids.txt
    cat $data_dir/catcha_deleted_${course_clean}.json | jq '.catcha_list[].id' >> all_converted_ids.txt

    echo "*"
    echo "***********************************************************"
done

cat all_converted_ids.txt | sort > converted_all_id.txt

psql -d naomi61 -tA -F' '\
    -c "select anno_id from anno_anno order by anno_id;" >> imported_all_id.txt


