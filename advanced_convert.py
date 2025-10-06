import pandas as pd
import json
from datetime import datetime

class DateTimeEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle datetime objects, which are not
    natively serializable.
    """
    def default(self, obj):
        if isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)

def get_sheet_names(file_path):
    """Prints the names of all sheets in an Excel file."""
    try:
        xls = pd.ExcelFile(file_path)
        print("Sheet names:", xls.sheet_names)
        return xls.sheet_names
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def process_sheet(file_path, sheet_name):
    """
    Processes a single sheet from the Excel file, handling complex headers
    and preserving all data.
    """
    try:
        # Read the raw data from the sheet without assuming any header
        df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

        # Attempt to find the main data table and headers
        header_row_index = -1
        for i, row in df_raw.iterrows():
            if row.notna().sum() > df_raw.shape[1] / 2:
                header_row_index = i
                break

        if header_row_index == -1:
            return {"sheet_name": sheet_name, "data_type": "non_tabular", "content": df_raw.to_dict(orient='records')}

        pre_header_data = df_raw.iloc[:header_row_index].dropna(how='all').to_dict(orient='records')
        df_data = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row_index)
        df_data.columns = [str(col) if 'Unnamed' not in str(col) else f"col_{i}" for i, col in enumerate(df_data.columns)]

        post_header_data_start_index = header_row_index + len(df_data) + 1
        post_header_data = df_raw.iloc[post_header_data_start_index:].dropna(how='all').to_dict(orient='records')

        return {
            "sheet_name": sheet_name,
            "pre_header_info": pre_header_data,
            "table_data": df_data.to_dict(orient='records'),
            "post_header_info": post_header_data
        }

    except Exception as e:
        print(f"An error occurred while processing sheet '{sheet_name}': {e}")
        return {"sheet_name": sheet_name, "error": str(e)}

def convert_excel_to_structured_json(file_path, output_path):
    """
    Converts an Excel file with multiple sheets and complex layouts into a
    structured JSON file.
    """
    sheet_names = get_sheet_names(file_path)
    if not sheet_names:
        return

    all_sheets_data = []
    for sheet_name in sheet_names:
        print(f"Processing sheet: {sheet_name}")
        sheet_data = process_sheet(file_path, sheet_name)
        all_sheets_data.append(sheet_data)

    # Save the structured data to a JSON file using the custom encoder
    with open(output_path, "w") as json_file:
        json.dump(all_sheets_data, json_file, indent=4, cls=DateTimeEncoder)

    print(f"Successfully converted Excel to structured JSON at '{output_path}'")


# Configuration
EXCEL_FILE = "Provider Services per Location (A&A + RISE) (1).xlsx"
JSON_OUTPUT_FILE = "data_final.json"

# Run the conversion
if __name__ == "__main__":
    convert_excel_to_structured_json(EXCEL_FILE, JSON_OUTPUT_FILE)