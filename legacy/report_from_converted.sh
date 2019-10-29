#!/bin/bash

reportfile="report_from_converted.txt"
data_dir="archive/batch3_convert"
echo "course, success, success_deleted, total_success, failed, failed_deleted total_failed" >> archive/$reportfile

total_success=0
total_failed=0
total_r_failed=0
total_d_failed=0

for course in `cat archive/courses_to_import.txt`
do
    echo "***********************************************************"
    echo "*  processing ${course}"
    echo "*"

    course_clean=$(echo $course | sed -e 's/[^a-zA-Z0-9]/_/g')
    r_success=$(cat $data_dir/catcha_${course_clean}.json | jq '.total_success')
    r_failed=$(cat $data_dir/catcha_${course_clean}.json | jq '.total_failed')
    d_success=$(cat $data_dir/catcha_deleted_${course_clean}.json | jq '.total_success')
    d_failed=$(cat $data_dir/catcha_deleted_${course_clean}.json | jq '.total_failed')

    let "c_success=$r_success+$d_success"
    let "c_failed=$r_failed+$d_failed"
    echo "$course, $r_success, $d_success, $c_success, $r_failed, $d_failed_deleted $c_failed" >> archive/$reportfile

    let "total_success=$total_success+$c_success"
    let "total_failed=$total_failed+$c_failed"
    let "total_r_failed=$total_r_failed+$r_failed"
    let "total_d_failed=$total_d_failed+$d_failed"

    echo "*"
    echo "***********************************************************"
done

echo "total, $total_success, $total_failed, $total_r_failed, $total_d_failed" >> archive/$reportfile
