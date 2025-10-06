import pandas as pd
import re
import json
from datetime import datetime

# --- Configuration ---
EXCEL_FILE = "Provider Services per Location (A&A + RISE) (1).xlsx"
CSV_OUTPUT_FILE = "notion_database.csv"

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

def clean_text(text):
    """
    Cleans up text by removing extra whitespace and special characters.
    """
    if isinstance(text, str):
        return re.sub(r'\s+', ' ', text).strip()
    return text

def process_clinic_sheet(df):
    """
    Processes a sheet with a standard clinic format.
    """
    records = []
    # This is a heuristic and may need adjustment
    # The first table is usually the main provider info
    provider_info = df.iloc[1].to_dict()
    clinic_name = provider_info.get('col_0')

    # Extract services from the second table-like structure
    # This is also a heuristic
    services_df_index = df[df['col_0'].str.contains('Office/Contact Info', na=False)].index
    if not services_df_index.empty:
        services_df_start = services_df_index[0]
        services_df = df.iloc[services_df_start+1:]
        for _, row in services_df.iterrows():
            record = {
                'Clinic': clinic_name,
                'Provider': provider_info.get('col_1'),
                'Category': 'Service',
                'Item': row.get('col_2'),
                'Details': row.get('col_4'),
                'Additional Info': f"Provider Hours: {provider_info.get('col_2')}, Provider Days: {provider_info.get('col_3')}"
            }
            records.append(record)
    else: # Fallback for sheets that don't have the second table
        records.append({
            'Clinic': clinic_name,
            'Provider': provider_info.get('col_1'),
            'Category': 'General Info',
            'Item': 'Provider Details',
            'Details': json.dumps({k: v for k, v in provider_info.items() if pd.notna(v)}, cls=DateTimeEncoder),
            'Additional Info': ''
        })

    return records


def main():
    """
    Main function to orchestrate the conversion to a single CSV.
    """
    all_records = []
    xls = pd.ExcelFile(EXCEL_FILE)

    for sheet_name in xls.sheet_names:
        print(f"Processing sheet: {sheet_name}")
        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        df.columns = [f"col_{i}" for i in range(len(df.columns))]

        # Simple heuristic to decide how to process the sheet
        if 'services' in sheet_name.lower() or 'schedule' in sheet_name.lower():
            # Handle summary sheets
            for _, row in df.iterrows():
                row_dict = row.to_dict()
                all_records.append({
                    'Clinic': row_dict.get('col_0'),
                    'Provider': row_dict.get('col_1'),
                    'Category': 'Scheduling/Service Summary',
                    'Item': sheet_name,
                    'Details': json.dumps({k: v for k, v in row_dict.items() if pd.notna(v) and k not in ['col_0', 'col_1']}, cls=DateTimeEncoder),
                    'Additional Info': ''
                })
        elif 'previous' in sheet_name.lower():
             for _, row in df.iterrows():
                row_dict = row.to_dict()
                all_records.append({
                    'Clinic': row_dict.get('col_0'),
                    'Provider': row_dict.get('col_1'),
                    'Category': 'Previous Office Info',
                    'Item': 'Closure Details',
                    'Details': json.dumps({k: v for k, v in row_dict.items() if pd.notna(v) and k not in ['col_0', 'col_1']}, cls=DateTimeEncoder),
                    'Additional Info': 'This office is closed.'
                })
        else: # Assumes a standard clinic sheet format
            provider_rows = df[df['col_1'].str.contains('Dr.|H.I.S.|Au.D.|HIS', na=False)]

            for idx, provider_row in provider_rows.iterrows():
                provider_dict = provider_row.to_dict()

                # Try to find the clinic name in the same row, or the row above if the current cell is empty
                clinic_name = df.iloc[idx]['col_0'] if pd.notna(df.iloc[idx]['col_0']) else (df.iloc[idx-1]['col_0'] if idx > 0 and pd.notna(df.iloc[idx-1]['col_0']) else sheet_name)

                record = {
                    'Clinic': clinic_name,
                    'Provider': provider_dict.get('col_1'),
                    'Category': 'Provider Services',
                    'Item': 'Service Matrix',
                    'Details': json.dumps({k: v for k, v in provider_dict.items() if pd.notna(v) and k not in ['col_0', 'col_1']}, cls=DateTimeEncoder),
                    'Additional Info': f"Hours: {provider_dict.get('col_2')}, Days: {provider_dict.get('col_3')}"
                }
                all_records.append(record)

    # Convert to DataFrame and save as CSV
    if all_records:
        final_df = pd.DataFrame(all_records)
        # Clean all text fields
        for col in final_df.columns:
            if final_df[col].dtype == 'object':
                final_df[col] = final_df[col].apply(clean_text)
        final_df.to_csv(CSV_OUTPUT_FILE, index=False)
        print(f"\nSuccessfully created Notion-ready CSV: {CSV_OUTPUT_FILE}")
    else:
        print("No records were extracted. The CSV file was not created.")

if __name__ == "__main__":
    main()