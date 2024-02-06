import os
import sys
import datetime
import subprocess
from ij.io import OpenDialog
from ij.gui import GenericDialog


class formattedtime:
    def get_time_str(self):
        current_datetime = datetime.datetime.now()
        date_str = current_datetime.strftime("%d%b%Y_%H%M").upper()
        return date_str

def confirmation_dialog(mergemode_setting, sortby_setting, order_setting, sum_setting, directory, output_directory):

    confirm_dialog = GenericDialog("Confirm settings")
    confirm_dialog.addMessage("Confirm your merge settings:")
    confirm_dialog.addMessage("Merge mode:                 " + mergemode_setting)
    confirm_dialog.addMessage("Sort by:                            " + sortby_setting)
    confirm_dialog.addMessage("Sort order:                      " + order_setting)

    if sum_setting:
        sum_setting = "Yes"
    else:
        sum_setting = "No"
    confirm_dialog.addMessage("Sum values?                 " + sum_setting)

    confirm_dialog.addMessage("Input CSV directory:      " + directory)
    csv_file_list = list_csv_files(directory)
    confirm_dialog.addMessage(str(len(csv_file_list)) + " CSVs to merge from input directory")

    confirm_dialog.addMessage("Output directory:            " + output_directory)

    confirm_dialog.addMessage("\n\nIf the settings above are correct, click OK to continue.\nTo revise these settings, click Cancel.")
    confirm_dialog.showDialog()

    if confirm_dialog.wasCanceled():
        return("cancelled")
    elif confirm_dialog.wasOKed():
        return("ok")

def get_csv_merge_settings():
    directory = ""
    output_directory = ""
    while True:
        gd = GenericDialog("CSV merge settings")

        gd.addCheckboxGroup(0,1,[], [], ["Merge mode"])
        #gd.addMessage("Merge mode:\n\tVertical - Data will be merged by adding rows.\n\tHorizontal - Data will be merged by adding columns (left to right).")
        gd.addMessage("Vertical - Data will be merged by adding rows (Best for Spotfire).\nHorizontal - Data will be merged by adding columns (left to right).")
        mergemode_choices = ["Vertical", "Horizontal"]
        gd.addChoice("", mergemode_choices, mergemode_choices[0])

        gd.addCheckboxGroup(0,1,[], [], ["Sort by"])
        #gd.addMessage("Sort by:\n\tRows - A1, B1, C1 ... N24, O24, P24.\n\tColumns - A1, A2, A3 ... P22, P23, P24.")
        gd.addMessage("Rows - A1, B1, C1 ... N24, O24, P24.\nColumns - A1, A2, A3 ... P22, P23, P24.")
        sortby_choices = ["Rows", "Columns"]
        gd.addChoice("", sortby_choices, sortby_choices[0])

        gd.addCheckboxGroup(0,1,[], [], ["Sort order"])
        #gd.addMessage("Order:\n\tDescending - A1 > P24.\n\tAscending - P24 > A1")
        gd.addMessage("Descending - A1 > P24.\nAscending - P24 > A1")
        order_choices = ["Descending", "Ascending"]
        gd.addChoice("", order_choices, order_choices[0])

        gd.addCheckboxGroup(0,1,[], [], ["Data format"])
        gd.addMessage("Checking \'Sum values\' will summarize the \'Area\' for the individual\nparticles from each input CSV and omit the other fields for the output.\nLeaving it unchecked will add the data as-is from the source.")
        gd.addCheckbox("Sum values", True)
        gd.addMessage("\n\n")

        gd.addCheckboxGroup(0,1,[], [], ["Input directory"])
        gd.addMessage("This is where the input .csv files are sourced from.")
        gd.addDirectoryField("", directory, 50)

        gd.addCheckboxGroup(0,1,[], [], ["Output directory"])
        gd.addMessage("This is where the output file will be generated.")
        gd.addDirectoryField("", output_directory, 50)

        gd.addMessage("\n\nClick OK to begin merge, or cancel to exit program.")
        gd.showDialog()

        # Retrieve the values
        mergemode_setting = gd.getNextChoice()
        sortby_setting = gd.getNextChoice()
        order_setting = gd.getNextChoice()
        sum_setting = gd.getNextBoolean()
        directory = gd.getNextString()
        output_directory = gd.getNextString()

        if gd.wasCanceled():
            print("get_csv_merge_settings was cancelled, exiting program...")
            exit()

        if directory is None or directory == "":
            warning_dialog("Please choose an input directory before continuing.")
            continue

        if output_directory is None or output_directory == "":
            warning_dialog("Please choose an output directory before continuing.")
            continue
        
        confirmation = confirmation_dialog(mergemode_setting, sortby_setting, order_setting, sum_setting, directory, output_directory)

        if confirmation == "ok":
            return mergemode_setting, sortby_setting, order_setting, sum_setting, directory, output_directory
        
