import os
import sys
import time
import Queue
import shutil
import datetime
import threading
import subprocess
from ij import IJ
from ij.io import OpenDialog
from java.lang import Runtime
from ij.gui import GenericDialog
from java.awt.event import ActionListener

# ___________________________________________________________________________________________________________SUPPLEMENTARY FUNCTIONS AND CLASSES
#*************************************************************************************************************

class customError(Exception):
    pass

class RunLog:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Get current date and time
        current_datetime = datetime.datetime.now()
        #date_str = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
        date_str = current_datetime.strftime("%d%b%Y_%H%M").upper()
        # File name
        file_name = "ImageJ_Analysis_RUNLOG_on_" + date_str + ".txt"
        self.run_log_fp = os.path.join(script_dir, file_name)

    def append(self, log_string, printout=False):
        # Append log string to the file
        with open(self.run_log_fp, 'a') as file:
            file.write(log_string + '\n')
        if printout is True:
            print(log_string)

class formattedtime:
    def get_time_str(self):
        current_datetime = datetime.datetime.now()
        date_str = current_datetime.strftime("%d%b%Y_%H%M").upper()
        return date_str
    
def add_path_backslash(directory):
    # This function just adds a backslash because apparently os.path.join doesn't add strings as new folders, just concatenates them into the basename/basedir.
    if not directory.endswith("\\"):
        directory = directory + "\\"
    return directory

def check_if_stack(imp, tif_file):

        # More direct method to check if the image is a stack
    if imp.getStackSize() > 1:
        #print("check_if_stack: IS A STACK: " + os.path.basename(tif_file))
        return True
    else:
        #print("check_if_stack: NOT A STACK: " + os.path.basename(tif_file))
        return False
    
    # Get the filepath to save the metadata information
    info_file_path = os.path.join(os.getcwd(), "Info for Image")
    info_file_path = info_file_path + ".txt"

    # Run the show info macro and save the information to a .txt file
    IJ.run(imp, "Show Info...", "")
    basename_w_ext = os.path.basename(tif_file)
    IJ.selectWindow("Info for " + basename_w_ext)
    IJ.saveAs("Text", info_file_path)

    # Close the info window
    IJ.selectWindow("Info for " + basename_w_ext)
    IJ.run("Close")

    # Open the info txt and check that "voxel" is contained in it
    try:
        with open(info_file_path, 'r') as file:
            for line in file:
                if 'voxel' in line.lower():
                    print("check_if_stack: IS A STACK: " + basename_w_ext)
                    return True
                
        print("check_if_stack: NOT A STACK: " + basename_w_ext)
        return False

    except Exception as e:
        print("ERROR check_if_stack: info_file_path is " + str(info_file_path) + "\n\n" + str(e))
        exit()

def extract_well_id(filename):

    # Split the filename using underscore as a delimiter (this naming convention should not change from the Gen5 output)
    parts = filename.split('_')
    
    # Well ID is identified as a len >= 2 string where the first character is a number and subsequent characters are digits
    for part in parts:
        if len(part) >= 2 and part[0].isalpha() and part[1:].isdigit():
            return part
    
    # If well_id is not found, return None to be processed as an error
    return None

def find_csv_files(directory):
    csv_files = []

    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.csv'):
                csv_files.append(os.path.join(root, filename))

    return csv_files

def find_tif_files(directory):
    tif_files = []

    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.tif'):
                tif_files.append(os.path.join(root, filename))

    return tif_files

def find_tif_files_with_string(directory, string):
    tif_files = []

    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.tif'):
                tif_files.append(os.path.join(root, filename))

    tif_files = [tif_file for tif_file in tif_files if string in tif_file]
    return tif_files

def get_wellID_list(type):
    """
    type: "384-well" or "96-well"
    
    """

    output_list = []

    if type == "96-well":
        for letter in "ABCDEFGH":
            for number in range(1, 13):
                output_list.append(letter + str(number))
    elif type == "384-well":
        for letter in "ABCDEFGHIJKLMNOP":
            for number in range(1, 25):
                output_list.append(letter + str(number))
    else:
        print("ERROR get_wellID_list: type not equal to 384 or 96. type is " + type)
        return None

    return output_list

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

def move_copy_file_to(move_copy_mode, source_fp, dest_fp):

    if move_copy_mode.lower() == "move":
        shutil.move(src=source_fp, dst=dest_fp)
        if not os.path.isfile(dest_fp):
            raise customError("ERROR move_copy_file_to: Did not move " +  source_fp + " file to " + dest_fp)
        print("Moved " + source_fp + " to " + dest_fp)
        
    elif move_copy_mode.lower() == "copy":
        shutil.copy2(src=source_fp, dst=dest_fp)
        if not os.path.isfile(dest_fp):
            raise customError("ERROR move_copy_file_to: Did not copy " +  source_fp + " file to " + dest_fp)
        print("Copied " + source_fp + " to " + dest_fp)
    return dest_fp

def send_to_error_folder(move_copy, tif_file, tif_filename_w_ext, reason, error_folder):
    if not os.path.isdir(error_folder):
        os.mkdir(error_folder)
        if not os.path.isdir(error_folder):
            raise customError("\nERROR organize_files: Could not generate error_folder: " + error_folder)
        else:
            dest = os.path.join(error_folder, tif_filename_w_ext)
            print("\nERROR " + reason + ".   Moving " + tif_file + " to " + dest)
            move_copy_file_to(move_copy_mode=move_copy, source_fp=tif_file, dest_fp=dest)
            return dest


# ___________________________________________________________________________________________________________USER INTERFACE FUNCTIONS
#*************************************************************************************************************
def get_particle_analysis_settings(size_min, size_max, include_holes_checked, merge_mode):
    # Set parameter for pixel^2 size.
    # Get these into the same dialog box
    # size_min = IJ.getString("pixel^2 size minimum: ", "30")
    # size_max = IJ.getString("pixel^2 size maximum: ", "Infinity")

    # Get the minimum and maximum particle analysis parameters
    gd = GenericDialog("Enter particle min/max sizes")
    gd.addStringField("Pixel^2 size minimum", size_min)
    gd.addStringField("Pixel^2 size maximum:", size_max)
    gd.addCheckbox("Include holes", include_holes_checked)
    merge_options = ["Don't merge", "Horizontal merge", "Vertical merge (Spotfire)"]
    gd.addChoice("Merge mode", merge_options, merge_mode)
    gd.addMessage("Click OK to save settings, or Cancel to restore to defaults and exit.")
    gd.showDialog()
    include_holes_checked = gd.getNextBoolean()
    merge_mode = gd.getNextChoice()
    size_min = gd.getNextString()
    size_max = gd.getNextString()

    # print("\nChosen Settings: \nsize_min: " + size_min 
    #       + " \nsize_max: " + size_max 
    #       + "\ninclude_holes: " + str(include_holes_checked) 
    #       + "\nMerge Mode: " + merge_mode)

    if gd.wasCanceled():
        print("get_particle_analysis_settings was cancelled, restoring default values ")
        return "30", "Infinity", False, "Vertical merge (Spotfire)"

    return size_min, size_max, include_holes_checked, merge_mode

