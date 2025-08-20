#!/bin/bash

cd /usr/local/meltano/mysql-snowflake-sync

[ -f $HYPERPLANE_CUSTOM_SECRET_KEY_TARGET_SNOWFLAKE_SECRET_PATH ] && echo "key file exists." || echo "key file does not exist."
cp $HYPERPLANE_CUSTOM_SECRET_KEY_TARGET_SNOWFLAKE_SECRET_PATH snowflake_private_key.p8

export AWS_ENDPOINT_URL=$HYPERPLANE_CUSTOM_SECRET_KEY_AWS_ENDPOINT_URL
export AWS_ACCESS_KEY_ID=$HYPERPLANE_CUSTOM_SECRET_KEY_AWS_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY=$HYPERPLANE_CUSTOM_SECRET_KEY_AWS_SECRET_ACCESS_KEY
export MELTANO_STATE_BACKEND_URI=$HYPERPLANE_CUSTOM_SECRET_KEY_MELTANO_STATE_BACKEND_URI
export AWS_DEFAULT_REGION='us-east-1'

echo "token: $AWS_ACCESS_KEY_ID:$AWS_SECRET_ACCESS_KEY"
meltano config meltano set state_backend.uri "${HYPERPLANE_CUSTOM_SECRET_KEY_MELTANO_STATE_BACKEND_URI}"
meltano config meltano set state_backend.s3.endpoint_url $HYPERPLANE_CUSTOM_SECRET_KEY_AWS_ENDPOINT_URL
meltano config meltano set state_backend.s3.aws_access_key_id $AWS_ACCESS_KEY_ID
meltano config meltano set state_backend.s3.aws_secret_access_key $AWS_SECRET_ACCESS_KEY

cat $HYPERPLANE_CUSTOM_SECRET_KEY_TARGET_SNOWFLAKE_SECRET_PATH
meltano config tap-mysql set database $HYPERPLANE_CUSTOM_SECRET_KEY_SOURCE_MYSQL_DB
meltano config tap-mysql set user $HYPERPLANE_CUSTOM_SECRET_KEY_SOURCE_MYSQL_USER
meltano config tap-mysql set host $HYPERPLANE_CUSTOM_SECRET_KEY_SOURCE_MYSQL_HOST
meltano config tap-mysql set port $HYPERPLANE_CUSTOM_SECRET_KEY_SOURCE_MYSQL_PORT
meltano config tap-mysql set password $HYPERPLANE_CUSTOM_SECRET_KEY_SOURCE_MYSQL_PW

meltano remove loader target-snowflake
meltano add loader target-snowflake  --no-install
sed -i 's/pip_url: meltanolabs-target-snowflake/pip_url: meltanolabs-target-snowflake==v0.17.1/' "meltano.yml"
meltano install loader
meltano config target-snowflake set account $HYPERPLANE_CUSTOM_SECRET_KEY_TARGET_SNOWFLAKE_ACCOUNT
meltano config target-snowflake set database $HYPERPLANE_CUSTOM_SECRET_KEY_TARGET_SNOWFLAKE_DB
meltano config target-snowflake set user $HYPERPLANE_CUSTOM_SECRET_KEY_TARGET_SNOWFLAKE_USER
meltano config target-snowflake set role $HYPERPLANE_CUSTOM_SECRET_KEY_TARGET_SNOWFLAKE_ROLE
meltano config target-snowflake set warehouse $HYPERPLANE_CUSTOM_SECRET_KEY_TARGET_SNOWFLAKE_WH
meltano config target-snowflake set default_target_schema $HYPERPLANE_CUSTOM_SECRET_KEY_TARGET_SNOWFLAKE_SCHEMA
meltano config target-snowflake set batch_size_rows 5000 # Half the batch

meltano config target-snowflake set add_record_metadata true
meltano config target-snowflake set private_key_path snowflake_private_key.p8
meltano config target-snowflake set validate_records false
meltano config meltano set elt.buffer_size 92428800
meltano config meltano set database_uri postgresql+psycopg://supabase_admin:Q9EnohfTpz@supabase-pgbouncer.hyperplane-supabase:6432/postgres

# TODO
meltano config tap-mysql set _metadata '*' replication-method INCREMENTAL # Change this to cursor
# TODO: Use Meltano config cli to set metadata with replication key. where the replication method => incremental.
meltano config tap-mysql set _metadata '*' replication-key $HYPERPLANE_JOB_PARAMETER_INCREMENTAL_KEY


DIR="/tmp/git/monorepo/meltano-mysql-snowflake-job/spawner_prod_hp/stream_maps"
# Initialize dbt_enabled variable
# Loop through all .sql files in the directory
for file in "$DIR"/*.sh; do
    # Check if any files exist
    if [[ ! -e "$file" ]]; then
        echo "No sh files found in $DIR."
        break
    fi
    # Extract the file name without the .sql extension
    filename=$(basename "$file" .sh)
    # Check if the cleaned filename is part of the SYNC_PATTERN environment variable
    if [[ "$HYPERPLANE_JOB_PARAMETER_REGEX_TO_SYNC" == *"$filename"* ]]; then
        # If it's in SYNC_PATTERN, copy the file to the DBT models directory
        echo "$filename.sh detected, copying into folder..."
        bash "$DIR/$filename.sh"
    fi
done


export MELTANO_SEND_ANONYMOUS_USAGE_STATS=false


IFS=':' read -ra ADDR <<< "$HYPERPLANE_JOB_PARAMETER_REGEX_TO_SYNC" #REGEX_TO_SYNC is :-deliminated i.e. "!stingray-e:!stingray-f:[y-z]"
for item in "${ADDR[@]}"; do
    meltano select tap-mysql "$item"
done

# for debugging
cat meltano.yml
cat .env

# run sync
export LAST_PART=$(echo ${HYPERPLANE_JOB_PARAMETER_REGEX_TO_SYNC} | awk -F: '{print $NF}')

meltano run tap-mysql target-snowflake  --state-id-suffix ${LAST_PART}-prod-hp --force ${HYPERPLANE_JOB_PARAMETER_EXTRA_FLAG}