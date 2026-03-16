$env:BASELINE_CHANGELOG_FILE = "baseline.mssql.sql"

if (Test-Path $env:BASELINE_CHANGELOG_FILE) {
    Remove-Item $env:BASELINE_CHANGELOG_FILE -Force
}

if (Test-Path "baseline" -PathType Container) {
    Remove-Item "baseline" -Recurse -Force
}

liquibase --changelog-file=$env:BASELINE_CHANGELOG_FILE generate-changelog 

Get-Item $env:BASELINE_CHANGELOG_FILE | Select-Object Name, Length, LastWriteTime

python split_sql.py $env:BASELINE_CHANGELOG_FILE
