import csv
import os
import json
import pandas as pd
from datetime import datetime

def find_csv_files():
    """List all CSV files in the current directory."""
    return [f for f in os.listdir('.') if f.endswith('.csv')]

def load_csv(file_name):
    """Load CSV file and return a DataFrame, treating the first row as data."""
    return pd.read_csv(file_name, header=None)

def preview_data(df):
    """Print a small sample of the DataFrame, reinterpreting first row as header for preview purposes."""
    if df.shape[0] > 1:  # Check if there's more than one row
        print(df.iloc[1:].head())
    else:
        print(df.head())

def get_profiles():
    """Load or initialize trimming profiles."""
    profiles_file = 'trim_profiles.json'
    if os.path.exists(profiles_file):
        with open(profiles_file, 'r') as file:
            profiles = json.load(file)
    else:
        profiles = {}
    return profiles

def save_profiles(profiles):
    """Save the trimming profiles to a file."""
    with open('trim_profiles.json', 'w') as file:
        json.dump(profiles, file, indent=4)

def apply_profile(df, profile):
    """Apply a trimming profile to the DataFrame."""
    if profile.get("remove_blank_rows"):
        df = df.dropna(how='all')  # Remove rows where all elements are NaN
    if profile.get("trim_prefixes"):
        conditions = [df.iloc[:, 0].fillna('UNLIKELY_PREFIX').str.startswith(prefix) for prefix in profile["trim_prefixes"]]
        df = df[~pd.concat(conditions, axis=1).any(axis=1)]
    if profile.get("delete_column"):
        try:
            col_index = int(profile["delete_column"]) - 1
            if col_index < len(df.columns):
                df = df.drop(df.columns[col_index], axis=1)
        except ValueError:
            if profile["delete_column"] in df.columns:
                df = df.drop(columns=[profile["delete_column"]])
    if profile.get("format_datetime"):
        df.iloc[:, profile["format_datetime"]] = pd.to_datetime(df.iloc[:, profile["format_datetime"]]).dt.strftime('%Y-%m-%d %H:%M:%S')
    return df

def create_profile():
    """Create a new trimming profile based on user input."""
    new_profile = {}
    if input("Remove all blank rows? (y/n): ") == 'y':
        new_profile["remove_blank_rows"] = True
    trim_choices = input("Enter prefixes to trim rows starting with in the first column, separated by commas (leave blank if not needed): ")
    if trim_choices:
        new_profile["trim_prefixes"] = [prefix.strip() for prefix in trim_choices.split(',')]
    col = input("Enter column name or index to delete or leave blank if not needed: ")
    if col:
        new_profile["delete_column"] = col
    datetime_col = input("Enter datetime column index to format or leave blank: ")
    if datetime_col:
        new_profile["format_datetime"] = int(datetime_col) - 1  # convert to zero-based index
    use_first_row_as_header = input("Set first row as header in saved file? (y/n): ")
    new_profile["use_first_row_as_header"] = use_first_row_as_header.lower() == 'y'
    return new_profile

def main():
    csv_files = find_csv_files()
    if not csv_files:
        print("No CSV files found in the directory.")
        return

    print("Available CSV files:")
    for index, file in enumerate(csv_files, 1):
        print(f"{index}. {file}")
    file_choice = int(input("Select a CSV file to trim (number): ")) - 1
    file_name = csv_files[file_choice]

    df = load_csv(file_name)
    print("Original Data (first row treated as data):")
    preview_data(df)

    profiles = get_profiles()
    if not profiles:
        print("No profiles found, creating a new one.")
        profiles['Profile1'] = create_profile()
        save_profiles(profiles)

    print("Select a trimming profile:")
    for i, key in enumerate(profiles.keys(), 1):
        print(f"{i}. {key}")
    print(f"{len(profiles) + 1}. Create a new trimming profile")

    choice = int(input("Enter your choice: "))
    if choice == len(profiles) + 1:
        profile_name = f"Profile{len(profiles) + 1}"
        profiles[profile_name] = create_profile()
        save_profiles(profiles)
    else:
        profile_name = list(profiles.keys())[choice - 1]

    df_trimmed = apply_profile(df, profiles[profile_name])
    print(f"Data after applying {profile_name}:")
    preview_data(df_trimmed)

    if input("Save changes to new CSV file? (y/n): ") == 'y':
        if profiles[profile_name].get("use_first_row_as_header"):
            header = df_trimmed.iloc[0]
            df_trimmed = df_trimmed[1:]
            df_trimmed.to_csv('trimmed_' + file_name, index=False, header=header)
        else:
            df_trimmed.to_csv('trimmed_' + file_name, index=False, header=False)
        print("Changes saved.")

if __name__ == "__main__":
    main()