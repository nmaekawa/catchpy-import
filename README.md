catchpy migration script
========================

Script to migrate annotations from catch v1 to catchpy v2.

The script works in steps:

1. pull annotation set from v1 given a context_id; and save to file
2. from annojs saved file, convert to catchpy webAnnotation format, and save to
   file
3. from converted saved file, push webAnnotations into catchpy v2
4. pull imported annotations from catchpy v2 via annojs api, and save to file
5. compare original set of annojs from v1 with imported annojs from v2

Each step will save annotatations that failed into a file, in order to keep
track of which annotation failed [[when.]]

to install
==========

You will need to have the catchpy django app repo
(https://github.com/nmaekawa/catchpy) at the same level as this catchpy
migration script repo (https://github.com/nmaekawa/catchpy-import).

The script will import directly into the database configured in catchpy django
settings, so the configured database user has to have grants into the database
from the box the script is running.

The default django settings is `catchpy.settings.dev`, but you can configure
it in the environment as env var `DJANGO_SETTINGS_MODULE`.

This scripts requires python 3.5 or higher.


step-by-step
============

    # clone catchpy django app and migrate script repos
    $> git clone https://github.com/nmaekawa/catchpy.git
    $> git clone https://github.com/nmaekawa/catchpy-import.git
    
    # create virtualenv and install requirements
    $> virtualenv -p python3 $VENVS/catchpy-import
    $> source $VENVS/catchpy-import/bin/activate
    $(catchpy-import)> cd catchpy-import
    # this refers to ../catchpy/requirements/base.txt
    $(catchpy-import)> pip install -r requirements.txt
    
    # check commands
    $(catchpy-import)> ./migrate.py
    Usage: migrate.py [OPTIONS] COMMAND [ARGS]...
    
    Options:
      --help  Show this message and exit.
    
      Commands:
        clear_anno_in_context_id
        compare_annojs            works like file1 contains file2, so set the...
        convert
        find_reply_to_reply
        make_token
        pull_all
        push_from_file
    
    # get help with input arguments
    $(catchpy-import)> ./migrate.py pull_all --help
    ...
    
    # the order of commands would be something like below
    # we are pulling from v1(source) to import into catchpy v2(target)
    
    # pull annotations from catch v1
    $(catchpy-import)> ./migrate.py pull_all --outdir pull_source \
        --source_url https://catch.harvardx.harvard.edu/catch/annotator/search \
        --api_key <consumer_key> \
        --secret_key <secret_key> \
        --context_id course-v1:HarvardX+GA001+2015
    
    # convert to webannotation
    $(catchpy-import)> mkdir convert
    $(catchpy-import)> ./migrate.py convert --workdir convert \
        --filpath ./pull_all/fullset_annojs_course_v1_HarvardX_GA001_2015.json
    
    # push to db
    $(catchpy-import)> mkdir push_from_file
    $(catchpy-import)> ./migrate.py push_from_file --workdir push_from_file \
        --filepath convert/catcha_fullset_annojs_course_v1_HarvardX_GA001_2015.json
    
    # pull from catchpy v2 as annotatorjs
    $(catchpy-import)> ./migrate.py pull_all --outdir pull_target \
        --source_url https://catchpy.harvardx.harvard.edu/annos/search \
        --api_key <v2_consumer_key> \
        --secret_key <v2_secret_key> \
        --context_id course-v1:HarvardX+GA001+2015
    
    # compare original and imported; file1 must be original, file2 must be imported
    $(catchpy-import)> mkdir compare
    $(catchpy-import)> ./migrate.py compare_annojs --workdir compare \
        --input_filepath_1 pull_source/fullset_fullset_annojs_course_v1_HarvardX_GA001_2015.json \
        --input_filepath_2 pull_target/fullset_fullset_annojs_course_v1_HarvardX_GA001_2015.json



eof
