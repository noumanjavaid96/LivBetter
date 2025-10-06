import pandas as pd
import json
import os
import sys
import google.generativeai as genai
from datetime import datetime

# --- Configuration ---
EXCEL_FILE = "Provider Services per Location (A&A + RISE) (1).xlsx"
JSON_OUTPUT_DIR = "processed_sheets"

# --- Gemini AI Configuration ---
try:
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise KeyError("GEMINI_API_KEY environment variable not set.")
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-flash-latest')
except KeyError as e:
    print(f"Error: {e}", file=sys.stderr)
    model = None
except Exception as e:
    print(f"An error occurred during Gemini AI configuration: {e}", file=sys.stderr)
    model = None

class DateTimeEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle datetime objects and other non-serializable types.
    """
    def default(self, obj):
        if isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        if pd.isna(obj):
            return None
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
        error_message = f"An error occurred during Gemini AI analysis: {e}"
        print(f"  - Gemini analysis failed for '{sheet_name}': {error_message}")
        return error_message

def get_sheet_names(file_path):
    """
    Returns a list of all sheet names in an Excel file.
    """
    try:
        xls = pd.ExcelFile(file_path)
        return xls.sheet_names
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.", file=sys.stderr)
        return []
    except Exception as e:
        print(f"An error occurred while reading the Excel file: {e}", file=sys.stderr)
        return []

def process_sheet_data(file_path, sheet_name):
    """
    Processes a single sheet from the Excel file, cleans the data,
    and returns it as a structured dictionary.
    """
    try:
        df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        df_raw.dropna(axis=1, how='all', inplace=True)

        header_row_index = -1
        for i, row in df_raw.iterrows():
            # A more robust check for a header row
            if row.notna().sum() > max(2, df_raw.shape[1] / 2) and not row.iloc[0] == row.iloc[1]:
                header_row_index = i
                break

        if header_row_index == -1:
            return {"sheet_name": sheet_name, "data_type": "non_tabular", "content": df_raw.to_dict(orient='records')}

        pre_header_df = df_raw.iloc[:header_row_index].dropna(axis=1, how='all').dropna(axis=0, how='all')

        df_data = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row_index)
        df_data.dropna(axis=1, how='all', inplace=True)
        df_data.columns = [str(col) if 'Unnamed' not in str(col) else f"col_{i}" for i, col in enumerate(df_data.columns)]

        post_header_df = df_raw.iloc[header_row_index + len(df_data) + 1:].dropna(axis=1, how='all').dropna(axis=0, how='all')

        return {
            "sheet_name": sheet_name,
            "pre_header_info": pre_header_df.to_dict(orient='records'),
            "table_data": df_data.to_dict(orient='records'),
            "post_header_info": post_header_df.to_dict(orient='records')
        }

    except Exception as e:
        print(f"An error occurred while processing sheet '{sheet_name}': {e}", file=sys.stderr)
        return {"sheet_name": sheet_name, "error": str(e)}

def main():
    """
    Main function to orchestrate the conversion process.
    """
    if not os.path.exists(JSON_OUTPUT_DIR):
        os.makedirs(JSON_OUTPUT_DIR)

    sheet_names = get_sheet_names(EXCEL_FILE)
    if not sheet_names:
        print("No sheets found to process. Exiting.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(sheet_names)} sheets to process. Starting conversion...\n")

    for sheet_name in sheet_names:
        print(f"--- Processing sheet: '{sheet_name}' ---")
        sheet_data = process_sheet_data(EXCEL_FILE, sheet_name)

        if "error" in sheet_data:
            print(f"Skipping analysis and saving due to processing error.")
            continue

        # Get Gemini analysis
        analysis = get_gemini_analysis(sheet_name, sheet_data)
        sheet_data["gemini_analysis"] = analysis

        # Sanitize sheet name for use as a filename
        safe_sheet_name = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '_')).rstrip()
        output_path = os.path.join(JSON_OUTPUT_DIR, f"{safe_sheet_name}.json")

        # Save the structured data to a JSON file
        try:
            with open(output_path, "w") as json_file:
                json.dump(sheet_data, json_file, indent=4, cls=DateTimeEncoder)
            print(f"  -> Successfully saved to '{output_path}'\n")
        except Exception as e:
            print(f"  -> Failed to save JSON for sheet '{sheet_name}': {e}\n", file=sys.stderr)

    print("--- All sheets processed. ---")

if __name__ == "__main__":
    main()