class AnalysisSettingsListener(ActionListener):
    def __init__(self):
        size_min = "30"
        size_max = "Infinity"
        include_holes_checked = False
        merge_mode = "Vertical merge (Spotfire)"
        self.analysis_settings = size_min, size_max, include_holes_checked, merge_mode
    def actionPerformed(self, event):
        size_min, size_max, include_holes_checked, merge_mode = self.analysis_settings
        self.analysis_settings = get_particle_analysis_settings(size_min, size_max, include_holes_checked, merge_mode)

def get_thresholding_settings(setting, threshold_mode, dark_bg, stack_hist, rst_range, save_thresholded_images):
    setting = None
    # Initialize the dialog
    gd = GenericDialog("Threshold Settings")

    thresh_mode = ["Default", "Huang", "Intermodes", "IsoData", "IJ_IsoData", "Li", "MaxEntropy", "Mean", "MinError", "Minimum", "Moments", "Otsu", "Percentile", "RenyiEntropy", "Shanbhag", "Triangle", "Yen"]
    gd.addChoice("Threshold Mode", thresh_mode, threshold_mode)

    # clr_mode = ["Red", "B&W", "Over/Under"]
    # gd.addChoice("Color Mode", clr_mode, clr_mode[0])
    gd.addCheckbox("Dark Background", dark_bg)
    gd.addCheckbox("Stack Histogram", stack_hist)
    gd.addCheckbox("Don't reset range", rst_range)
    gd.addCheckbox("Save thresholded images?", save_thresholded_images)
    gd.addMessage("Click OK to save settings, or Cancel to restore to defaults and exit.")
    gd.showDialog()


    # Retrieve the values
    threshold_mode = gd.getNextChoice()
    dark_bg = gd.getNextBoolean()
    stack_hist = gd.getNextBoolean()
    rst_range = gd.getNextBoolean()
    save_thresholded_images = gd.getNextBoolean()

    # Create the setting to pass into the function
    setting = threshold_mode
    if dark_bg:
        setting = setting + " dark"
    if rst_range:
        setting = setting + " no-reset"
    if stack_hist:
        setting = setting + " stack"

    # For debugging and logging
    # print("Thresholding Settings:\n\tThresholding Mode: " + threshold_mode 
    # + "\n\tDark Background: " + str(dark_bg) 
    # + "\n\tStack Histogram: " + str(stack_hist) 
    # + "\n\tDon't reset range: " + str(rst_range)
    # + "\n\tSave thresholded image: " + str(save_thresholded_images))

    if gd.wasCanceled():
        print("get_thresholding_settings was cancelled, restoring default values")
        return None, "Default", False, False, False, False
    else:
        return setting, threshold_mode, dark_bg, stack_hist, rst_range, save_thresholded_images
                                            
class ThresholdingSettingsListener(ActionListener):
    def __init__(self):
        setting = None
        threshold_mode = "Default"
        dark_bg = False
        stack_hist = False
        rst_range = False
        save_thresholded_images = False
        self.thresholding_settings = setting, threshold_mode, dark_bg, stack_hist, rst_range, save_thresholded_images

    def actionPerformed(self, event):
        setting, threshold_mode, dark_bg, stack_hist, rst_range, save_thresholded_images = self.thresholding_settings
        self.thresholding_settings = get_thresholding_settings(setting, threshold_mode, dark_bg, stack_hist, rst_range, save_thresholded_images)

def get_organization_settings(organize_mode, move_copy, string1, string2, generate_log):

    # Initialize the dialog
    gd = GenericDialog("Organize images?")

    gd.addMessage("Choose how images will be organized into folders before\nthe particle analysis script is run.")

    organize_choices = ["Don't Organize", "96-well", "384-well"]
    gd.addChoice("Organization", organize_choices, organize_mode)

    move_copy_choices = ["Move", "Copy"]
    gd.addChoice("Move or Copy?", move_copy_choices, move_copy)

    gd.addMessage("Input unique strings to differentiate groups of images.\nEach image containing the following string will be\nplaced into its respective folder.\n(Case Sensitive)")
    gd.addStringField("String 1", string1)
    gd.addStringField("String 2", string2)
    gd.addCheckbox("Generate organization & error log", generate_log)
    gd.addMessage("Click OK to save settings, or Cancel to restore to defaults and exit.")
    gd.showDialog()

    # Retrieve the values
    organize_mode = gd.getNextChoice()
    move_copy = gd.getNextChoice()
    string1 = gd.getNextString()
    string2 = gd.getNextString()
    generate_log = gd.getNextBoolean()
    # print("Organization Settings:\n\tOrganize Mode: " + str(organize_mode)
    #        + "\n\tMove/Copy: " + str(move_copy)
    #          + "\n\tString 1: " + str(string1) 
    #          + "\n\tString 2: " + str(string2)
    #          + "\n\tGenerate Log: " + str(generate_log))
    
    if gd.wasCanceled():
        print("get_organization_settings was cancelled, restoring default values")
        return "384-well", "Copy", "Confocal", "BrightField", False
    else:
        return organize_mode, move_copy, string1, string2, generate_log
    
class OrganizationSettingsListener(ActionListener):
    def __init__(self):
        organize_mode = "384-well"
        move_copy = "Copy"
        string1 = "Confocal"
        string2 = "BrightField"
        generate_log = False
        self.organization_settings = organize_mode, move_copy, string1, string2, generate_log

    def actionPerformed(self, event):
        organize_mode, move_copy, string1, string2, generate_log = self.organization_settings
        self.organization_settings = get_organization_settings(organize_mode, move_copy, string1, string2, generate_log)

