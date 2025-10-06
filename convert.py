import pandas as pd

# Read the Excel file
try:
    df = pd.read_excel("Provider Services per Location (A&A + RISE) (1).xlsx", engine='openpyxl')

    # Convert the DataFrame to a JSON string
    # Using orient='records' to get a list of objects, which is a common JSON format.
    json_data = df.to_json(orient='records', indent=4)

    # Save the JSON data to a file
    with open("data.json", "w") as json_file:
        json_file.write(json_data)

    print("Successfully converted Excel to JSON.")

except FileNotFoundError:
    print("Error: The Excel file was not found.")
except Exception as e:
    print(f"An error occurred: {e}")