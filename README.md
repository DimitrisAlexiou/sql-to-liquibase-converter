# SQL to Liquibase Converter

A Python utility that converts SQL INSERT statements into Liquibase XML changesets. Specifically designed to handle multi-line SQL inserts with proper handling of special characters, NULL values, and database schema prefixes. Ideal for database migration projects and version control of database changes.

## Features

- Converts SQL INSERT statements to Liquibase XML format
- Handles multi-line SQL inserts
- Properly escapes special characters
- Supports NULL values
- Removes database schema prefixes
- Generates unique changeset IDs with timestamps

## Usage

1. Place your SQL file with INSERT statements in the same directory as the script
2. Run the script:
```bash
python liquibase_script_convertor.py
```
3. Check the generated `liquibase_inserts.xml` file

## Requirements

- Python 3.6+
