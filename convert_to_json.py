import pandas as pd
import json
import numpy as np

def convert_csv_to_json(csv_path, json_path):
    """
    Reads a CSV file, converts it to a JSON format, and saves it to a file.
    It replaces NaN values with null for JSON compatibility.
    """
    try:
        # Read the CSV file
        df = pd.read_csv(csv_path)

        # Replace NaN values with None, which will be converted to null in JSON
        df = df.replace({pd.NA: None, pd.NaT: None, np.nan: None})

        # Convert the DataFrame to a list of dictionaries
        records = df.to_dict(orient='records')

        # Write the JSON file
        with open(json_path, 'w') as f:
            json.dump(records, f, indent=4)

        print(f"Successfully converted {csv_path} to {json_path}.")

    except FileNotFoundError:
        print(f"Error: The file at {csv_path} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    convert_csv_to_json('notion_database.csv', 'notion_database.json')