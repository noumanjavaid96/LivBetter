import pandas as pd
import numpy as np

def format_office_hours(csv_path):
    """
    Reads a CSV file, combines office hours columns into a 'Combined Office Hours'
    column, and saves the updated CSV.

    The logic is as follows:
    1. If 'General Office Hours' has a value, it is used for 'Combined Office Hours'.
    2. If 'General Office Hours' is empty or null, 'Provider Days' and 'Provider Hours'
       are combined to create the value.
    3. The script overwrites the original CSV with the updated data.
    """
    try:
        # Read the CSV file. `keep_default_na=False` ensures that empty strings
        # are read as empty strings, not NaN.
        df = pd.read_csv(csv_path, keep_default_na=False)

        # Ensure the target column exists, otherwise add it. This will also handle
        # rerunning the script on an already processed file.
        if 'Combined Office Hours' not in df.columns:
            df['Combined Office Hours'] = ''

        for index, row in df.iterrows():
            general_hours = str(row.get('General Office Hours', '')).strip()
            provider_days = str(row.get('Provider Days', '')).strip()
            provider_hours = str(row.get('Provider Hours', '')).strip()

            combined_value = ""

            if general_hours:
                combined_value = general_hours
            elif provider_days and provider_hours:
                # Combine days and hours with a colon
                combined_value = f"{provider_days}: {provider_hours}"
            elif provider_days:
                combined_value = provider_days
            elif provider_hours:
                combined_value = provider_hours

            df.at[index, 'Combined Office Hours'] = combined_value

        df.to_csv(csv_path, index=False)
        print(f"Successfully updated {csv_path} with 'Combined Office Hours'.")

    except FileNotFoundError:
        print(f"Error: The file at {csv_path} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    format_office_hours('notion_database.csv')