def get_settings_strings(step_list, organization_settings, thresholding_settings, analysis_settings, directory, output_csv_dir, print_settings):

    # print("get_settings_strings DEBUGGING step_list: " + str(step_list))
    # print("get_settings_strings DEBUGGING organization_settings: " + str(organization_settings))
    # print("get_settings_strings DEBUGGING analysis_settings: " + str(analysis_settings))
    # print("get_settings_strings DEBUGGING thresholding_settings: " + str(thresholding_settings))
    # print("get_settings_strings DEBUGGING directory: " + str(directory))
    # print("get_settings_strings DEBUGGING print_settings: " + str(print_settings))

    if step_list is not None:
        [tif_organization_yn1, threshold_yn2, analyze_particles_yn3] = step_list
        step_list_string = ("User Selected Workflow:"
            + "\n       Organize tif files?: " + str(tif_organization_yn1) 
            + "\n       Auto-threshold?: " + str(threshold_yn2)
            + "\n       Analyze Particles?: " + str(analyze_particles_yn3))

    if tif_organization_yn1:
        organize_mode, move_copy, string1, string2, generate_log = organization_settings
        organization_settings_string = ("Organization Settings:"
                        + "\n       Organize Mode: " + str(organize_mode)
                        + "\n       Move/Copy: " + str(move_copy)
                        + "\n       String 1: " + str(string1) 
                        + "\n       String 2: " + str(string2)
                        + "\n       Generate Log: " + str(generate_log))
    else:
        organization_settings_string = ("Organization Settings: None")

    if threshold_yn2:
        setting, threshold_mode, dark_bg, stack_hist, rst_range, save_thresholded_images = thresholding_settings
        thresholding_settings_string = ("Auto-threshold Settings:" 
                        + "\n       Thresholding Mode: " + threshold_mode 
                        + "\n       Dark Background: " + str(dark_bg) 
                        + "\n       Stack Histogram: " + str(stack_hist) 
                        + "\n       Don't reset range: " + str(rst_range)
                        + "\n       Save thresholded image: " + str(save_thresholded_images)
                        + "\n       Command: " + str(setting))
    else:
        thresholding_settings_string = ("Auto-threshold Settings: None")

    if analyze_particles_yn3:
        size_min, size_max, include_holes_checked, merge_mode = analysis_settings
        analysis_settings_string = ("Analyze Particles Settings:"
                        + "\n       Minimum Size: " + size_min 
                        + "\n       Maximum Size: " + str(size_max) 
                        + "\n       Include Holes?: " + str(include_holes_checked) 
                        + "\n       Merge Mode: " + str(merge_mode))
    else:
        analysis_settings_string = ("Analyze Particles Settings: None")

    if directory:
        directory_string = ("Directory: " + str(directory))
    elif directory is None or directory == "":
        directory_string = ("Directory: None")
    
    if output_csv_dir:
        output_csv_dir_string = ("Merged Output CSV Directory: " + str(output_csv_dir))
    elif output_csv_dir is None or output_csv_dir == "":
        output_csv_dir_string = ("Merged Output CSV Directory: None")

    if print_settings:
        print(step_list_string + "\n"
            + organization_settings_string + "\n"
            + thresholding_settings_string + "\n"
            + analysis_settings_string + "\n"
            + directory_string + "\n"
            + output_csv_dir_string)

    return step_list_string, organization_settings_string, thresholding_settings_string, analysis_settings_string, directory_string, output_csv_dir_string

def confirmation_dialog(step_list, organization_settings, thresholding_settings, analysis_settings, directory, output_csv_dir):

    step_list_string, organization_settings_string, thresholding_settings_string, analysis_settings_string, directory_string, output_csv_dir_string = get_settings_strings(step_list, organization_settings, thresholding_settings, analysis_settings, directory, output_csv_dir, print_settings=True)

    confirm_dialog = GenericDialog("Confirm settings")
    confirm_dialog.addMessage(step_list_string)
    confirm_dialog.addMessage(organization_settings_string)
    confirm_dialog.addMessage(thresholding_settings_string)
    confirm_dialog.addMessage(analysis_settings_string)
    confirm_dialog.addMessage(directory_string)
    confirm_dialog.addMessage(output_csv_dir_string)
    confirm_dialog.addMessage("\n\nIf the settings above are correct, click OK to continue.\nTo revise these settings, click Cancel.")
    confirm_dialog.showDialog()

    if confirm_dialog.wasCanceled():
        return("cancelled")
    elif confirm_dialog.wasOKed():
        return("ok")

def warning_dialog(message):
    # Set up a dialog box and 
    warning_dialog = GenericDialog("Warning")
    warning_dialog.addMessage(message)
    warning_dialog.showDialog()

