#!/usr/bin/env python3
import os
import re
import sys

# Check for command-line argument
if len(sys.argv) < 2:
    print("Error: No input file specified")
    print("Usage: python3 split_sql.py <path_to_sql_file>")
    print("Example: python3 split_sql.py baseline.mssql.sql")
    sys.exit(1)

# Read the baseline file from command-line argument
baseline_file = sys.argv[1]

# Check if file exists
if not os.path.exists(baseline_file):
    print(f"Error: File '{baseline_file}' not found")
    sys.exit(1)

print(f"Processing file: {baseline_file}")

with open(baseline_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Split by changeset comments
changesets = re.split(r'(-- changeset [^\n]+)', content)

# First element is the liquibase header
liquibase_header = changesets[0].strip()

# Create base directory (use the directory of the input file)
base_dir = os.path.dirname(os.path.abspath(baseline_file))

# Create directories for each object type
directories = {
    'tables': os.path.join(base_dir, 'baseline/sqls/tables'),
    'functions': os.path.join(base_dir, 'baseline/sqls/functions'),
    'views': os.path.join(base_dir, 'baseline/sqls/views'),
    'procedures': os.path.join(base_dir, 'baseline/sqls/procedures'),
    'triggers': os.path.join(base_dir, 'baseline/sqls/triggers'),
    'synonyms': os.path.join(base_dir, 'baseline/sqls/synonyms'),
    'sequences': os.path.join(base_dir, 'baseline/sqls/sequences'),
    'indexes': os.path.join(base_dir, 'baseline/sqls/indexes'),
    'constraints': os.path.join(base_dir, 'baseline/sqls/constraints'),
    'types': os.path.join(base_dir, 'baseline/sqls/types'),
    'schemas': os.path.join(base_dir, 'baseline/sqls/schemas'),
    'other': os.path.join(base_dir, 'baseline/sqls/other'),
    'data': os.path.join(base_dir, 'baseline/sqls/data')
}

for dir_path in directories.values():
    os.makedirs(dir_path, exist_ok=True)

# Counters for naming files
counters = {key: 1 for key in directories.keys()}

# Accumulator for INSERT INTO statements grouped by schema.table
data_inserts = {}

# Process changesets
i = 1
while i < len(changesets):
    if i >= len(changesets):
        break

    changeset_line = changesets[i].strip()

    if i + 1 < len(changesets):
        sql_content = changesets[i + 1].strip()
    else:
        sql_content = ''

    if not sql_content:
        i += 2
        continue

    # Determine object type and extract name
    object_type = None
    object_name = None
    schema_name = None

    # IMPORTANT: Check for PROCEDURE first (before TABLE) because procedures may contain CREATE TABLE in their body
    # Check for PROCEDURE (both CREATE PROCEDURE and if object_id patterns)
    if 'PROCEDURE' in sql_content.upper() or "'p'" in sql_content.lower() or "'P'" in sql_content:
        proc_match = re.search(r"object_id\('(\w+)'", sql_content)
        if not proc_match:
            proc_match = re.search(r'(?:CREATE|ALTER) PROCEDURE (?:\[?(\w+)\]?\.)?(\[?\w+\]?)', sql_content, re.IGNORECASE)
            if proc_match:
                schema_name = proc_match.group(1).strip('[]') if proc_match.group(1) else None
                object_name = proc_match.group(2).strip('[]') if proc_match.group(2) else proc_match.group(1).strip('[]')
        else:
            object_name = proc_match.group(1)
        object_type = 'procedures'

    # Check for FUNCTION (must be "CREATE FUNCTION" as a statement, not just keyword)
    elif re.search(r'CREATE\s+FUNCTION', sql_content, re.IGNORECASE):
        func_match = re.search(r'CREATE FUNCTION (?:\[?(\w+)\]?\.)?(\[?\w+\]?)', sql_content, re.IGNORECASE)
        if func_match:
            schema_name = func_match.group(1).strip('[]') if func_match.group(1) else None
            object_name = func_match.group(2).strip('[]') if func_match.group(2) else func_match.group(1).strip('[]')
            object_type = 'functions'

    # Check for VIEW (must be "CREATE VIEW" as a statement, not just keyword)
    elif re.search(r'CREATE\s+VIEW', sql_content, re.IGNORECASE):
        view_match = re.search(r'CREATE VIEW (?:\[?(\w+)\]?\.)?(\[?\w+\]?)', sql_content, re.IGNORECASE)
        if view_match:
            schema_name = view_match.group(1).strip('[]') if view_match.group(1) else None
            object_name = view_match.group(2).strip('[]') if view_match.group(2) else view_match.group(1).strip('[]')
            object_type = 'views'

    # Check for TRIGGER (must be "CREATE TRIGGER" as a statement, not just keyword)
    elif re.search(r'CREATE\s+TRIGGER', sql_content, re.IGNORECASE):
        trigger_match = re.search(r'CREATE TRIGGER (?:\[?(\w+)\]?\.)?(\[?\w+\]?)', sql_content, re.IGNORECASE)
        if trigger_match:
            schema_name = trigger_match.group(1).strip('[]') if trigger_match.group(1) else None
            object_name = trigger_match.group(2).strip('[]') if trigger_match.group(2) else trigger_match.group(1).strip('[]')
            object_type = 'triggers'

    # Check for SYNONYM (must be "CREATE SYNONYM" as a statement, not just keyword)
    elif re.search(r'CREATE\s+SYNONYM', sql_content, re.IGNORECASE):
        synonym_match = re.search(r'CREATE SYNONYM (?:\[?(\w+)\]?\.)?(\[?\w+\]?)', sql_content, re.IGNORECASE)
        if synonym_match:
            schema_name = synonym_match.group(1).strip('[]') if synonym_match.group(1) else None
            object_name = synonym_match.group(2).strip('[]') if synonym_match.group(2) else synonym_match.group(1).strip('[]')
            object_type = 'synonyms'

    # Check for SEQUENCE (must be "CREATE SEQUENCE" as a statement, not just keyword)
    elif re.search(r'CREATE\s+SEQUENCE', sql_content, re.IGNORECASE):
        sequence_match = re.search(r'CREATE SEQUENCE (?:\[?(\w+)\]?\.)?(\[?\w+\]?)', sql_content, re.IGNORECASE)
        if sequence_match:
            schema_name = sequence_match.group(1).strip('[]') if sequence_match.group(1) else None
            object_name = sequence_match.group(2).strip('[]') if sequence_match.group(2) else sequence_match.group(1).strip('[]')
            object_type = 'sequences'

    # Check for TYPE (user-defined types)
    elif re.search(r'CREATE\s+TYPE', sql_content, re.IGNORECASE):
        type_match = re.search(r'CREATE TYPE (?:\[?(\w+)\]?\.)?(\[?\w+\]?)', sql_content, re.IGNORECASE)
        if type_match:
            schema_name = type_match.group(1).strip('[]') if type_match.group(1) else None
            object_name = type_match.group(2).strip('[]') if type_match.group(2) else type_match.group(1).strip('[]')
            object_type = 'types'

    # Check for SCHEMA (must be "CREATE SCHEMA" as a statement)
    elif re.search(r'CREATE\s+SCHEMA', sql_content, re.IGNORECASE):
        schema_match = re.search(r'CREATE SCHEMA \[?(\w+)\]?', sql_content, re.IGNORECASE)
        if schema_match:
            object_name = schema_match.group(1).strip('[]')
            object_type = 'schemas'

    # Check for INDEX (must be "CREATE...INDEX" as a statement, not just keywords)
    elif re.search(r'CREATE\s+(?:\w+\s+)?INDEX', sql_content, re.IGNORECASE):
        index_match = re.search(r'CREATE (?:\w+ )?INDEX (\w+)', sql_content, re.IGNORECASE)
        index_schema_match = re.search(r'\bON\s+\[?(\w+)\]?\.\[?\w+\]?', sql_content, re.IGNORECASE)
        if index_match:
            object_name = index_match.group(1)
            schema_name = index_schema_match.group(1).strip('[]') if index_schema_match else None
            object_type = 'indexes'

    # Check for ALTER TABLE (constraints) - must start with ALTER TABLE
    elif re.match(r'^\s*ALTER\s+TABLE', sql_content, re.IGNORECASE):
        constraint_match = re.search(r'ADD CONSTRAINT (\w+)', sql_content, re.IGNORECASE)
        alter_schema_match = re.search(r'ALTER TABLE \[?(\w+)\]?\.\[?\w+\]?', sql_content, re.IGNORECASE)
        if constraint_match:
            object_name = constraint_match.group(1)
            schema_name = alter_schema_match.group(1).strip('[]') if alter_schema_match else None
            object_type = 'constraints'

    # Check for CREATE TABLE (checked last to avoid matching CREATE TABLE inside procedures)
    # Only match if CREATE TABLE appears near the start (within first 50 chars) to avoid matching it inside procedure bodies
    elif sql_content.upper().find('CREATE TABLE') < 50 and sql_content.upper().find('CREATE TABLE') != -1:
        table_match = re.search(r'CREATE TABLE (\[?(\w+)\]?\.)?(\[?\w+\]?)', sql_content, re.IGNORECASE)
        if table_match:
            object_type = 'tables'
            schema_name = table_match.group(2).strip('[]') if table_match.group(2) else None
            object_name = table_match.group(3).strip('[]')

    # Check for INSERT INTO statements - collect grouped by schema.table
    elif re.search(r'^\s*INSERT\s+INTO', sql_content, re.IGNORECASE | re.MULTILINE):
        insert_match = re.search(r'INSERT\s+INTO\s+\[?(\w+)\]?\.\[?(\w+)\]?', sql_content, re.IGNORECASE)
        if insert_match:
            table_key = f'{insert_match.group(1).strip("[]")}.{insert_match.group(2).strip("[]")}'
        else:
            bare_match = re.search(r'INSERT\s+INTO\s+\[?(\w+)\]?', sql_content, re.IGNORECASE)
            table_key = bare_match.group(1).strip('[]') if bare_match else 'unknown'
        if table_key not in data_inserts:
            data_inserts[table_key] = []
        data_inserts[table_key].append((changeset_line, sql_content))
        counters['data'] += 1
        i += 2
        continue

    # Default to other if we can't determine
    if not object_type:
        object_type = 'other'
        object_name = f'object_{counters[object_type]}'

    # Sanitize object name for filename, prefixing schema if available
    if object_name:
        base = f'{schema_name}.{object_name}' if schema_name else object_name
        filename = re.sub(r'[^\w\-_.]', '_', base)
    else:
        filename = f'{object_type}_{counters[object_type]}'

    # Create the file
    file_path = os.path.join(directories[object_type], f'{filename}.sql')

    # Handle duplicate filenames
    original_file_path = file_path
    counter = 1
    while os.path.exists(file_path):
        file_path = os.path.join(directories[object_type], f'{filename}_{counter}.sql')
        counter += 1

    # Write the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('-- liquibase formatted sql\n')

        # For functions, procedures, triggers, and views, append endDelimiter:GO and runOnChange:true to changeset line
        if object_type in ['functions', 'procedures', 'triggers', 'views']:
            f.write(f'{changeset_line} runOnChange:true endDelimiter:GO\n')
        else:
            f.write(f'{changeset_line}\n')

        # For procedures, check if content starts with "if object_id" and add GO after that line
        if object_type == 'procedures':
            lines = sql_content.split('\n')
            if lines and re.match(r'^\s*if\s+object_id', lines[0], re.IGNORECASE):
                # Write first line (if object_id line)
                f.write(lines[0] + '\n')
                # Add GO
                f.write('GO\n')
                # Write remaining lines
                remaining_content = '\n'.join(lines[1:])
                f.write(remaining_content)
                if not remaining_content.endswith('\n'):
                    f.write('\n')
            else:
                f.write(sql_content)
                if not sql_content.endswith('\n'):
                    f.write('\n')
        else:
            f.write(sql_content)
            if not sql_content.endswith('\n'):
                f.write('\n')

        # For functions, procedures, triggers, and views, add GO as the final line
        if object_type in ['functions', 'procedures', 'triggers', 'views']:
            f.write('GO\n')

    counters[object_type] += 1
    i += 2

# Write grouped INSERT INTO data files
for table_key, entries in data_inserts.items():
    filename = re.sub(r'[^\w\-_.]', '_', table_key)
    file_path = os.path.join(directories['data'], f'{filename}.sql')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('-- liquibase formatted sql\n')
        for changeset_line, sql_content in entries:
            f.write(f'{changeset_line}\n')
            f.write(sql_content)
            if not sql_content.endswith('\n'):
                f.write('\n')

print("File splitting complete!")
print(f"\nTotal changesets processed: {(len(changesets) - 1) // 2}")
print("\nSummary:")
for obj_type, count in counters.items():
    actual_count = count - 1
    if actual_count > 0:
        print(f"  {obj_type}: {actual_count} files")

# Generate changelog.yml in the baseline directory
# Order matters for Liquibase: schemas -> types -> sequences -> tables -> indexes -> constraints -> views -> functions -> procedures -> triggers -> synonyms -> other
ordered_types = [
    'schemas',
    'types',
    'sequences',
    'tables',
    'indexes',
    'constraints',
    'views',
    'functions',
    'procedures',
    'triggers',
    'synonyms',
    'other',
    'data',
]

changelog_path = os.path.join(base_dir, 'baseline', 'changelog.yml')
with open(changelog_path, 'w', encoding='utf-8') as f:
    f.write('databaseChangeLog:\n')
    for obj_type in ordered_types:
        f.write(f'  - includeAll:\n')
        f.write(f'      path: sqls/{obj_type}/\n')
        f.write(f'      relativeToChangelogFile: true\n')
        f.write(f'      endsWithFilter: .sql\n')
        f.write(f'      errorIfMissingOrEmpty: false\n')

print(f"\nGenerated: {changelog_path}")
