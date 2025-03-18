import re
import csv
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

class LiquibaseConverter:
    XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog
                       http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-4.26.xsd">
    <changeSet author="your_author" id="your_id_{timestamp}">
{content}
    </changeSet>
</databaseChangeLog>
"""

    def __init__(self, input_file: str, output_xml_file: str, output_csv_file: str = None):
        self.input_file = input_file
        self.output_xml_file = output_xml_file
        self.output_csv_file = output_csv_file
        self.timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    def convert(self):
        """Main conversion method that orchestrates the conversion process."""
        sql_content = self._read_sql_file()
        insert_statements = self._extract_insert_statements(sql_content)
        
        # Generate XML
        xml_content = self._generate_xml_content(insert_statements)
        self._write_output_file(xml_content)
        
        # Generate CSV if output_csv_file is provided
        if self.output_csv_file:
            self._generate_csv_file(insert_statements)

    def _read_sql_file(self) -> str:
        """Read and clean SQL content from input file."""
        with open(self.input_file, "r", encoding="utf-8") as file:
            return clean_sql_content(file.read())

    def _extract_insert_statements(self, sql_content: str) -> list:
        """Extract INSERT statements from SQL content."""
        return re.findall(
            r"INSERT INTO ([\w_.]+)\s*\((.*?)\)\s*VALUES\s*(.*?);", 
            sql_content, 
            re.DOTALL
        )

    def _parse_values_row(self, row: str) -> list:
        """Parse a single row of values maintaining proper quoting."""
        values_list = []
        current = []
        in_quote = False
        
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
        
        return [val.strip().strip("'") for val in values_list]

    def _generate_column_xml(self, column: str, value: str) -> str:
        """Generate XML for a single column."""
        if value.upper() == "NULL":
            return f'            <column name="{column}"/>'
        return f'            <column name="{column}" value="{escape_xml_chars(value)}"/>'

    def _generate_xml_content(self, insert_statements: list) -> str:
        """Generate XML content from INSERT statements."""
        xml_inserts = []
        
        for table_name, columns, values in insert_statements:
            table_name = table_name.split('.')[-1]
            columns_list = [col.strip() for col in columns.split(",")]
            rows = re.findall(r"\((.*?)\)", values, re.DOTALL)
            
            for row in rows:
                values_list = self._parse_values_row(row)
                insert_xml = ['        <insert tableName="{}">'.format(table_name)]
                
                for col, val in zip(columns_list, values_list):
                    insert_xml.append(self._generate_column_xml(col, val))
                    
                insert_xml.append("        </insert>")
                xml_inserts.append('\n'.join(insert_xml))

        return self.XML_TEMPLATE.format(
            timestamp=self.timestamp,
            content='\n'.join(xml_inserts)
        )

    def _write_output_file(self, content: str):
        """Write the generated XML content to output file."""
        with open(self.output_xml_file, "w", encoding="utf-8") as output_file:
            output_file.write(content)

    def _generate_csv_file(self, insert_statements: list):
        """Generate CSV file from INSERT statements."""
        csv_data = []
        
        for table_name, columns, values in insert_statements:
            columns_list = [col.strip() for col in columns.split(",")]
            rows = re.findall(r"\((.*?)\)", values, re.DOTALL)
            
            for row in rows:
                values_list = self._parse_values_row(row)
                # Create a dictionary for each row
                row_dict = {}
                for col, val in zip(columns_list, values_list):
                    row_dict[col] = val if val.upper() != "NULL" else ""
                csv_data.append(row_dict)

        # Write to CSV file
        if csv_data:
            headers = list(csv_data[0].keys())
            with open(self.output_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                writer.writerows(csv_data)

def convert_sql_to_liquibase(input_file: str, output_xml_file: str, output_csv_file: str = None):
    """Main function to convert SQL to Liquibase XML and optionally to CSV."""
    converter = LiquibaseConverter(input_file, output_xml_file, output_csv_file)
    converter.convert()

if __name__ == "__main__":
    input_file = "inserts.sql"
    output_xml_file = "liquibase_inserts.xml"
    output_csv_file = "inserts.csv"
    
    convert_sql_to_liquibase(input_file, output_xml_file, output_csv_file)
    print(f"Conversion completed! Check '{output_xml_file}' for XML output")
    print(f"CSV file created at '{output_csv_file}'")