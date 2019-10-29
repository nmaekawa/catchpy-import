#!/bin/bash

reportfile="report_from_original.txt"

total=0
total_deleted=0
echo "course, regular, deleted, total" >> archive/$reportfile

for course in `cat archive/courses_to_import.txt`
do
    echo "***********************************************************"
    echo "*  processing ${course}"
    echo "*"

    counter=$(mysql -h 10.10.10.10 -u root -pcatch migration -Ns --delimiter=',' \
        -e "select count(*) from annotation where context_id = '$course';" \
        2>/dev/null)
    counter_deleted=$(mysql -h 10.10.10.10 -u root -pcatch migration -Ns --delimiter=',' \
        -e "select count(*) from annotation where context_id = 'deleted_$course';" \
        2>/dev/null)

    let "course_total=$counter+$counter_deleted"
    echo "$course, $counter, $counter_deleted, $course_total" >> archive/$reportfile

    let "total=$total+$counter"
    let "total_deleted=$total_deleted+$counter_deleted"

    echo "*"
    echo "***********************************************************"
done

let "total_total=$total+$total_deleted"
echo "total, $total, $total_deleted, $total_total" >> archive/$reportfile
