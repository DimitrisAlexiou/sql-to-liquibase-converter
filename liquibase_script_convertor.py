import re
import os
from datetime import datetime

def clean_sql_content(content):
    """Clean up SQL content while preserving essential whitespace."""
    # Remove comments
    content = re.sub(r'--.*$', '', content, flags=re.MULTILINE)
    # Normalize whitespace but preserve newlines for readability
    content = re.sub(r'\s+', ' ', content)
    return content.strip()

def escape_xml_chars(text):
    """Escape special characters for XML."""
    replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&apos;'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def convert_sql_to_liquibase(input_file, output_file):
    # Read the SQL file
    with open(input_file, "r", encoding="utf-8") as file:
        sql_content = clean_sql_content(file.read())

    # Extract INSERT statements
    insert_pattern = re.findall(r"INSERT INTO ([\w_.]+)\s*\((.*?)\)\s*VALUES\s*(.*?);", sql_content, re.DOTALL)

    # Generate timestamp for changeset ID
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Start Liquibase XML structure
    xml_output = f"""<?xml version="1.0" encoding="UTF-8"?>
<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog
                       http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-4.26.xsd">

    <changeSet author="your_author" id="your_id_{timestamp}">
"""

    # Process each INSERT statement
    for table_name, columns, values in insert_pattern:
        # Remove database prefix
        table_name = table_name.split('.')[-1]
        
        # Process columns
        columns_list = [col.strip() for col in columns.split(",")]
        
        # Process values
        rows = re.findall(r"\((.*?)\)", values, re.DOTALL)
        
        for row in rows:
            values_list = []
            current = []
            in_quote = False
            
            # Parse values maintaining proper quoting
            for char in row:
                if char == "'" and (not current or current[-1] != '\\'):
                    in_quote = not in_quote
                    current.append(char)
                elif char == ',' and not in_quote:
                    values_list.append(''.join(current).strip())
                    current = []
                else:
                    current.append(char)
            
            if current:
                values_list.append(''.join(current).strip())
            
            # Clean and process values
            values_list = [val.strip().strip("'") for val in values_list]

            # Generate insert XML
            xml_output += f'        <insert tableName="{table_name}">\n'
            for col, val in zip(columns_list, values_list):
                if val.upper() == "NULL":
                    xml_output += f'            <column name="{col}"/>\n'
                else:
                    val = escape_xml_chars(val)
                    xml_output += f'            <column name="{col}" value="{val}"/>\n'
            xml_output += "        </insert>\n"

    # Close XML structure
    xml_output += """    </changeSet>
</databaseChangeLog>
"""

    # Write output
    with open(output_file, "w", encoding="utf-8") as output_file:
        output_file.write(xml_output)

if __name__ == "__main__":
    input_file = "inserts.sql"
    output_file = "liquibase_inserts.xml"
    
    convert_sql_to_liquibase(input_file, output_file)
    print(f"Conversion completed! Check '{output_file}'")