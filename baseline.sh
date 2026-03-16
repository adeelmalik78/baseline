BASELINE_CHANGELOG_FILE="baseline.mssql.sql"
BASELINE_DATA_CHANGELOG_FILE="baseline_data.mssql.sql"

if [ -z ${BASELINE_CHANGELOG_FILE} ]; then
    rm -f ${BASELINE_CHANGELOG_FILE}
fi

if [ -d "baseline" ]; then
    rm -rf baseline
fi

# Generate baseline for objects
liquibase --changelog-file=${BASELINE_CHANGELOG_FILE} generate-changelog \
    --exclude-objects="schema:sys,schema:information_schema,table:DATABASECHANGELOG,table:DATABASECHANGELOGLOCK"
ls -alh ${BASELINE_CHANGELOG_FILE}
python3 split_sql.py ${BASELINE_CHANGELOG_FILE}

# Generate data for specific tables (only if table arguments are provided)
if [ $# -gt 0 ]; then
    liquibase --changelog-file="${BASELINE_DATA_CHANGELOG_FILE}" generate-changelog \
        --diff-types="data" --include-objects="$@"
    ls -alh ${BASELINE_DATA_CHANGELOG_FILE}
    python3 split_sql.py "${BASELINE_DATA_CHANGELOG_FILE}"
else
    echo "No data was requested. If you need data, run ..."
    echo " ./baseline.sh table:<table1>,table:<table2>,..."
    echo "e.g., "
    echo "./baseline.sh table:ProductCategory,table:Address"
fi