def get_analysis_workflow():
    # Instantiate the listeners
    orgListener = OrganizationSettingsListener()
    threshListener = ThresholdingSettingsListener()
    analysisListener = AnalysisSettingsListener()

    # Set initial values for values retrieved directly from workflow dialog
    script_dir = os.path.dirname(os.path.abspath(__file__))
    directory = script_dir
    output_csv_dir = script_dir

    tif_organization_yn1 = False
    threshold_yn2 = False
    analyze_particles_yn3 = False
    while True:
        gd = GenericDialog("Set up analysis workflow")
        # Organization settings setup
        gd.addCheckboxGroup(0,1,[], [], ["1. ORGANIZE"])
        gd.addMessage("""Organize your tif files into folders for each well ID in 96w or 384w formats before\nrunning an analysis. Saved thresholded files or analysis CSVs will be saved into the\norganized folder. The resulting folder will be in the same directory as the input folder\nwith an \'_auto-organized\' suffix.""")
        gd.addCheckbox("Organize tif files", tif_organization_yn1)
        gd.addButton("Organization Settings", orgListener)
        #gd.addMessage("")
        # Thresholding settings setup
        gd.addCheckboxGroup(0,1,[], [], ["2. THRESHOLD"])
        gd.addMessage("""Use auto-thresholding to threshold images before running Analyze Particles. This step\ncan be skipped if the images have already been thresholded. Thresholded images can\nalso be saved to the source folder for later use and will have an \'_auto-thresholded\' suffix.""")
        gd.addCheckbox("Auto-threshold", threshold_yn2)
        gd.addButton("Auto-thresholding Settings", threshListener)
        #gd.addMessage("")
        # Analyze Particles and Merge CSVs settings setup
        gd.addCheckboxGroup(0,1,[], [], ["3. ANALYZE"])
        gd.addMessage("""Analyze particles will run through each thresholded tif file in your source directory\nand identify the particles based on the input size parameters.The data will be saved\nto individual files before they can be merged horizontally or vertically.""")
        gd.addCheckbox("Analyze particles & generate CSVs", analyze_particles_yn3)
        gd.addButton("Analysis and Merge Settings", analysisListener)
        gd.addMessage("")
        # Directory Input setting setup
        gd.addDirectoryField("Directory: ", directory, 50)
        # Output CSV Input setting setup
        gd.addDirectoryField("Output CSV Directory: ", output_csv_dir, 50)
        gd.showDialog()
        tif_organization_yn1 = gd.getNextBoolean()
        threshold_yn2 = gd.getNextBoolean()
        analyze_particles_yn3 = gd.getNextBoolean()
        directory = gd.getNextString()
        output_csv_dir = gd.getNextString()
        
        # Step list as a list for easier unpacking
        step_list = [tif_organization_yn1, threshold_yn2, analyze_particles_yn3]

        # The following error conditions will show a warning dialog if met:
        if gd.wasCanceled():
            print("get_analysis_workflow: CANCELLED")
            return "cancelled"
        
        if threshold_yn2 is True and analyze_particles_yn3 is False:
            setting, threshold_mode, dark_bg, stack_hist, rst_range, save_thresholded_images = threshListener.thresholding_settings
            if save_thresholded_images is False:
                warning_dialog("You have chosen to Threshold, but not save the thresholded files or analyze particles.\nThis operation will not have an outcome.\nPlease enable 'Save thresholded files?' or 'Analyze Particles'")
                continue

        if directory == "" or directory is None:
            warning_dialog("The directory has not been set. Please select a valid directory.")
            continue

        if (output_csv_dir == "" or output_csv_dir is None) and analyze_particles_yn3 is True:
            warning_dialog("Analyze Particles was checked but output CSV filepath was not specified.")
            continue
        
        # The following error conditions may not be met because settigns will never be None as the listener functions return several variables.
        # But I'm highkey scared that it might happen so I'm leaving it here.
        if tif_organization_yn1 and orgListener.organization_settings is None:
            warning_dialog("Tif organization has been selected but organization settings have not been chosen.")
            continue

        if threshold_yn2 and threshListener.thresholding_settings is None:
            warning_dialog("Auto-thresholding has been selected but thresholding settings have not been chosen.")
            continue
            
        if analyze_particles_yn3 and analysisListener.analysis_settings is None:
            warning_dialog("Analyze particles has been selected but analysis settings have not been chosen.")
            continue

        if tif_organization_yn1 is True and threshold_yn2 is False and analyze_particles_yn3 is True:
            warning_dialog("Workflow cannot go from organization to analyze particles without auto-thresholding")
            continue

        if tif_organization_yn1 is False and threshold_yn2 is False and analyze_particles_yn3 is False:
            warning_dialog("No workflow option checkboxes have been selected. Click 'Cancel' to exit the program.")
            continue

        ## Debugging print statements
        # print("get_analysis_workflow:")
        # print("get_analysis_workflow DEBUGGING step_list: " + str(step_list))
        # print("get_analysis_workflow DEBUGGING organization_settings: " + str(orgListener.organization_settings))
        # print("get_analysis_workflow DEBUGGING analysis_settings: " + str(analysisListener.analysis_settings))
        # print("get_analysis_workflow DEBUGGING thresholding_settings: " + str(threshListener.thresholding_settings))
        # print("get_analysis_workflow DEBUGGING directory: " + str(directory))

        # Show the confirmation dialog with the user-chosen settings
        confirmation = confirmation_dialog(step_list, orgListener.organization_settings, threshListener.thresholding_settings, analysisListener.analysis_settings, directory, output_csv_dir)

        # Exit out of the loop if the confirmation was OKed or go back to the main dialog if it was cancelled
        if confirmation == "ok":
            get_settings_strings(step_list, orgListener.organization_settings, threshListener.thresholding_settings, analysisListener.analysis_settings, directory, output_csv_dir, print_settings=False)
            return step_list, orgListener.organization_settings, threshListener.thresholding_settings, analysisListener.analysis_settings, directory, output_csv_dir




# ___________________________________________________________________________________________________________ORGANIZATION FUNCTIONS
#*************************************************************************************************************
    
