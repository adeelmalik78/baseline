BASELINE_CHANGELOG_FILE="baseline.mssql.sql"

if [ -z ${BASELINE_CHANGELOG_FILE} ]; then
    rm -f ${BASELINE_CHANGELOG_FILE}
fi

if [ -d "baseline/sqls" ]; then
    rm -rf baseline/sqls
fi

liquibase --changelog-file=${BASELINE_CHANGELOG_FILE} generate-changelog --diff-types="tables,columns,indexes,foreignkeys,primarykeys,uniqueconstraints,functions,views,storedprocedures,triggers,sequences,catalogs,schemas"

ls -alh ${BASELINE_CHANGELOG_FILE}

python3 split_sql.py ${BASELINE_CHANGELOG_FILE}