$BASELINE_CHANGELOG_FILE = "baseline.mssql.sql"

if (Test-Path $BASELINE_CHANGELOG_FILE) {
    Remove-Item $BASELINE_CHANGELOG_FILE -Force
}

if (Test-Path "baseline\sqls" -PathType Container) {
    Remove-Item "baseline\sqls" -Recurse -Force
}

liquibase --changelog-file=$BASELINE_CHANGELOG_FILE generate-changelog --diff-types="tables,columns,indexes,foreignkeys,primarykeys,uniqueconstraints,functions,views,storedprocedures,triggers,sequences,catalogs,schemas"

Get-Item $BASELINE_CHANGELOG_FILE | Select-Object Name, Length, LastWriteTime

python split_sql.py $BASELINE_CHANGELOG_FILE