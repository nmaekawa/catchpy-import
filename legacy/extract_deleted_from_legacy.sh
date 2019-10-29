#!/bin/bash
source dotenvfile

for context in `cat archive/context_id_for_deleted.txt`
do
    echo "***********************************************************"
    echo "*  processing ${context}"
    echo "*"
    echo "./migrate.py pull_all --outdir ./archive/batch1 --source_url $MIGRATION_SERVER_URL --api_key $MIGRATION_API_KEY --secret_key $MIGRATION_SECRET_KEY --context_id '${context}' --reuse_outdir"
    ./migrate.py pull_all --outdir ./archive/batch1 --source_url "${MIGRATION_SERVER_URL}" --api_key "${MIGRATION_API_KEY}" --secret_key "${MIGRATION_SECRET_KEY}" --context_id "${context}" --reuse_outdir
    echo "*"
    echo "***********************************************************"
done
