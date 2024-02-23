import os
import re
import pip
import argparse

try:
    import pandas as pd
except ImportError:
    pip.main(["install", "pandas"])
    import pandas as pd


def extract_well_id(filename):

    # Split the filename using underscore as a delimiter (this naming convention should not change from the Gen5 output)
    parts = filename.split('_')
    
    # Well ID is identified as a len >= 2 string where the first character is a number and subsequent characters are digits
    for part in parts:
        if len(part) >= 2 and part[0].isalpha() and part[1:].isdigit():
            return part
    
    # If well_id is not found, return None to be processed as an error
    return None

def extract_sequence_id(filepath, delimiter):
    # Split the file path using underscore as the delimiter
    parts = filepath.split(delimiter)
    # Define a regular expression pattern to match three consecutive digits
    pattern = re.compile(r'^\d{3}$')
    # Iterate over the parts to find a match
    for part in parts:
        if pattern.match(part):
            return part
    # Return None if no match is found
    return None

def first_integer(string):
    integer_list = []
    for i in range (0, len(string)):
        if string[i].isnumeric():
            integer_list.append(string[i])
            if not string[i+1].isnumeric():
                break
            else:
                continue
    if len(integer_list) > 0:
        number = ''.join(integer_list)
        number = int(number)
        return number
    else:
        print(f"ERROR first_integer: Cannot sort because no numbers were found in \"{os.path.basename(string)}\"")

def extract_well_id(filename):

    # Split the filename using underscore as a delimiter (this naming convention should not change from the Gen5 output)
    parts = filename.split('_')
    
    # Well ID is identified as a len >= 2 string where the first character is a number and subsequent characters are digits
    for part in parts:
        if len(part) >= 2 and part[0].isalpha() and part[1:].isdigit():
            return part
    
    # If well_id is not found, return None to be processed as an error
    return None

def extract_sequence_id(filepath, delimiter):
    # Split the file path using underscore as the delimiter
    parts = filepath.split(delimiter)
    # Define a regular expression pattern to match three consecutive digits
    pattern = re.compile(r'^\d{3}$')
    # Iterate over the parts to find a match
    for part in parts:
        if pattern.match(part):
            return part
    # Return None if no match is found
    return None

def find_csv_files(directory):
    tif_files = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.csv'):
                tif_files.append(os.path.join(root, filename))
    return tif_files

