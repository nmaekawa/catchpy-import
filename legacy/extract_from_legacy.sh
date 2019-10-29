#!/bin/bash
source 201901/dotenvfile

for context in `cat 201901/catch_context_id_recent.txt`
do
    echo "***********************************************************"
    echo "*  processing ${context}"
    echo "*"
    echo "./migrate.py pull-all --outdir ./201901/batch2-recent --source_url $MIGRATION_SERVER_URL --api_key $MIGRATION_API_KEY --secret_key $MIGRATION_SECRET_KEY --context_id '${context}' --reuse_outdir"
    ./migrate.py pull-all --outdir ./201901/batch2-recent --source_url "${MIGRATION_SERVER_URL}" --api_key "${MIGRATION_API_KEY}" --secret_key "${MIGRATION_SECRET_KEY}" --context_id "${context}" --reuse_outdir
#    ./migrate.py pull-all --outdir ./201901/batch2-recent --source_url "${MIGRATION_SERVER_URL}" --api_key "${MIGRATION_API_KEY}" --secret_key "${MIGRATION_SECRET_KEY}" --context_id "deleted_${context}" --reuse_outdir
    echo "*"
    echo "***********************************************************"
done