def batch_organize_files(directory, organization_settings):

    organize_mode, move_copy, string1, string2, generate_log = organization_settings

    moved_copied_list = [] # (Source, Destination) - only useful to reverse the operation
    error_list = []

    if not os.path.isdir(directory):
        log.append("ERROR batch_organize_files: variable directory is not a directory")
        raise customError("ERROR batch_organize_files: variable directory is not a directory")
    

    # Create the folder for the organized files to live in.
    current_datetime = datetime.datetime.now()
    date_str = current_datetime.strftime("%d%b%Y_%H%M").upper()
    folder_name = os.path.dirname(directory)
    organized_folder_path = os.path.join(directory, folder_name + "_auto-organized_on_" + date_str)

    log.append("Creating directory: " + organized_folder_path)
    os.mkdir(organized_folder_path)

    if not os.path.isdir(organized_folder_path):
        log.append("ERROR batch_organize_files: failed to create directory " + organized_folder_path)
        raise customError("ERROR batch_organize_files: failed to create directory " + organized_folder_path)


    # Create the string1 and string2 subfolders
    organized_folder_path = add_path_backslash(organized_folder_path)
    string1_folder = os.path.join(organized_folder_path + string1)
    string2_folder = os.path.join(organized_folder_path + string2)
    print("string1 folder: " + string1_folder)
    print("string2 folder: " + string2_folder)
    os.mkdir(string1_folder)
    os.mkdir(string2_folder)
    string1_folder = add_path_backslash(string1_folder)
    string2_folder = add_path_backslash(string2_folder)
    log.append("string1 folder: " + string1_folder)
    log.append("string2 folder: " + string2_folder)

    if not os.path.isdir(string1_folder):
        log.append("ERROR batch_organize_files: failed to create string1 directory " + string1_folder)
        raise customError("ERROR batch_organize_files: failed to create string1 directory " + string1_folder)

    if not os.path.isdir(string2_folder):
        log.append("ERROR batch_organize_files: failed to create string1 directory " + string2_folder)
        raise customError("ERROR batch_organize_files: failed to create string2 directory " + string2_folder)

    # Define the error folder's path - should it need to be created for use
    error_folder = os.path.join(organized_folder_path + "Errors")
    error_folder = add_path_backslash(error_folder)
    print("error folder: " + error_folder)

    # Get tif file list from the master folder
    file_list = find_tif_files(directory)

    # Determine the folder structure
    well_id_list = get_wellID_list(organize_mode)
    
    # Create each wellID subfolder
    for well_id in well_id_list:
        # In string1's folder
        well_id_folder_1 = os.path.join(string1_folder, well_id)
        print("Generating well_id_folder_1: " + well_id_folder_1)
        os.mkdir(well_id_folder_1)

        # In string2's folder
        well_id_folder_2 = os.path.join(string2_folder, well_id)
        print("Generating well_id_folder_2: " + well_id_folder_2)
        os.mkdir(well_id_folder_2)

    # Organize each of the tif files
    for tif_file in file_list:

        tif_filename_w_ext = os.path.basename(tif_file)
        print("batch_organize_files Organizing " + tif_file + "...")
        wellid_from_filename = extract_well_id(tif_filename_w_ext)

        # If string1 is found and the well ID matches
        if string1 in tif_filename_w_ext and wellid_from_filename in well_id_list:
            dest = os.path.join(string1_folder, wellid_from_filename, tif_filename_w_ext)
            move_copy_file_to(move_copy_mode=move_copy, source_fp=tif_file, dest_fp=dest)
            print("\n" + move_copy + ": " + tif_file + " to " + dest)
            moved_copied_list.append((tif_file, dest))

        # If string2 is found and the Well ID matches
        elif string2 in tif_filename_w_ext and wellid_from_filename in well_id_list:
            dest = os.path.join(string2_folder, wellid_from_filename, tif_filename_w_ext)
            move_copy_file_to(move_copy_mode=move_copy, source_fp=tif_file, dest_fp=dest)
            print("\n" + move_copy + ": " + tif_file + " to " + dest)
            moved_copied_list.append((tif_file, dest))
        
        # ERROR if the wellID is not found in the filename
        elif extract_well_id(tif_filename_w_ext) == None:
            reason = "Reason: Well ID not in tif filename: " + tif_file
            dest = send_to_error_folder(move_copy, tif_file, tif_filename_w_ext, reason, error_folder)
            log.append("ERROR batch_organize_files: " + reason)
            error_list.append((tif_file, reason))
            moved_copied_list.append((tif_file, dest))
            # raise customError("ERROR batch_organize_files: " + reason)
        
        # ERROR if the wellID is found but does not exist in the well_id_list (possibly chosen 96-well organize_mode instead of 384-well)
        elif wellid_from_filename is not None and wellid_from_filename not in well_id_list:
            log.append("ERROR batch_organize_files: wellid_from_filename is not in well_id_list, wellid_from_filename: " + wellid_from_filename)
            raise customError("ERROR batch_organize_files: wellid_from_filename is not in well_id_list, wellid_from_filename: " + wellid_from_filename)
        

        # ERROR if both strings exists in the source tif filename
        elif string1 in tif_filename_w_ext and string2 in tif_filename_w_ext:
            reason = "Reason: both string1: " + string1 + " nor string2: " + string2 + " in tif filename"
            dest = send_to_error_folder(move_copy, tif_file, tif_filename_w_ext, reason, error_folder)
            log.append("ERROR batch_organize_files: " + reason)
            error_list.append((tif_file, reason))
            moved_copied_list.append((tif_file, dest))
            # warning_dialog("ERROR batch_organize_files: " + reason)

        # ERROR if neither string exists in the source tif filename
        elif string1 not in tif_filename_w_ext and string2 not in tif_filename_w_ext:
            reason = "Reason: neither string1: " + string1 + " nor string2: " + string2 + " in tif filename: " + tif_file
            dest = send_to_error_folder(move_copy, tif_file, tif_filename_w_ext, reason, error_folder)
            log.append("ERROR batch_organize_files: " + reason)
            error_list.append((tif_file, reason))
            moved_copied_list.append((tif_file, dest))
            # warning_dialog("ERROR batch_organize_files: " + reason)

    file_list.remove(tif_file)
    file_list = [destination_fp for source_fp, destination_fp in moved_copied_list]

    if generate_log is True:
        log.append("AUTO ORGANIZATION FILE TRANSACTIONS: ")
        for source_fp, destination_fp in moved_copied_list:
            log.append((move_copy + " from " + source_fp + " to " + destination_fp))
    
    return file_list, organized_folder_path




# ___________________________________________________________________________________________________________AUTO THRESHOLDING FUNCTIONS
#*************************************************************************************************************


# OLD MULTI-THREADED AUTO THRESHOLDING
# def auto_threshold_image(threshold_setting, tif_file):
#     # Open the file
#     #IJ.open(tif_file)
#     #imp = IJ.getImage()
#     imp = IJ.openImage(tif_file)

#     IJ.run(imp, "8-bit", "")
#     IJ.setAutoThreshold(imp, threshold_setting)
#     IJ.run(imp, "Convert to Mask", "")

#     tif_filename_w_ext = os.path.basename(tif_file)
#     tif_filename_wo_ext = os.path.splitext(tif_filename_w_ext)[0]
#     tif_basedir = os.path.dirname(tif_file)
    
#     # Determine and save the file to the output path
#     output_path = os.path.join(tif_basedir, tif_filename_wo_ext  + "_auto-thresholded.tif")
#     IJ.saveAs(imp, "Tiff", output_path)
#     imp.close()
#     #print("Saved thresholded image to " + output_path)
#     return output_path

# def worker():
#     while True:
#         item = q.get()
#         if item is None:
#             # No more items to process
#             break
#         threshold_setting, tif_file = item
#         auto_threshold_image(threshold_setting, tif_file)
#         q.task_done()
#         print("\nThread {} completed processing {}".format(threading.current_thread().name, os.path.basename(tif_file)))

# def batch_auto_threshold(file_list, directory, thresholding_settings):

#     # Get the tif files from the directory if a file_list has not been created from a previous process.
#     if file_list is None or len(file_list) < 1:
#         file_list = find_tif_files(directory)
#         log.append("batch_auto_threshold did not receive a file_list, defaulting to directory: " + directory, printout=True)
#         log.append("Found " + str(len(file_list)) + " files in " + directory, printout=True)

#     log.append("Found " + str(len(file_list)) + " files in file_list", printout=True)

#     # TO RUN THIS PROCESS FASTER, UNCOMMENT OUT THE LINE BELOW AND COMMENT THE max_threads LINE AFTER THAT
#     #max_threads = 12
#     max_threads = Runtime.getRuntime().availableProcessors() // 2
#     setting, threshold_mode, dark_bg, stack_hist, rst_range, save_thresholded_images = thresholding_settings

#     log.append("Starting batch_auto_threshold using " + str(max_threads) + " and thresholding setting: " + setting, printout=True)

#     # Create a queue to hold tasks
#     global q
#     q = Queue.Queue()

#     # Start worker threads
#     threads = []
#     for i in range(max_threads):
#         t = threading.Thread(target=worker)
#         t.start()
#         threads.append(t)

#     # Enqueue tasks
#     for tif_file in file_list:
#         q.put((setting, tif_file))

#     # Block until all tasks are done
#     q.join()

#     # Stop workers
#     for i in range(max_threads):
#         q.put(None)
#     for t in threads:
#         t.join()