def sortby_columns(csv_file_list, ascending_descending):
    sortby_columns_descending_list = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12', 'A13', 'A14', 'A15', 'A16', 'A17', 'A18', 'A19', 'A20', 'A21', 'A22', 'A23', 'A24', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11', 'B12', 'B13', 'B14', 'B15', 'B16', 'B17', 'B18', 'B19', 'B20', 'B21', 'B22', 'B23', 'B24', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C12', 'C13', 'C14', 'C15', 'C16', 'C17', 'C18', 'C19', 'C20', 'C21', 'C22', 'C23', 'C24', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10', 'D11', 'D12', 'D13', 'D14', 'D15', 'D16', 'D17', 'D18', 'D19', 'D20', 'D21', 'D22', 'D23', 'D24', 'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E10', 'E11', 'E12', 'E13', 'E14', 'E15', 'E16', 'E17', 'E18', 'E19', 'E20', 'E21', 'E22', 'E23', 'E24', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12', 'F13', 'F14', 'F15', 'F16', 'F17', 'F18', 'F19', 'F20', 'F21', 'F22', 'F23', 'F24', 'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10', 'G11', 'G12', 'G13', 'G14', 'G15', 'G16', 'G17', 'G18', 'G19', 'G20', 'G21', 'G22', 'G23', 'G24', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'H10', 'H11', 'H12', 'H13', 'H14', 'H15', 'H16', 'H17', 'H18', 'H19', 'H20', 'H21', 'H22', 'H23', 'H24', 'I1', 'I2', 'I3', 'I4', 'I5', 'I6', 'I7', 'I8', 'I9', 'I10', 'I11', 'I12', 'I13', 'I14', 'I15', 'I16', 'I17', 'I18', 'I19', 'I20', 'I21', 'I22', 'I23', 'I24', 'J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8', 'J9', 'J10', 'J11', 'J12', 'J13', 'J14', 'J15', 'J16', 'J17', 'J18', 'J19', 'J20', 'J21', 'J22', 'J23', 'J24', 'K1', 'K2', 'K3', 'K4', 'K5', 'K6', 'K7', 'K8', 'K9', 'K10', 'K11', 'K12', 'K13', 'K14', 'K15', 'K16', 'K17', 'K18', 'K19', 'K20', 'K21', 'K22', 'K23', 'K24', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8', 'L9', 'L10', 'L11', 'L12', 'L13', 'L14', 'L15', 'L16', 'L17', 'L18', 'L19', 'L20', 'L21', 'L22', 'L23', 'L24', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9', 'M10', 'M11', 'M12', 'M13', 'M14', 'M15', 'M16', 'M17', 'M18', 'M19', 'M20', 'M21', 'M22', 'M23', 'M24', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'N7', 'N8', 'N9', 'N10', 'N11', 'N12', 'N13', 'N14', 'N15', 'N16', 'N17', 'N18', 'N19', 'N20', 'N21', 'N22', 'N23', 'N24', 'O1', 'O2', 'O3', 'O4', 'O5', 'O6', 'O7', 'O8', 'O9', 'O10', 'O11', 'O12', 'O13', 'O14', 'O15', 'O16', 'O17', 'O18', 'O19', 'O20', 'O21', 'O22', 'O23', 'O24', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15', 'P16', 'P17', 'P18', 'P19', 'P20', 'P21', 'P22', 'P23', 'P24']

    sort_dict = {}
    # Assign the values to the dictionary
    for file in csv_file_list:
        basename_wo_ext = os.path.basename(file).split(".")[0]
        file_wellID = extract_well_id(os.path.basename(file))
        sequenceID = extract_sequence_id(basename_wo_ext, "_")
        #print(file_wellID + " " + sequenceID)

        # Initialize the nested dictionary if it doesn't exist
        if file_wellID not in sort_dict:
            sort_dict[file_wellID] = {}
            if int(sequenceID) not in sort_dict[file_wellID]:
                sort_dict[file_wellID][int(sequenceID)] = None

        sort_dict[file_wellID][int(sequenceID)] = file

    # Assign the sort order to generate the list in the corresponding order
    if ascending_descending == "ascending":
        sortby_columns_list = sortby_columns_descending_list.reverse()
    else:
        sortby_columns_list = sortby_columns_descending_list

    sorted_list = []
    for wellID in sortby_columns_list:
        for i in range(0, 21):
            if wellID in sort_dict:
                if i in sort_dict[wellID]:
                    sorted_list.append(sort_dict[wellID][i])
    
    return sorted_list

