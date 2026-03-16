$env:BASELINE_CHANGELOG_FILE = "baseline.mssql.sql"
$env:BASELINE_DATA_CHANGELOG_FILE = "baseline_data.mssql.sql"

if (Test-Path $env:BASELINE_CHANGELOG_FILE) {
    Remove-Item $env:BASELINE_CHANGELOG_FILE -Force
}

if (Test-Path "baseline" -PathType Container) {
    Remove-Item "baseline" -Recurse -Force
}

# Generate baseline for objects
liquibase --changelog-file=$env:BASELINE_CHANGELOG_FILE generate-changelog `
    --exclude-objects="schema:sys,schema:information_schema,table:DATABASECHANGELOG,table:DATABASECHANGELOGLOCK"
Get-Item $env:BASELINE_CHANGELOG_FILE | Select-Object Name, Length, LastWriteTime
python split_sql.py $env:BASELINE_CHANGELOG_FILE

# Generate data for specific tables (only if table arguments are provided)
if ($args.Count -gt 0) {
    liquibase --changelog-file=$env:BASELINE_DATA_CHANGELOG_FILE generate-changelog `
        --diff-types="data" --include-objects="$($args -join ',')"
    Get-Item $env:BASELINE_DATA_CHANGELOG_FILE | Select-Object Name, Length, LastWriteTime
    python split_sql.py $env:BASELINE_DATA_CHANGELOG_FILE
} else {
    Write-Host "No data was requested. If you need data, run ..."
    Write-Host " .\baseline.ps1 table:<table1>,table:<table2>,..."
    Write-Host "e.g., "
    Write-Host ".\baseline.ps1 table:ProductCategory,table:Address"
}