def get_csv_merger_py_path():
    try:
        # Use __file__ if it is defined
        script_path = os.path.abspath(__file__)
    except NameError:
        # If __file__ is not defined (e.g., in interactive mode), use sys.argv[0]
        script_path = os.path.abspath(sys.argv[0])

    script_dir = os.path.dirname(script_path)
    script_file_list = list_files(script_dir)

    if "CSV_Merger.py" not in script_file_list:
        # Prompt user to find the merge script
        open_dialog = OpenDialog("Select filepath for CSV_Merger.py")
        if open_dialog.getPath() is not None:
            csv_merger_script_fp = open_dialog.getPath()
        else:
            exit()
    else:
        for file in script_file_list:
            if "CSV_Merger.py"  in file:
                csv_merger_script_fp = os.path.join(script_dir, file)
                break

    return csv_merger_script_fp

def list_files(directory):
    try:
        # Get the list of files in the directory
        files = os.listdir(directory)
        
        # Filter out directories, keeping only files
        files = [file for file in files if os.path.isfile(os.path.join(directory, file))]
        
        return files
    except Exception as e:
        print("ERROR list_files: " + e)
        exit()

def list_csv_files(directory):
    csv_files = []

    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.csv'):
                csv_files.append(os.path.join(root, filename))

    return csv_files

def warning_dialog(message):
    warning_dialog = GenericDialog("Warning")
    warning_dialog.addMessage(message)
    warning_dialog.showDialog()

def generate_csv_filelist_txt(directory):
    csv_merger_script_fp = get_csv_merger_py_path()
    filelist_txt_fp = os.path.join(os.path.dirname(csv_merger_script_fp), "Files_to_merge.txt")
    # Delete the old one if it exists:
    if os.path.isfile(filelist_txt_fp):
        os.remove(filelist_txt_fp)
    # Create the file and populate
    for file_path in list_csv_files(directory):
        with open(filelist_txt_fp, "a") as write_file:
            write_file.write(file_path + "\n")

    return filelist_txt_fp

def convert_to_command(mergemode_setting, sortby_setting, order_setting, sum_setting, directory, output_dir):
    # Find CSV_Merger.py filepath to invoke it
    csv_merger_script_fp = get_csv_merger_py_path()
    invokation_command = "python " + csv_merger_script_fp + " "

    # Input files
    # Create txt filelist from directory
    filelist_txt_fp = generate_csv_filelist_txt(directory=directory)
    directory_command = "--CSVlist " + filelist_txt_fp + " "

    # Output filepath
    timestr = formattedtime()
    current_datetime = timestr.get_time_str()
    filename = "Merged_output_on_" + current_datetime + ".csv"
    output_command = "--outputPath " + os.path.join(output_dir, filename) + " "

    # Sortby 
    if sortby_setting == "Rows":
        sortby_command = "--sortBy rows "
    elif sortby_setting == "Columns":
        sortby_command = "--sortBy columns "

    # Mergemode
    if mergemode_setting == "Horizontal":
        mergemode_command = "--mergeMode 0 "
    elif mergemode_setting == "Vertical":
        mergemode_command = "--mergeMode 1 "

    # Sort order
    if order_setting == "Descending":
        order_command = "--orderSetting descending "
    elif order_setting == "Ascending":
        order_command = "--orderSetting ascending "

    # Summing values
    if sum_setting:
        sum_command = "--sumValues true"
    else:
        sum_command = "--sumValues false"
        
    # parser.add_argument('--CSVlist', required=True, type=str, help="Comma separated filepaths(should not start/end with a comma)")
    # parser.add_argument("--outputPath", required=True, type=str, help="Output .csv filepath")
    # parser.add_argument("--mergeMode", required=True, type=str, help="How the final merged output data is grouped together. 0 - Horizontal, creates new column per data point. 1- Vertical, creates new row per data point")
    # parser.add_argument("--sortBy", required=True, type=str, help="\'columns\' - A1, A2, A3 ... P22, P23, P24. \'rows\' - A1, B1, C1 ... N24, O24, P24")
    # parser.add_argument("--orderSetting", required=False, type=str, help="\'descending\' - A1 > P24 \'ascending\' - P24 > A1")
    # parser.add_argument("--sumValues", required=False, type=str, help="\'true\' to sum the \'Area\' values from each tif analyzed in the output CSV, otherwise \'false\'")

    # reorder this shit bruh
    command = invokation_command + directory_command + output_command + mergemode_command + sortby_command + order_command + sum_command
    return command, filelist_txt_fp

mergemode_setting, sortby_setting, order_setting, sum_setting, directory, output_dir = get_csv_merge_settings()

print("mergemode_setting: " + mergemode_setting)
print("sortby_setting: " + sortby_setting)
print("order_setting: " + order_setting)
print("sum_setting: " + str(sum_setting))
print("directory: " + directory)
print("output_dir: " + output_dir)
print()

command, filelist_txt_fp = convert_to_command(mergemode_setting, sortby_setting, order_setting, sum_setting, directory, output_dir)
print(command)
output_message = subprocess.check_output(command, shell=True)
print("INVOKED CSV_Merger.py")
output_message = output_message.decode('utf-8')
print(output_message)

try:
    os.remove(filelist_txt_fp)
    print("Removed " + filelist_txt_fp)
except Exception as e:
    print(str(e))