def sortby_rows(csv_file_list, ascending_descending):
    sortby_rows_descending_list = ['A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'I1', 'J1', 'K1', 'L1', 'M1', 'N1', 'O1', 'P1', 'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2', 'J2', 'K2', 'L2', 'M2', 'N2', 'O2', 'P2', 'A3', 'B3', 'C3', 'D3', 'E3', 'F3', 'G3', 'H3', 'I3', 'J3', 'K3', 'L3', 'M3', 'N3', 'O3', 'P3', 'A4', 'B4', 'C4', 'D4', 'E4', 'F4', 'G4', 'H4', 'I4', 'J4', 'K4', 'L4', 'M4', 'N4', 'O4', 'P4', 'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'G5', 'H5', 'I5', 'J5', 'K5', 'L5', 'M5', 'N5', 'O5', 'P5', 'A6', 'B6', 'C6', 'D6', 'E6', 'F6', 'G6', 'H6', 'I6', 'J6', 'K6', 'L6', 'M6', 'N6', 'O6', 'P6', 'A7', 'B7', 'C7', 'D7', 'E7', 'F7', 'G7', 'H7', 'I7', 'J7', 'K7', 'L7', 'M7', 'N7', 'O7', 'P7', 'A8', 'B8', 'C8', 'D8', 'E8', 'F8', 'G8', 'H8', 'I8', 'J8', 'K8', 'L8', 'M8', 'N8', 'O8', 'P8', 'A9', 'B9', 'C9', 'D9', 'E9', 'F9', 'G9', 'H9', 'I9', 'J9', 'K9', 'L9', 'M9', 'N9', 'O9', 'P9', 'A10', 'B10', 'C10', 'D10', 'E10', 'F10', 'G10', 'H10', 'I10', 'J10', 'K10', 'L10', 'M10', 'N10', 'O10', 'P10', 'A11', 'B11', 'C11', 'D11', 'E11', 'F11', 'G11', 'H11', 'I11', 'J11', 'K11', 'L11', 'M11', 'N11', 'O11', 'P11', 'A12', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12', 'H12', 'I12', 'J12', 'K12', 'L12', 'M12', 'N12', 'O12', 'P12', 'A13', 'B13', 'C13', 'D13', 'E13', 'F13', 'G13', 'H13', 'I13', 'J13', 'K13', 'L13', 'M13', 'N13', 'O13', 'P13', 'A14', 'B14', 'C14', 'D14', 'E14', 'F14', 'G14', 'H14', 'I14', 'J14', 'K14', 'L14', 'M14', 'N14', 'O14', 'P14', 'A15', 'B15', 'C15', 'D15', 'E15', 'F15', 'G15', 'H15', 'I15', 'J15', 'K15', 'L15', 'M15', 'N15', 'O15', 'P15', 'A16', 'B16', 'C16', 'D16', 'E16', 'F16', 'G16', 'H16', 'I16', 'J16', 'K16', 'L16', 'M16', 'N16', 'O16', 'P16', 'A17', 'B17', 'C17', 'D17', 'E17', 'F17', 'G17', 'H17', 'I17', 'J17', 'K17', 'L17', 'M17', 'N17', 'O17', 'P17', 'A18', 'B18', 'C18', 'D18', 'E18', 'F18', 'G18', 'H18', 'I18', 'J18', 'K18', 'L18', 'M18', 'N18', 'O18', 'P18', 'A19', 'B19', 'C19', 'D19', 'E19', 'F19', 'G19', 'H19', 'I19', 'J19', 'K19', 'L19', 'M19', 'N19', 'O19', 'P19', 'A20', 'B20', 'C20', 'D20', 'E20', 'F20', 'G20', 'H20', 'I20', 'J20', 'K20', 'L20', 'M20', 'N20', 'O20', 'P20', 'A21', 'B21', 'C21', 'D21', 'E21', 'F21', 'G21', 'H21', 'I21', 'J21', 'K21', 'L21', 'M21', 'N21', 'O21', 'P21', 'A22', 'B22', 'C22', 'D22', 'E22', 'F22', 'G22', 'H22', 'I22', 'J22', 'K22', 'L22', 'M22', 'N22', 'O22', 'P22', 'A23', 'B23', 'C23', 'D23', 'E23', 'F23', 'G23', 'H23', 'I23', 'J23', 'K23', 'L23', 'M23', 'N23', 'O23', 'P23', 'A24', 'B24', 'C24', 'D24', 'E24', 'F24', 'G24', 'H24', 'I24', 'J24', 'K24', 'L24', 'M24', 'N24', 'O24', 'P24']

    sort_dict = {}
    # Assign the values to the dictionary
    for file in csv_file_list:
        basename_wo_ext = os.path.basename(file).split(".")[0]
        file_wellID = extract_well_id(os.path.basename(file))
        sequenceID = extract_sequence_id(basename_wo_ext, "_")
        if sequenceID is None:
            print(f"ERROR sortby_rows: Could not find sequence ID from {file}")
        #print(file_wellID + " " + sequenceID)

        # Initialize the nested dictionary if it doesn't exist
        if file_wellID not in sort_dict:
            sort_dict[file_wellID] = {}
            if int(sequenceID) not in sort_dict[file_wellID]:
                sort_dict[file_wellID][int(sequenceID)] = None

        sort_dict[file_wellID][int(sequenceID)] = file

    # Assign the sort order to generate the list in the corresponding order
    if ascending_descending == "ascending":
        sortby_columns_list = sortby_rows_descending_list.reverse()
    else:
        sortby_columns_list = sortby_rows_descending_list

    sorted_list = []
    for wellID in sortby_columns_list:
        for i in range(0, 21):
            if wellID in sort_dict:
                if i in sort_dict[wellID]:
                    sorted_list.append(sort_dict[wellID][i])
    
    return sorted_list

def merge_columns_vertically(csv_file_list, output_csv):
    try:
        for input_csv in csv_file_list:
            if not os.path.isfile(output_csv):
                df_to_add = pd.read_csv(input_csv, low_memory=False)
                df_to_add[" "] = f"{input_csv} >"
                df_out = df_to_add
                df_out.to_csv(output_csv, mode='a', header=True, index=False)
            else:
                df_to_add = pd.read_csv(input_csv, low_memory=False)
                df_to_add[" "] = f"{input_csv} >"
                df_out = pd.read_csv(output_csv, low_memory=False)
                
                # Ensure columns match and reorder if necessary
                df_to_add = df_to_add[df_out.columns]
                
                df_out = pd.concat([df_out, df_to_add], axis=0, ignore_index=True)
                df_out.to_csv(output_csv, index=False)
        return "ok"
    
    except Exception as e:
        print(f"ERROR merge_columns_vertically: {str(e)}")

def merge_columns_vertically_sumValues(csv_file_list, output_csv):
    try:
        for input_csv in csv_file_list:
            #print(f"processing {os.path.basename(input_csv)}...")

            # Read the input CSV file
            df_to_add = pd.read_csv(input_csv, low_memory=False)

            # Sum the values of the second column
            area_sum = df_to_add.iloc[:, 1].sum()

            # Create a new DataFrame with 'Source' and 'Area' columns
            processed_data = pd.DataFrame({'Source': [os.path.basename(input_csv)], 
                                        'Area': [area_sum]})

            if not os.path.isfile(output_csv):
                # If output CSV doesn't exist, create it with the new data and headers
                processed_data.to_csv(output_csv, header=True, index=False)
            else:
                # If output CSV exists, append the new data
                with open(output_csv, 'a') as f:
                    processed_data.to_csv(f, header=False, index=False)

            #print("finished.")
        remove_empty_rows_and_rewrite(output_csv)
        return "ok"
    
    except Exception as e:
        print(f"ERROR merge_columns_vertically_sumValues: {str(e)}")

def merge_columns_horizontally(csv_file_list, output_csv):
    try:
        for input_csv in csv_file_list:
            if not os.path.isfile(output_csv):
                df_to_add = pd.read_csv(input_csv, low_memory=False)
                df_to_add[" "] = ""
                df_to_add.insert(1, "", f"{input_csv} >")
                df_out = df_to_add
                # Save the merged data to the output CSV file
                df_out.to_csv(output_csv, index=False)

            else:
                # Read the input CSV file into a DataFrame
                df_to_add = pd.read_csv(input_csv, low_memory=False)
                df_dest = pd.read_csv(output_csv, low_memory=False)
                df_dest[" "] = ""
                df_dest[""] = f"{input_csv} >"

                df_out = pd.concat([df_dest, df_to_add], axis=1)

                # Save the merged data to the output CSV file
                df_out.to_csv(output_csv, index=False)

        return "ok"
    
    except Exception as e:
        print(f"ERROR merge_columns_horizontally: {str(e)}")

def merge_columns_horizontally_sumValues(csv_file_list, output_csv):
    try:
        for input_csv in csv_file_list:
            #print(f"Processing {os.path.basename(input_csv)}...")

            # Read the input CSV file
            df_to_add = pd.read_csv(input_csv, low_memory=False)

            # Sum the values of the second column
            area_sum = df_to_add.iloc[:, 1].sum()

            # Create a new DataFrame for the new columns
            new_columns = pd.DataFrame({
                f"Source_{os.path.basename(input_csv)}": [os.path.basename(input_csv)],
                f"Area_{os.path.basename(input_csv)}": [area_sum]
            })

            if not os.path.isfile(output_csv):
                # If output CSV doesn't exist, create it with the new columns
                new_columns.to_csv(output_csv, header=True, index=False)
            else:
                # If output CSV exists, read it and add the new columns
                df_output = pd.read_csv(output_csv)
                df_output = pd.concat([df_output, new_columns], axis=1)
                df_output.to_csv(output_csv, index=False)

            #print("Finished.")
        remove_empty_rows_and_rewrite(output_csv)

        return "ok"
    
    except Exception as e:
        print(f"ERROR merge_columns_horizontally_sumValues: {str(e)}")

def remove_empty_rows_and_rewrite(csv_filepath):
    try:
        # Load the CSV file into a DataFrame
        df = pd.read_csv(csv_filepath)

        # Remove rows where all elements are NaN
        df_cleaned = df.dropna(how='all')

        # Rewrite the CSV file with the cleaned DataFrame
        df_cleaned.to_csv(csv_filepath, index=False)

        print(f"File '{csv_filepath}' has been cleaned and rewritten.")
    
    except Exception as e:
        print(f"ERROR remove_empty_rows_and_rewrite: {e}")

# ___________________________________________________________________________________________________________RETRIEVE SETTINGS
#*************************************************************************************************************
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script that merges all available data from input CSV files into a single CSV for data manipulation."
    )
    parser.add_argument('--CSVlist', required=True, type=str, help="Comma separated filepaths(should not start/end with a comma)")
    parser.add_argument("--outputPath", required=True, type=str, help="Output .csv filepath")
    parser.add_argument("--mergeMode", required=True, type=str, help="How the final merged output data is grouped together. 0 - Horizontal, creates new column per data point. 1- Vertical, creates new row per data point")
    parser.add_argument("--sortBy", required=False, type=str, help="\'columns\' - A1, A2, A3 ... P22, P23, P24. \'rows\' - A1, B1, C1 ... N24, O24, P24. Default to rows.")
    parser.add_argument("--orderSetting", required=False, type=str, help="\'descending\' - A1 > P24 \'ascending\' - P24 > A1. Default to descending.")
    parser.add_argument("--sumValues", required=False, type=str, help="\'true\' to sum the \'Area\' values from each tif analyzed in the output CSV, otherwise \'false\'. Defaults to true.")
    args = parser.parse_args()

    print("*****************CSV_Merger.py STARTING*****************")
    print(f"Received command: ")
    print(f"CSV list: {args.CSVlist}")
    print(f"Output filepath: {args.outputPath}")
    print(f"Merge mode: {args.mergeMode}")
    print(f"Sort by: {args.sortBy}")
    print(f"Order: {args.orderSetting}")
    print(f"Sum values: {str(args.sumValues)}")


    # Get the merge settings
    csv_file_string = args.CSVlist
    output_file_path = args.outputPath
    merge_mode = args.mergeMode
    sortby_setting = args.sortBy
    order_setting = args.orderSetting
    sum_setting = args.sumValues

    # Set defaults
    if sortby_setting is None:
        sortby_setting = "rows"

    if order_setting is None:
        order_setting = "descending"

    if sum_setting is None:
        sum_setting = "true"


    # ___________________________________________________________________________________________________________PROCESS INPUTS
    #*************************************************************************************************************
    # Grab the CSV list string and convert it back into a list of filepaths
    csv_file_fp = csv_file_string.replace("\"", "")
    if not os.path.isfile(csv_file_string):
        print("ERROR CSV_Merger: does not exist: " + csv_file_fp)
        exit()
    
    csv_file_list = []
    # Open the file and read line by line
    with open(csv_file_fp, 'r') as file:
        for line in file:
            # Remove whitespace
            line = line.strip()
            # Validate the file
            if os.path.exists(line):
                csv_file_list.append(line)
            else:
                print("ERROR CSV_Merger: does not exist: " + line)


    # Grab the output filepath string and replace the quotation marks
    output_file_path.replace("\"", "")
    if os.path.isfile(output_file_path):
        print(f"{output_file_path} already exists. This script will not perform an overwrite. Change the output path or delete/move this file before trying again.")
        exit()

    # csv_file_string - filepath
    # output_file_path - filepath
    # merge_mode - 0 (horizontal) or 1 (vertical)
    # sum_setting - True or False

    # ___________________________________________________________________________________________________________SORT CSV LIST
    #*************************************************************************************************************

    # Defaults to columns
    if sortby_setting == "rows":
        csv_file_list = sortby_rows(csv_file_list, order_setting)
    if sortby_setting == "columns":
        csv_file_list = sortby_columns(csv_file_list, order_setting)


    if merge_mode == "0":
        if sum_setting == "true":
            output_message = merge_columns_horizontally_sumValues(csv_file_list, output_file_path)
        if sum_setting == "false":
            output_message = merge_columns_horizontally(csv_file_list, output_file_path)

    elif merge_mode == "1":
        if sum_setting == "true":
            output_message = merge_columns_vertically_sumValues(csv_file_list, output_file_path)
        if sum_setting == "false":
            output_message = merge_columns_vertically(csv_file_list, output_file_path)

    if output_message != "ok":
        print("ERROR: Something went wrong with the merge. Merge function failed.")


    #**********************START OLD CODE**********************
    # sort_list = []
    # for file in csv_file_list:
    #     number = first_integer(os.path.basename(file))
    #     sort_list.append((file, number))
    # # Sort the list by the second element (number) in each tuple
    # sorted_list = sorted(sort_list, key=lambda x: x[1])
    # # Extract the first element (string) from each tuple to get a sorted list of strings
    # sorted_files = [file[0] for file in sorted_list]

    # output_basename = os.path.basename(output_file_path)


    # for file in sorted_files:
    #     print(f"Starting to merge {file}...")
    #     if merge_mode == "0":
    #         merge_columns_horizontally(file, output_file_path)
    #     elif merge_mode == "1":
    #         merge_columns_vertically(file, output_file_path)
    #     print(f"Successfully merged {os.path.basename(file)} into {output_basename}")
    #**********************END OLD CODE**********************

    print("All CSVs merged Successfully!")

    print("\n____________________CSVs Merged:____________________")
    for file in csv_file_list:
        print(file)
    print("\n____________________Merged Output:____________________")
    print(output_file_path)
    print("*****************CSV_Merger.py FINISHED*****************\n\n")
