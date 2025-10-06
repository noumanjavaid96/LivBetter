import pandas as pd
import json
import os
import sys
import google.generativeai as genai
from datetime import datetime

# --- Gemini AI Configuration ---
try:
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise KeyError("GEMINI_API_KEY environment variable not set.")
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-flash-latest')
except KeyError as e:
    print(f"Error: {e}")
    model = None
except Exception as e:
    print(f"An error occurred during Gemini AI configuration: {e}")
    model = None

class DateTimeEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle datetime objects, which are not
    natively serializable.
    """
    def default(self, obj):
        if isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)

def get_gemini_analysis(sheet_name, data):
    """
    Analyzes the sheet data using the Gemini API and returns a summary.
    """
    if not model:
        return "Gemini AI analysis could not be performed. API key may be missing or invalid."

    prompt = f"""
    Analyze the following JSON data from a spreadsheet sheet named '{sheet_name}'.
    The data includes pre-header information, a main data table, and post-header information.
    Your task is to:
    1. Provide a concise summary of the sheet's purpose and content.
    2. Interpret the structure and key information present in the data.
    3. Confirm that the data appears complete and makes sense in the context of a "Provider Services per Location" document.

    Data:
    {json.dumps(data, indent=2, cls=DateTimeEncoder)}
    """
    try:
        print(f"  - Requesting Gemini analysis for '{sheet_name}'...")
        response = model.generate_content(prompt)
        print(f"  - Received Gemini analysis for '{sheet_name}'.")
        return response.text
    except Exception as e:
        print(f"  - Gemini analysis failed for '{sheet_name}': {e}")
        return f"An error occurred during Gemini AI analysis: {e}"

def process_sheet(file_path, sheet_name):
    """
    Processes a single sheet from the Excel file, handling complex headers
    and preserving all data.
    """
    try:
        df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

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

def process_single_sheet(file_path, sheet_name, output_dir):
    """
    Converts a single Excel sheet into a structured and analyzed JSON file.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Processing sheet: {sheet_name}")
    sheet_data = process_sheet(file_path, sheet_name)

    # Get Gemini analysis
    analysis = get_gemini_analysis(sheet_name, sheet_data)
    sheet_data["gemini_analysis"] = analysis

    # Sanitize sheet name for use as a filename
    safe_sheet_name = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '_')).rstrip()
    output_path = os.path.join(output_dir, f"{safe_sheet_name}.json")

    # Save the structured data to a JSON file
    with open(output_path, "w") as json_file:
        json.dump(sheet_data, json_file, indent=4, cls=DateTimeEncoder)

    print(f"  -> Saved to '{output_path}'")

# Configuration
EXCEL_FILE = "Provider Services per Location (A&A + RISE) (1).xlsx"
JSON_OUTPUT_DIR = "processed_sheets"

# Run the conversion for a single sheet
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python advanced_convert.py <sheet_name>")
        sys.exit(1)

    sheet_to_process = sys.argv[1]
    process_single_sheet(EXCEL_FILE, sheet_to_process, JSON_OUTPUT_DIR)