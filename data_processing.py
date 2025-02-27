import os
import subprocess
import pandas as pd
from pandarallel import pandarallel

# Initialize pandarallel for parallel processing
pandarallel.initialize()

def process_txt_files(input_folder="input", output_folder="output"):
    """
    Concatenates TXT files, cleans the raw data, and saves a cleaned CSV.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    combined_file = os.path.join(output_folder, "combined.txt")
    
    # Concatenate all TXT files into one file
    if os.name == 'nt':  # Windows
        subprocess.run(f'type {input_folder}\\*.txt > {combined_file}', shell=True)
    else:  # Unix-like systems
        subprocess.run(f'cat {input_folder}/*.txt > {combined_file}', shell=True)
    
    # Define column specifications and names based on documentation.
    colspecs = [
        (0, 2),     # Recordart
        (2, 4),     # Transaktionsart
        (4, 6),     # Kanton
        (6, 16),    # Code Tarif
        (16, 24),   # Datum gültig ab
        (24, 33),   # Steuerbares Einkommen ab Fr.
        (33, 42),   # Tarifschritt in Fr.
        (42, 43),   # Code Geschlecht
        (43, 45),   # Anzahl Kinder
        (45, 54),   # Mindeststeuer in Fr.
        (54, 59),   # Steuer %-Satz
        (59, 62)    # Code Status
    ]
    column_names = [
        'recordart', 'transaktionsart', 'kanton', 'code_tarif',
        'datum_gueltig_ab', 'steuerbares_einkommen', 'tarifschritt',
        'code_geschlecht', 'anzahl_kinder', 'mindeststeuer',
        'steuer_prozent', 'code_status'
    ]
    
    # Read the fixed-width file.
    df = pd.read_fwf(
        combined_file,
        colspecs=colspecs,
        names=column_names,
        skiprows=1,    # Skip header of the first file
        skipfooter=1,  # Skip footer of the last file
        engine='python'
    )
    
    # Clean whitespace in string columns.
    for col in df.select_dtypes(include=['object']):
        df[col] = df[col].str.strip()
    
    # Split 'code_tarif' into individual components.
    df['code_tarif_one'] = df['code_tarif'].str[0]
    df['code_tarif_two'] = df['code_tarif'].str[1]
    df['kirchensteuer'] = df['code_tarif'].str[2]
    
    # Determine if the second character is numeric.
    numeric_values = pd.to_numeric(df['code_tarif_two'], errors='coerce')
    df['is_integer'] = numeric_values.notna()
    
    # Create a combined 'tarif_code' based on conversion success.
    df['tarif_code'] = df.parallel_apply(
        lambda row: row['code_tarif_one'] + row['code_tarif_two']
                    if not row['is_integer'] else row['code_tarif_one'],
        axis=1
    )
    
    # Convert monetary values to decimals (assuming 2 decimal places).
    df['steuerbares_einkommen'] = df['steuerbares_einkommen'].astype(float) / 100
    df['mindeststeuer'] = df['mindeststeuer'].astype(float) / 100
    df['steuer_prozent'] = df['steuer_prozent'].astype(float) / 100
    
    # Remove the temporary combined file.
    os.remove(combined_file)
    
    # Save the cleaned DataFrame to CSV.
    cleaned_file = os.path.join(output_folder, "tar25_cleaned.csv")
    df.to_csv(cleaned_file, index=False)
    print(f"Data has been cleaned and saved to '{cleaned_file}'")
    return df

def load_data(recreate_data=False):
    """
    Loads cleaned data from CSV or processes raw TXT files if needed.
    """
    cleaned_file = 'output/tar25_cleaned.csv'
    if recreate_data or not os.path.exists(cleaned_file):
        print("Processing TXT files...")
        df = process_txt_files()
    else:
        print("Reading from existing CSV file...")
        df = pd.read_csv(cleaned_file)
    return df

def transform_data(df):
    """
    Applies any additional transformations to the DataFrame.
    """
    # (Optional) Convert date fields or apply further transformations if needed.
    return df

def filter_data(df):
    """
    Filters the data to include only records with:
      - Taxable income below 30,000 CHF.
    Also saves the filtered data to CSV.
    """
    # Create a copy to avoid SettingWithCopyWarning
    df_filtered = df[df['steuerbares_einkommen'] <= 30_000].copy()
    
    # Ensure 'kanton' column contains only strings
    df_filtered['kanton'] = df_filtered['kanton'].astype(str)
    
    # Fill NaN values in anzahl_kinder with 0 before converting to integer
    df_filtered['anzahl_kinder'] = df_filtered['anzahl_kinder'].fillna(0).astype(int)
    
    output_filtered = 'output/tar25_cleaned_filtered.csv'
    df_filtered.to_csv(output_filtered, index=False)
    print(f"Filtered data saved to '{output_filtered}'")
    return df_filtered
