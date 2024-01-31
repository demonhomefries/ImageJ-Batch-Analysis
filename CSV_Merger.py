import os
import pip
import argparse

try:
    import pandas as pd
except ImportError:
    pip.main(["install", "pandas"])
    import pandas as pd

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

def merge_columns_horizontally(input_csv, output_csv):

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

def merge_columns_vertically(input_csv, output_csv):
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script that concatenates all available data from input CSV files."
    )
    parser.add_argument('--CSVlist', required=True, type=str, help="Comma separated filepaths(should not start/end with a comma)")
    parser.add_argument("--outputPath", required=True, type=str, help="Output .csv filepath")
    parser.add_argument("--mergeMode", required=True, type=str, help="How the final merged output columns are grouped together. Horizontal append - 0, Vertical append - 1")
    args = parser.parse_args()

    print("*****************CSV_Merger.py STARTING*****************")
    # Grab the CSV list string and convert it back into a list of filepaths
    csv_file_string = args.CSVlist
    csv_file_fp = csv_file_string.replace("\"", "")
    if not os.path.isfile(csv_file_string):
        print("ERROR CSV_Merger: does not exist: " + csv_file_fp)
    
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
    output_file_path = args.outputPath
    output_file_path.replace("\"", "")

    # Get the merge mode 
    merge_mode = args.mergeMode
    

    print(f"csv_file_string: {csv_file_string}")
    print(f"csv_file_list: {csv_file_list}")
    print(f"output_file_path: {output_file_path}")

    #print(csv_file_list)
    #for file in csv_file_list:
        #print(file)
    #print(output_file_path)

    sort_list = []
    for file in csv_file_list:
        #print(f"DEBUG line 72: {file}")
        number = first_integer(os.path.basename(file))
        sort_list.append((file, number))
    # Sort the list by the second element (number) in each tuple
    sorted_list = sorted(sort_list, key=lambda x: x[1])
    # Extract the first element (string) from each tuple to get a sorted list of strings
    sorted_files = [file[0] for file in sorted_list]

    output_basename = os.path.basename(output_file_path)

    for file in sorted_files:
        print(f"Starting to merge {file}...")
        if merge_mode == "0":
            merge_columns_horizontally(file, output_file_path)
        elif merge_mode == "1":
            merge_columns_vertically(file, output_file_path)
        print(f"Successfully merged {os.path.basename(file)} into {output_basename}")

    print("All CSVs merged Successfully!")

    print("\n____________________CSVs Merged:____________________")
    for file in csv_file_list:
        print(file)
    print("\n____________________Merged Output:____________________")
    print(output_file_path)
    print("*****************CSV_Merger.py FINISHED*****************\n\n")
