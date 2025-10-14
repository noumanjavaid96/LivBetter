# Excel to CSV and JSON Conversion for Notion Import

This project processes a multi-sheet Excel file (`Provider Services per Location (A&A + RISE) (1).xlsx`) and converts it into a single, clean CSV file (`notion_database.csv`) and a corresponding JSON file (`notion_database.json`), both suitable for data import and analysis.

## `notion_database.csv`

This is the final, consolidated CSV file. It contains 46 columns, formatted to be easily imported into applications like Notion. The data has been cleaned, standardized, and consolidated from the various sheets of the original Excel file.

### Office Hours Consolidation

A key transformation in this project is the consolidation of office hours. The `format_hours.py` script processes the 'Provider Days', 'Provider Hours', and 'General Office Hours' columns and creates a single, human-readable "Combined Office Hours" column in the final CSV.

The logic is as follows:
1.  If the `General Office Hours` column has a value, it is used for the `Combined Office Hours` column.
2.  If `General Office Hours` is empty, the script combines the `Provider Days` and `Provider Hours` columns.
3.  The resulting string is then placed in the `Combined Office Hours` column.

## `notion_database.json`

This file is a JSON representation of the final `notion_database.csv`. The `convert_to_json.py` script was used to generate this file, ensuring that any `NaN` or empty values from the CSV are converted to `null` to maintain JSON validity. This makes the data suitable for use in web applications and other systems that consume JSON.