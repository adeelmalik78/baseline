# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Liquibase database baseline project for Microsoft SQL Server. The workflow captures a snapshot of an existing MSSQL database schema and splits it into individual, organized SQL files in Liquibase-formatted SQL format.

## Workflow

**Step 1 — Generate baseline changelog** from the live database:
```bash
# macOS/Linux
./baseline.sh

# Windows (PowerShell)
./baseline.ps1
```

Both scripts:
1. Delete any existing `baseline.mssql.sql` and `baseline/sqls/` directory
2. Run `liquibase generate-changelog` to capture the full database schema
3. Run `python3 split_sql.py baseline.mssql.sql` to split the monolithic changelog into individual files

**Step 2 — Run the splitter directly** (if you already have a baseline file):
```bash
python3 split_sql.py baseline.mssql.sql
```

## Database Connection

Configured in [liquibase.properties](liquibase.properties):
- **DB**: `jdbc:sqlserver://demo-db1-win.liquibase.net:1433;databaseName=npt_dev`
- **Schemas captured**: `adeel1`, `dbo` (excludes `sys`, `information_schema`)
- **Changelog file**: `src/master_changelog.xml`

## Output Structure

The splitter (`split_sql.py`) classifies each changeset by SQL object type and writes individual `.sql` files to:

```
baseline/sqls/
├── tables/        # CREATE TABLE statements
├── views/         # CREATE VIEW (runOnChange:true, endDelimiter:GO)
├── procedures/    # CREATE/ALTER PROCEDURE (runOnChange:true, endDelimiter:GO)
├── functions/     # CREATE FUNCTION (runOnChange:true, endDelimiter:GO)
├── triggers/      # CREATE TRIGGER (runOnChange:true, endDelimiter:GO)
├── indexes/       # CREATE INDEX
├── constraints/   # ALTER TABLE ... ADD CONSTRAINT
├── sequences/     # CREATE SEQUENCE
├── synonyms/      # CREATE SYNONYM
├── types/         # CREATE TYPE
├── schemas/       # CREATE SCHEMA
└── other/         # Anything unclassified
```

Files are named `schema.ObjectName.sql`. Duplicates get a numeric suffix (`_1`, `_2`, etc.).

## Key Behavior in split_sql.py

- **Procedure detection takes priority over table detection** — procedures that contain `CREATE TABLE` in their body are correctly classified as procedures, not tables.
- **Procedures**: If the content starts with `if object_id(...)`, a `GO` delimiter is injected after that line before the `ALTER PROCEDURE` body.
- **Stored routines** (views, procedures, functions, triggers): Always get `runOnChange:true endDelimiter:GO` appended to the changeset line, and a `GO` statement appended at the end.
- **Tables/indexes/constraints**: Get `splitStatements:true` only (from the source changeset line).
- The Liquibase header (everything before the first changeset) is discarded — only individual changesets are written to files.

## Liquibase Commands

To apply the baseline to a database after splitting:
```bash
liquibase --changelog-file=baseline.mssql.sql update
```
(This line is commented out in both shell scripts — uncomment to run.)