def auto_threshold_image(threshold_setting, tif_file):
    # Open the file
    #IJ.open(tif_file)
    #imp = IJ.getImage()
    imp = IJ.openImage(tif_file)

    # Get inputs/output filepaths
    tif_filename_w_ext = os.path.basename(tif_file)
    tif_filename_wo_ext = os.path.splitext(tif_filename_w_ext)[0]
    tif_basedir = os.path.dirname(tif_file)

     # Validate that the file is not a stack
    if check_if_stack(imp, tif_file):
        log.append("ERROR auto_threshold_image: " + tif_file + " is a stack, skipping...", printout=True)
        exit()

    IJ.run(imp, "8-bit", "")
    IJ.setAutoThreshold(imp, threshold_setting)
    IJ.run(imp, "Convert to Mask", "")
    
    # Determine and save the file to the output path
    output_path = os.path.join(tif_basedir, tif_filename_wo_ext  + "_auto-thresholded.tif")
    IJ.saveAs(imp, "Tiff", output_path)
    imp.close()
    #print("Saved thresholded image to " + output_path)
    return output_path

def worker():
    while True:
        item = q.get()
        if item is None:
            # No more items to process
            break
        threshold_setting, tif_file = item
        output_path = auto_threshold_image(threshold_setting, tif_file)
        output_paths_queue.put(output_path)  # Append the output path to the queue
        q.task_done()
        print("\nThread {} completed processing {}".format(threading.current_thread().name, os.path.basename(tif_file)))

def batch_auto_threshold(file_list, directory, thresholding_settings):

    # Get the tif files from the directory if a file_list has not been created from a previous process.
    if file_list is None or len(file_list) < 1:
        file_list = find_tif_files(directory)
        log.append("batch_auto_threshold did not receive a file_list, defaulting to directory: " + directory, printout=True)
        log.append("Found " + str(len(file_list)) + " files in " + directory, printout=True)

    log.append("Found " + str(len(file_list)) + " files in file_list", printout=True)

    # TO RUN THIS PROCESS FASTER, UNCOMMENT OUT THE LINE BELOW AND COMMENT THE max_threads LINE AFTER THAT
    #max_threads = 12
    max_threads = Runtime.getRuntime().availableProcessors() // 2
    setting, threshold_mode, dark_bg, stack_hist, rst_range, save_thresholded_images = thresholding_settings

    log.append("Starting batch_auto_threshold using " + str(max_threads) + " and thresholding setting: " + setting, printout=True)

    # Create a queue to hold tasks
    global q
    q = Queue.Queue()

    # Create a queue for output paths
    global output_paths_queue
    output_paths_queue = Queue.Queue()

    # Start worker threads
    threads = []
    for i in range(max_threads):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    # Enqueue tasks
    for tif_file in file_list:
        q.put((setting, tif_file))

    # Block until all tasks are done
    q.join()

    # Stop workers
    for i in range(max_threads):
        q.put(None)
    for t in threads:
        t.join()

    # Collect output paths from the queue
    output_paths = []
    while not output_paths_queue.empty():
        output_paths.append(output_paths_queue.get())

    return output_paths, directory

# ___________________________________________________________________________________________________________ANALYZE PARTICLES FUNCTIONS
#*************************************************************************************************************

def batch_analyze_particles(file_list, directory, analysis_settings):
    size_min, size_max, include_holes_checked, merge_mode = analysis_settings
    output_csv_list = []
    
    # Get the tif files from the directory if a file_list has not been created from a previous process.
    if file_list is None or len(file_list) < 1:
        file_list = find_tif_files_with_string(directory, "_auto-thresholded.tif")
        log.append("batch_analyze_particles did not receive a file_list, defaulting to directory: " + directory, printout=True)
        log.append("Found " + str(len(file_list)) + " files in " + directory, printout=True)


    for index, tif_file in enumerate(file_list):

        # Validate the file as existing and quit if not
        if not os.path.isfile(tif_file):
            log.append("ERROR: " + tif_file + " could not be found/does not exist. Skipping...", printout=True)
            continue

        # Generate inputs/outputs
        tif_filename_w_ext = os.path.basename(tif_file)
        tif_filename_wo_ext = os.path.splitext(tif_filename_w_ext)[0]
        tif_basedir = os.path.dirname(tif_file)
        output_csv = (tif_basedir + "\\" + tif_filename_wo_ext + ".csv")

        # Track progress
        print("\nProcessing " + str(tif_file) + "... " + str(index + 1) + "/" + str(len(file_list)))

        # Open the file
        imp = IJ.openImage(tif_file)

        # Validate that the file is not a stack
        if check_if_stack(imp, tif_file):
            log.append("ERROR batch_analyze_particles: " + tif_filename_w_ext + " is a stack, skipping...", printout=True)
            continue
        
        # # Determine and save the file to the output path
        # output_path = os.path.join(tif_basedir, tif_filename_wo_ext  + "_auto-thresholded.tif")
        # IJ.saveAs(imp, "Tiff", output_path)
        # imp.close()

        analyze_particles_parameters = "size=" + size_min + "-" + size_max + " pixel show=Overlay display clear"

        # Pass the include holes option into the analysis parameters
        if include_holes_checked:
            analyze_particles_parameters = analyze_particles_parameters + " include"

        # Run the analysis and save the results
        IJ.run(imp, "Analyze Particles...", analyze_particles_parameters)
        IJ.saveAs("Results", output_csv)

        if os.path.isfile(output_csv):
            log.append("Completed Analyzing Particles for " + tif_filename_w_ext + " Output CSV:" + output_csv + "", printout=True)
            output_csv_list.append(output_csv)
        else:
            log.append("Process ran, but did not produce output CSV for " + tif_filename_wo_ext, printout=True)

        imp.close()


    return output_csv_list, directory


# ___________________________________________________________________________________________________________SINGLE THRESHOLD AND ANALYZE PARTICLES
#*************************************************************************************************************

