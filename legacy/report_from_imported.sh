#!/bin/bash

reportfile="report_from_imported.txt"

total=0
total_deleted=0
echo "course, regular, deleted, total" >> archive/$reportfile

for course in `cat archive/courses_to_import.txt`
do
    echo "***********************************************************"
    echo "*  processing ${course}"
    echo "*"

    counter=$(psql -d naomi61 -tA \
        -c "select count(*) from anno_anno where raw->'platform'->>'context_id' = '$course' and anno_deleted = false")
    counter_deleted=$(psql -d naomi61 -tA \
        -c "select count(*) from anno_anno where raw->'platform'->>'context_id' = '$course' and anno_deleted = true")

    let "course_total=$counter+$counter_deleted"
    echo "$course, $counter, $counter_deleted, $course_total" >> archive/$reportfile

    let "total=$total+$counter"
    let "total_deleted=$total_deleted+$counter_deleted"

    echo "*"
    echo "***********************************************************"
done

let "total_total=$total+$total_deleted"
echo "total, $total, $total_deleted, $total_total" >> archive/$reportfile
