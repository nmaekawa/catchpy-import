#!/bin/bash

for course in `cat archive/courses_to_import.txt`
do
    echo "***********************************************************"
    echo "*  processing ${course}"
    echo "*"

    mysql -h 10.10.10.10 -u root -pcatch migration -Ns \
        -e "select '${course}', id from annotation where context_id = 'deleted_$course' order by id;" \
        2>/dev/null >> original_deleted_id.txt

    psql -d naomi61 -tA -F' '\
        -c "select raw->'platform'->>'context_id', anno_id from anno_anno where raw->'platform'->>'context_id' = '$course' and anno_deleted = true;" \
        >> imported_deleted_id.txt

done

cat original_deleted_id.txt | sort > deleted_original.txt
cat imported_deleted_id.txt | sort > deleted_imported.txt

echo "*"
echo "***********************************************************"