def single_threshold_and_analyze(file_list, directory, thresholding_settings, analysis_settings):
    threshold_setting, threshold_mode, dark_bg, stack_hist, rst_range, save_thresholded_images = thresholding_settings
    size_min, size_max, include_holes_checked, merge_mode = analysis_settings
    output_csv_list = []

    # Get the tif files from the directory if a file_list has not been created from a previous process.
    if file_list is None or len(file_list) < 1:
        file_list = find_tif_files(directory)
        log.append("single_threshold_and_analyze did not receive a file_list, defaulting to directory: " + directory, printout=True)
        log.append("Found " + str(len(file_list)) + " files in " + directory, printout=True)


    for index, tif_file in enumerate(file_list):

        # Validate the file as existing and quit if not
        if not os.path.isfile(tif_file):
            log.append("ERROR: " + tif_file + " could not be found/does not exist. Skipping...", printout=True)
            continue

        # Generate inputs/outputs
        tif_filename_w_ext = os.path.basename(tif_file)
        tif_filename_wo_ext = os.path.splitext(tif_filename_w_ext)[0]
        tif_basedir = os.path.dirname(tif_file)
        output_csv = (tif_basedir + "\\" + tif_filename_wo_ext + ".csv")

        # Track progress
        print("\nProcessing " + str(tif_file) + "... " + str(index + 1) + "/" + str(len(file_list)))

        # Open the file
        imp = IJ.openImage(tif_file)

        # Validate that the file is not a stack
        if check_if_stack(imp, tif_file):
            log.append("ERROR single_threshold_and_analyze: " + tif_filename_w_ext + " is a stack, skipping...", printout=True)
            continue

        # Threshold the image
        IJ.run(imp, "8-bit", "")
        IJ.setAutoThreshold(imp, threshold_setting)
        IJ.run(imp, "Convert to Mask", "")
        
        # # Determine and save the file to the output path
        # output_path = os.path.join(tif_basedir, tif_filename_wo_ext  + "_auto-thresholded.tif")
        # IJ.saveAs(imp, "Tiff", output_path)
        # imp.close()

        analyze_particles_parameters = "size=" + size_min + "-" + size_max + " pixel show=Overlay display clear"

        # Pass the include holes option into the analysis parameters
        if include_holes_checked:
            analyze_particles_parameters = analyze_particles_parameters + " include"

        # Run the analysis and save the results
        IJ.run(imp, "Analyze Particles...", analyze_particles_parameters)
        IJ.saveAs("Results", output_csv)

        if os.path.isfile(output_csv):
            log.append("Completed Analyzing Particles for " + tif_filename_w_ext + " Output CSV:" + output_csv + "", printout=True)
            output_csv_list.append(output_csv)
        else:
            log.append("Process ran, but did not produce output CSV for " + tif_filename_wo_ext, printout=True)

        imp.close()

    return output_csv_list, directory


# ___________________________________________________________________________________________________________SINGLE THRESHOLD AND ANALYZE PARTICLES
#*************************************************************************************************************
def call_csv_merge(file_list, directory, merge_mode, csv_merger_script_fp, merged_csv_output_fp):

    # Get the tif files from the directory if a file_list has not been created from a previous process.
    if file_list is None or len(file_list) < 1:
        file_list = find_csv_files(directory)
        log.append("call_csv_merge did not receive a file_list, defaulting to directory: " + directory, printout=True)
        log.append("Found " + str(len(file_list)) + " CSV files in " + directory, printout=True)

    # Add all of the files to merge into a file and pass that .txt file's path onto the CSV_Merge.py
    filelist_txt_fp = os.path.join(os.path.dirname(csv_merger_script_fp), "Files_to_merge.txt")
    for file_path in file_list:
        with open(filelist_txt_fp, "a") as write_file:
            write_file.write(file_path + "\n")

    # csv_list_argument = ",".join(file_list)
    # if csv_list_argument.startswith(","):
    #     csv_list_argument = csv_list_argument[1:]
    # if csv_list_argument.endswith(","):
    #     csv_list_argument = csv_list_argument[:-1]

    # # Put the arguments in quotes so any spaces in the filepaths will not confuse argparse
    csv_merger_script_fp = "\"" + csv_merger_script_fp + "\""
    # csv_list_argument =  "\"" + csv_list_argument + "\""
    merged_csv_output_fp =  "\"" + merged_csv_output_fp + "\""
    command = "python " + csv_merger_script_fp + " --outputPath " + merged_csv_output_fp + " --CSVlist " + str(filelist_txt_fp) + " --mergeMode " + merge_mode
    
    log.append("\n\nMERGE COMMAND:")
    log.append(command)
    log.append("\n\n")

    output_message = subprocess.check_output(command, shell=True)
    output_message = output_message.decode('utf-8')
    log.append(output_message, printout=True)

    if os.path.isfile(merged_csv_output_fp):
        return merged_csv_output_fp
    else:
        customError("ERROR call_csv_merge: was not able to find merged_csv_output_fp after generation: " + merged_csv_output_fp)


# ___________________________________________________________________________________________________________RETRIEVE SETTINGS AND RUN MAIN
#*************************************************************************************************************

log = RunLog()
log.append("Starting analysis")
log.append(("Generated runlog: " + log.run_log_fp))


full_workflow_settings = get_analysis_workflow()

# Print out the settings and initiate the workflow functions
if full_workflow_settings != "cancelled":
    # Start with the list of files to process as None in case the user starts the process without organizing or thresholding
    file_list = None
    # Unpack the settings for each step+
    step_list, organization_settings, thresholding_settings, analysis_settings, directory, merged_csv_output_dir = full_workflow_settings
    # Unpack the chosen steps
    organize_tif_bool, auto_threshold_bool, analyze_particles_bool= step_list
    # Get the settings formatted for printing
    step_list_string, organization_settings_string, thresholding_settings_string, analysis_settings_string, directory_string, merged_csv_output_dir_string = get_settings_strings(step_list, organization_settings, thresholding_settings, analysis_settings, directory, merged_csv_output_dir, print_settings=True)

    # Write the settings to the log
    log.append("**********************USER-INPUT ANALYSIS WORKFLOW SETTINGS:**********************", printout=True)
    log.append(step_list_string, printout=True)
    log.append(organization_settings_string, printout=True)
    log.append(thresholding_settings_string, printout=True)
    log.append(analysis_settings_string, printout=True)
    log.append(directory_string, printout=True)
    log.append(merged_csv_output_dir_string + "\n\n", printout=True)

    # ORGANIZING
    if organize_tif_bool:
        log.append("**********************STARTING FILE ORGANIZATION**********************", printout=True)
        print(organization_settings_string)
        print("Target Directory: " + directory)
        
        file_list, directory = batch_organize_files(directory, organization_settings)

        print(len(file_list))
        print(directory)
        log.append("**********************ORGANIZATION COMPLETE**********************\n\n", printout=True)

    # THRESHOLDING
    if auto_threshold_bool:
        setting, threshold_mode, dark_bg, stack_hist, rst_range, save_thresholded_images = thresholding_settings

        if analyze_particles_bool is True and save_thresholded_images is False:
            log.append("**********************STARTING THRESHOLDING AND ANALYZING PARTICLES**********************", printout=True)
            print(thresholding_settings_string)
            print("Target Directory: " + directory)

            size_min, size_max, include_holes_checked, merge_mode = analysis_settings
            
            file_list, directory = single_threshold_and_analyze(file_list, directory, thresholding_settings, analysis_settings)
            # file_list is now a list of .csv filepaths

            analyze_particles_bool = False

            log.append("**********************THRESHOLDING AND ANALYZING PARTICLES COMPLETE**********************\n\n", printout=True)


        if save_thresholded_images is True:

            log.append("**********************STARTING THRESHOLDING**********************", printout=True)
            print(thresholding_settings_string)
            print("Target Directory: " + directory)

            file_list, directory = batch_auto_threshold(file_list, directory, thresholding_settings)

            log.append("**********************THRESHOLDING COMPLETE**********************\n\n", printout=True)
    

    # ANALYZING
    if analyze_particles_bool:
        log.append("**********************STARTING ANALYZE PARTICLES**********************", printout=True)
        size_min, size_max, include_holes_checked, merge_mode = analysis_settings
        print(thresholding_settings_string)
        print("Target Directory: " + directory)

        file_list, directory = batch_analyze_particles(file_list, directory, analysis_settings)

        # INSERT FUNCTION HERE
        # file_list, directory = batch_analyze_particles(filelist, directory, analysis_settings)

        log.append("**********************ANALYZE PARTICLES COMPLETE**********************\n\n", printout=True)


        # MERGING
        if merge_mode != "Don't merge":
            if merge_mode == "Horizontal merge":
                merge_mode = "0"
            if merge_mode == "Vertical merge (Spotfire)":
                merge_mode = "1"

            log.append("**********************STARTING MERGE CSV**********************\n\n", printout=True)
            merge_script_fp = get_csv_merger_py_path()
            
            # Get formatted date and time
            timestr = formattedtime()
            current_datetime = timestr.get_time_str()

            merged_csv_output_fp = os.path.join(merged_csv_output_dir, "Merged_output_on_" + current_datetime + ".csv")
            merged_csv_output_fp = call_csv_merge(file_list, directory, merge_mode, merge_script_fp, merged_csv_output_fp)
            log.append("**********************MERGE CSV COMPLETE**********************\n\n", printout=True)
            log.append("\nProcess completed, Merged CSV output: " + str(merged_csv_output_fp), printout=True)
        else:
            log.append("merge_mode was \'Don't merge\', skipping merge...", printout=True)

