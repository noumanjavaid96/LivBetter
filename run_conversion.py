import pandas as pd
import subprocess
import os

# --- Configuration ---
EXCEL_FILE = "Provider Services per Location (A&A + RISE) (1).xlsx"
CONVERSION_SCRIPT = "advanced_convert.py"

def get_sheet_names(file_path):
    """
    Returns a list of all sheet names in an Excel file.
    """
    try:
        xls = pd.ExcelFile(file_path)
        return xls.sheet_names
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return []
    except Exception as e:
        print(f"An error occurred while reading the Excel file: {e}")
        return []

def run_conversion_for_all_sheets(excel_file, conversion_script):
    """
    Iterates through all sheets and runs the conversion script for each one.
    """
    sheet_names = get_sheet_names(excel_file)
    if not sheet_names:
        print("No sheets found to process.")
        return

    print(f"Found {len(sheet_names)} sheets to process. Starting conversion...\n")

    for sheet_name in sheet_names:
        print(f"--- Running conversion for sheet: '{sheet_name}' ---")
        try:
            # Construct the command to run the conversion script for a single sheet
            command = ["python", conversion_script, sheet_name]

            # Run the command as a subprocess
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                print(stdout)
                print(f"--- Successfully processed sheet: '{sheet_name}' ---\n")
            else:
                print(f"Error processing sheet: '{sheet_name}'")
                print("STDOUT:")
                print(stdout)
                print("STDERR:")
                print(stderr)
                print(f"--- Failed to process sheet: '{sheet_name}' ---\n")

        except Exception as e:
            print(f"An unexpected error occurred while processing sheet '{sheet_name}': {e}")
            print(f"--- Failed to process sheet: '{sheet_name}' ---\n")

if __name__ == "__main__":
    # Ensure the API key is available to the subprocesses
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set. Please set it before running.")
    else:
        run_conversion_for_all_sheets(EXCEL_FILE, CONVERSION_SCRIPT)