print("\n\n\nRun Log filepath: " + str(log.run_log_fp))
print("Merged CSV output: " + str(merged_csv_output_fp))





# TODO: add an error confirmation function between each step which checks the log file for the word "ERROR" and returns that line in a dialog box
# if the user clicks ok, the process continues, if the user clicks cancel, exit out of the program.



exit()

full_workflow_settings = get_analysis_workflow()
# Print out the settings
if full_workflow_settings != "cancelled":
    step_list, organization_settings, thresholding_settings, analysis_settings, directory = full_workflow_settings
    get_settings_strings(step_list, organization_settings, thresholding_settings, analysis_settings, directory, print_settings=True)

    # Unpack the steps
    organize_tif_bool, auto_threshold_bool, analyze_particles_bool= step_list

    # Unpack Organization Settings
    if organize_tif_bool:
        organize_mode, move_copy, string1, string2, generate_log = organization_settings
        print("ORGANIZATION SETTINGS DEBUG:")
        print("\torganize_mode: " + str(organize_mode))
        print("\tmove_copy: " + str(move_copy))
        print("\tstring1: " + str(string1))
        print("\tstring2: " + str(string2))
        print("\tgenerate_log: " + str(generate_log))

    # Unpack Thresholding Settings
    if auto_threshold_bool:
        setting, threshold_mode, dark_bg, stack_hist, rst_range, save_thresholded_images = thresholding_settings
        print("AUTO THRESHOLD SETTINGS DEBUG:")
        print("\tsetting: " + str(setting))
        print("\tthreshold_mode: " + str(threshold_mode))
        print("\tdark_bg: " + str(dark_bg))
        print("\tstack_hist: " + str(stack_hist))
        print("\trst_range: " + str(rst_range))
        print("\tsave_thresholded_images: " + str(save_thresholded_images))

    # Unpack Analysis Settings
    if analyze_particles_bool:
        
        size_min, size_max, include_holes_checked, merge_mode = analysis_settings
        print("ANALYZE PARTICLES SETTINGS DEBUG:")
        print("\tsize_min: " + str(size_min))
        print("\tsize_max: " + str(size_max))
        print("\tinclude_holes_checked: " + str(include_holes_checked))
        print("\tmerge_mode: " + str(merge_mode))




# Main goes here






print("Run Log filepath:" + log.run_log_fp)
























# def organize_script(organize_mode, move_copy, string1, string2, generate_log):
#         # ___________________________________________________________________________________________________________FILE ORGANIZATION
#     #****************************************************************************************************************
    
#     # Make empty filelist so that it can be assigned if files are organized
#     # Filelist will otherwise default to the tif files in the user-selected directory (dir)
#     organized_tif_filelist = []

#     # Get the organization settings from user
#     result = get_organization_settings()
#     if result == "cancelled":
#         print("User cancelled get_organization_settings, exiting...")
#         exit()
#     else:
#         organize_mode, move_copy, string1, string2, generate_log = result


#     # Get the directory containing all the tif files from user
#     dir = IJ.getDirectory("ORGANIZE FILES: Select a directory containing .tif files to organize")
#     if dir == None:
#         print("User cancelled getDirectory, exiting...")
#         exit()


#     if organize_mode != "Don't Organize":
#         # Organize the files and return the list of errors
#         moved_copied_files, errored_files = organize_files(organize_mode, move_copy, string1, string2, dir)

#         # Print out all the files that have been moved/copied
#         for source, dest in moved_copied_files:
#             print("Source: " + source + ", Destination: " + str(dest))
#         print(len(moved_copied_files))

#         # Print out all the files that have met error conditions
#         for file, reason in errored_files:
#             print("Source: " + file + ", " + reason)
#         print(len(errored_files))

#         # Return the list of files to iterate through if the files have been organized
#         organized_tif_filelist = [dest for source, dest in moved_copied_files]

#         if generate_log is True:
#             log_fp = os.path.join(os.path.dirname(os.getcwd()), "organization_log.txt")
#             print("Generated log file: " + log_fp)

#             with open(log_fp, "w") as log:
#                 log.write("******FILES " + move_copy.upper() + "******\n")
#                 for source, dest in moved_copied_files:
#                     log.write(str(source) + " to " + str(dest) + "\n")

#                 log.write("\n\n******ERRORS******\n")
#                 for file, reason in errored_files:
#                     log.write(str(file) + " errored, " + str(reason) + "\n")


#     if len(organized_tif_filelist) > 0:
#         # Get the organized list of tif files
#         filelist = organized_tif_filelist
#     else:
#         # Get the list of tif files to iterate through
#         filelist = (find_tif_files(dir))
    
#     return filelist