from ij import IJ
from ij.gui import GenericDialog
import time
import os
from ij.io import DirectoryChooser
from java.awt.event import ActionListener

# def get_time_elapsed(start_time, process):
#     current_time = time.time()
#     time_elapsed_seconds = current_time - start_time
#     time_elapsed_milliseconds = time_elapsed_seconds * 1000
#     time_elapsed = "{:.2f} milliseconds".format(time_elapsed_milliseconds)

#     print("Time elapsed: {} for {}".format(time_elapsed, process))
#     start_time = time.time()
#     return start_time

# def find_tif_files(directory):
#     tif_files = []

#     for root, dirs, files in os.walk(directory):
#         for filename in files:
#             if filename.endswith('.tif'):
#                 tif_files.append(os.path.join(root, filename))

#     return tif_files

# def get_autothresholded_tifs(dir):
#     master_list = find_tif_files(dir)
#     master_list = [file for file in master_list if "auto-thresholded" in file]
#     return master_list

# def get_thresholded_or_not_choice():
#     gd = GenericDialog("Threshold Settings")
#     gd.addMessage("Organize tif files or continue to Analyze Particles")
#     gd.addCheckbox("Use files with \'_auto-thresholded\' in name?", False)
#     gd.showDialog()
#     choice = gd.getNextBoolean()

#     print("Get thresholded files?:\n\tChoice: " + str(choice))
#     return choice


def validate_and_correct_order(steps):
    # Define the correct order of steps
    correct_order = [
        "Organize Files",
        "Auto-threshold",
        "Analyze Particles + Generate CSVs",
        "Merge CSVs"
    ]

    # Create a dictionary for the steps and their order
    step_order = {step: i for i, step in enumerate(correct_order)}

    # Filter out empty steps and sort the remaining steps based on the correct order
    filtered_steps = [step for step in steps if step in step_order]
    sorted_steps = sorted(filtered_steps, key=lambda x: step_order[x])

    # Fill in the missing steps with empty strings to maintain the length of the list
    sorted_steps += [""] * (len(steps) - len(sorted_steps))

    return sorted_steps

def get_particle_analysis_settings():
    # Set parameter for pixel^2 size.
    # Get these into the same dialog box
    # size_min = IJ.getString("pixel^2 size minimum: ", "30")
    # size_max = IJ.getString("pixel^2 size maximum: ", "Infinity")

    # Get the minimum and maximum particle analysis parameters
    gd = GenericDialog("Enter particle min/max sizes")
    gd.addStringField("Pixel^2 size minimum", "30")
    gd.addStringField("Pixel^2 size maximum:", "Infinity")
    gd.addCheckbox("Include holes", False)
    merge_options = ["Horizontal merge", "Vertical merge (Spotfire)"]
    gd.addChoice("Merge mode", merge_options, merge_options[0])
    gd.showDialog()
    include_holes_checked = gd.getNextBoolean()
    merge_mode = gd.getNextChoice()
    size_min = gd.getNextString()
    size_max = gd.getNextString()

    if gd.wasCanceled():
        print("get_particle_analysis_settings: CANCELLED ")
        return "cancelled"

    # print("\nChosen Settings: \nsize_min: " + size_min 
    #       + " \nsize_max: " + size_max 
    #       + "\ninclude_holes: " + str(include_holes_checked) 
    #       + "\nMerge Mode: " + merge_mode)

    if merge_mode == "Horizontal merge":
        merge_mode = "0"
    elif merge_mode == "Vertical merge (Spotfire)":
        merge_mode = "1"

    return size_min, size_max, include_holes_checked, merge_mode

def get_thresholding_settings():

    # Set default values
    dark_bg = False
    stack_hist = False
    rst_range = False

    # Initialize the dialog
    gd = GenericDialog("Threshold Settings")

    thresh_mode = ["Default", "Huang", "Intermodes", "IsoData", "IJ_IsoData", "Li", "MaxEntropy", "Mean", "MinError", "Minimum", "Moments", "Otsu", "Percentile", "RenyiEntropy", "Shanbhag", "Triangle", "Yen"]
    gd.addChoice("Threshold Mode", thresh_mode, thresh_mode[0])

    # clr_mode = ["Red", "B&W", "Over/Under"]
    # gd.addChoice("Color Mode", clr_mode, clr_mode[0])
    gd.addCheckbox("Dark Background", False)
    gd.addCheckbox("Stack Histogram", False)
    gd.addCheckbox("Don't reset range", False)
    gd.addCheckbox("Save thresholded images?", False)
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
        print("get_thresholding_settings: CANCELLED ")
        return "cancelled"
    else:
        return setting, save_thresholded_images, [threshold_mode, dark_bg, stack_hist, rst_range]

def get_organization_settings():

    # Initialize the dialog
    gd = GenericDialog("Organize images?")

    gd.addMessage("Choose how images will be organized into folders before\nthe particle analysis script is run.")

    organize_choices = ["Don't Organize", "96-well", "384-well"]
    gd.addChoice("Organization", organize_choices, organize_choices[2])

    move_copy_choices = ["Move", "Copy"]
    gd.addChoice("Move or Copy?", move_copy_choices, move_copy_choices[0])

    gd.addMessage("Input unique strings to differentiate groups of images.\nEach image containing the following string will be\nplaced into its respective folder.\n(Case Sensitive)")
    gd.addStringField("String 1", "Confocal")
    gd.addStringField("String 2", "BrightField")
    gd.addCheckbox("Generate organization & error log", False)
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
        print("get_organization_settings: CANCELLED ")
        return "cancelled"
    else:
        return organize_mode, move_copy, string1, string2, generate_log


def get_settings_strings(step_list, organization_settings, thresholding_settings, analysis_settings, directory, print_settings):

    if step_list is not None:
        [tif_organization_yn1, threshold_yn2, analyze_particles_yn3, csv_merge_yn4] = step_list
        step_list_string = ("User Selected Workflow:"
            + "\n       Organize tif files?: " + str(tif_organization_yn1) 
            + "\n       Auto-threshold?: " + str(threshold_yn2)
            + "\n       Analyze Particles?: " + str(analyze_particles_yn3)
            + "\n       Merge CSVs?: " + str(csv_merge_yn4))

    if organization_settings is not None:
        organize_mode, move_copy, string1, string2, generate_log = organization_settings
        organization_settings_string = ("Organization Settings:"
                        + "\n       Organize Mode: " + str(organize_mode)
                        + "\n       Move/Copy: " + str(move_copy)
                        + "\n       String 1: " + str(string1) 
                        + "\n       String 2: " + str(string2)
                        + "\n       Generate Log: " + str(generate_log))
    else:
        organization_settings_string = ("Organization Settings: None")

    if thresholding_settings is not None:
        setting, save_thresholded_images, [threshold_mode, dark_bg, stack_hist, rst_range] = thresholding_settings
        thresholding_settings_string = ("Auto-threshold Settings:" 
                        + "\n       Thresholding Mode: " + threshold_mode 
                        + "\n       Dark Background: " + str(dark_bg) 
                        + "\n       Stack Histogram: " + str(stack_hist) 
                        + "\n       Don't reset range: " + str(rst_range)
                        + "\n       Save thresholded image: " + str(save_thresholded_images)
                        + "\n       Command: " + str(setting))
    else:
        thresholding_settings_string = ("Auto-threshold Settings: None")
    
    if analysis_settings is not None:
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
    
    if print_settings:
        print(step_list_string + "\n"
            + organization_settings_string + "\n"
            + thresholding_settings_string + "\n"
            + analysis_settings_string + "\n"
            + directory_string)

    return step_list_string, organization_settings_string, thresholding_settings_string, analysis_settings_string, directory_string


class OrganizationSettingsListener(ActionListener):
    def __init__(self):
        self.organization_settings = None
    def actionPerformed(self, event):
        self.organization_settings = get_organization_settings()

class ThresholdingSettingsListener(ActionListener):
    def __init__(self):
        self.thresholding_settings = None
    def actionPerformed(self, event):
        self.thresholding_settings = get_thresholding_settings()

class AnalysisSettingsListener(ActionListener):
    def __init__(self):
        self.analysis_settings = None
    def actionPerformed(self, event):
        self.analysis_settings = get_particle_analysis_settings()

def confirmation_dialog(step_list, organization_settings, thresholding_settings, analysis_settings, directory):

    step_list_string, organization_settings_string, thresholding_settings_string, analysis_settings_string, directory_string = get_settings_strings(step_list, organization_settings, thresholding_settings, analysis_settings, directory, print_settings=True)

    confirm_dialog = GenericDialog("Confirm settings")
    confirm_dialog.addMessage(step_list_string)
    confirm_dialog.addMessage(organization_settings_string)
    confirm_dialog.addMessage(thresholding_settings_string)
    confirm_dialog.addMessage(analysis_settings_string)
    confirm_dialog.addMessage(directory_string)
    confirm_dialog.addMessage("\n\nIf the settings above are correct, click OK to continue.\nTo revise these settings, click Cancel.")
    confirm_dialog.showDialog()

    if confirm_dialog.wasCanceled():
        return("cancelled")
    elif confirm_dialog.wasOKed():
        return("ok")
    # If user OKs the dialog, return true to the get_analysis_workflow dialog and pass on the variables to the initial function call
    # If user cancels the dialog, go back to the get_analysis_workflow dialog with the currently chosen settings




def get_analysis_workflow():
    # Instantiate the listeners
    orgListener = OrganizationSettingsListener()
    threshListener = ThresholdingSettingsListener()
    analysisListener = AnalysisSettingsListener()

    while True:
        gd = GenericDialog("Set up analysis workflow")
        # Organization
        gd.addCheckbox("Organize tif files", True)
        gd.addButton("Organization Settings", orgListener)
        gd.addMessage("")
        # Thresholding
        gd.addCheckbox("Auto-threshold", True)
        #gd.addCheckbox("Save thresholded files", False)
        gd.addButton("Auto-thresholding Settings", threshListener)
        gd.addMessage("")
        # Analyze Particles
        gd.addCheckbox("Analyze particles & generate CSVs", True)
        gd.addButton("Analysis Settings", analysisListener)
        gd.addMessage("")
        # Merge CSVs
        gd.addCheckbox("Merge CSVs", True)
        gd.addMessage("")

        # Directory Input
        gd.addDirectoryField("Directory: ", "", 30)

        gd.showDialog()

        tif_organization_yn1 = gd.getNextBoolean()
        threshold_yn2 = gd.getNextBoolean()
        analyze_particles_yn3 = gd.getNextBoolean()
        csv_merge_yn4 = gd.getNextBoolean()
        directory = gd.getNextString()

        step_list = [tif_organization_yn1, threshold_yn2, analyze_particles_yn3, csv_merge_yn4]

        # ERROR CONDITIONS:
        if gd.wasCanceled():
            print("get_analysis_workflow: CANCELLED")
            return "cancelled"
        
        if directory == "" or directory.strip() is None:
            warning_dialog = GenericDialog("Warning")
            warning_dialog.addMessage("The directory has not been set. Please select a valid directory.")
            warning_dialog.showDialog()
            continue
        
        # cannot have any option sequence with a space in the middle (i.e. True False True True)
        """
        organize and analyze
        threshold and merge 
        organize and merge
        organize, threshold, and merge (without analyze)
        organize, analyse, merge (warning needed if skipping threshold)

        """
        #cannot have analyze particles and generate CSVs alone unless all of the files are already thresholded (make a separate warning dialog for these)
        #

        confirmation = confirmation_dialog(step_list, orgListener.organization_settings, threshListener.thresholding_settings, analysisListener.analysis_settings, directory)
        if confirmation == "ok":
            get_settings_strings(step_list, orgListener.organization_settings, threshListener.thresholding_settings, analysisListener.analysis_settings, directory, print_settings=True)
            return step_list, directory, orgListener.organization_settings, threshListener.thresholding_settings, analysisListener.analysis_settings











full_workflow_settings = get_analysis_workflow()

# Print out the settings
if full_workflow_settings != "cancelled":
    step_list, directory, organization_settings, thresholding_settings, analysis_settings = full_workflow_settings
    step_list_string, organization_settings_string, thresholding_settings_string, analysis_settings_string, directory_string = get_settings_strings()
    print(step_list_string)
    print(organization_settings_string)
    print(thresholding_settings_string)
    print(analysis_settings_string)
    print(directory_string)












# def get_organize_analyze_option():
#     gd = GenericDialog("Pre-analysis check")

#     gd.addMessage("Organize tif files or continue to Analyze Particles")

#     initial_options = ["Organize files", "Analyze Particles"]
#     gd.addChoice("Action:", initial_options, initial_options[0])
#     gd.showDialog()

#     initial_action = gd.getNextChoice()

#     if gd.wasCanceled():
#         print("get_particle_analysis_settings: CANCELLED ")
#         return "cancelled"
#     else:
#         print("Initial Action Settings:\n\tAction: " + str(initial_action))
#         return initial_action

# initial_action = get_organize_analyze_option()
# if initial_action == "cancelled":
#     pass











































# import os 
# import sys
# from ij import IJ, WindowManager
# from ij.measure import ResultsTable
# from ij.io import FileInfo, OpenDialog
# from ij.gui import GenericDialog


# def get_organize_analyze_option():
#     gd = GenericDialog("Pre-analysis check")
#     # Add a message to the dialog
#     gd.addMessage("Do you want organize your tif files before analyzing particles?")

#     # Add "Yes" and "No" buttons
#     gd.addChoice("Choose an option", ["Yes", "No"], "Yes")

#     # Show the dialog
#     gd.showDialog()

#     # Check the user's response
#     if gd.wasOKed():
#         # User clicked "Yes"
#         print("User clicked Yes. Continue with the action.")
#         # Add your code for "Yes" option here
#     else:
#         # User clicked "No" or closed the dialog
#         print("User clicked No or closed the dialog. Cancel the action.")
#         # Add your code for "No" or closing the dialog here




# get_organize_analyze_option()


























# def list_files(directory):
#     try:
#         # Get the list of files in the directory
#         files = os.listdir(directory)
        
#         # Filter out directories, keeping only files
#         files = [file for file in files if os.path.isfile(os.path.join(directory, file))]
        
#         return files
#     except Exception as e:
#         print("ERROR list_files: " + e)
#         exit()

# def get_script_path():
#     try:
#         # Use __file__ if it is defined
#         script_path = os.path.abspath(__file__)
#     except NameError:
#         # If __file__ is not defined (e.g., in interactive mode), use sys.argv[0]
#         script_path = os.path.abspath(sys.argv[0])
#     return script_path


# script_path = get_script_path()

# script_dir = os.path.dirname(script_path)
# script_file_list = list_files(script_dir)
# print("Current script_path: " + script_path)

# if "CSV_Merger.py" not in script_file_list:

#     print("ERROR: Could not find CSV Merge script, prompting user...")

#     # Prompt user to find the merge script
#     open_dialog = OpenDialog("Select filepath for CSV_Merger.py")
#     if open_dialog.getPath() is not None:
#         csv_merger_script_fp = open_dialog.getPath()
#     else:
#         print("Failed to find CSV_Merger.py. Exiting program without merging CSVs.")
#         exit()

# elif "CSV_Merger.py" in script_file_list:
#     for file in script_file_list:
#         if "CSV_Merger.py" in file:
#             print("Found CSV_Merger.py: " + file)
#             csv_merger_script_fp = os.path.join(script_dir, file)
#             break
#     if not os.path.isfile(csv_merger_script_fp):
#         print("ERROR: Could not auto-find csv_merger_script_fp: " + csv_merger_script_fp)

# print("csv_merger_script_fp: " + csv_merger_script_fp)
























# def get_organization_settings():

#     # Initialize the dialog
#     gd = GenericDialog("Organize images?")

#     gd.addMessage("Choose how images will be organized into folders before\nthe particle analysis script is run.")

#     organize_choices = ["Don't Organize", "96-well", "384-well"]
#     gd.addChoice("Organization", organize_choices, organize_choices[2])

#     move_copy_choices = ["Move", "Copy"]
#     gd.addChoice("Move or Copy?", move_copy_choices, move_copy_choices[0])

#     gd.addMessage("Input unique strings to differentiate groups of images.\nEach image containing the following string will be\nplaced into its respective folder.\n(Case Sensitive)")
#     gd.addStringField("String 1", "Confocal")
#     gd.addStringField("String 2", "BrightField")
#     gd.addCheckbox("Generate organization & error log", False)
#     gd.showDialog()

#     # Retrieve the values
#     organize_mode = gd.getNextChoice()
#     move_copy = gd.getNextChoice()
#     string1 = gd.getNextString()
#     string2 = gd.getNextString()
#     generate_log = gd.getNextBoolean()
#     print("Organization Settings:\n\tOrganize Mode: " + str(organize_mode)
#            + "\n\tMove/Copy: " + str(move_copy)
#              + "\n\tString 1: " + str(string1) 
#              + "\n\tString 2: " + str(string2)
#              + "\n\tGenerate Log? " + str(generate_log))
    
#     if gd.wasCanceled():
#         print("get_organization_settings: CANCELLED ")
#         return "cancelled"
#     else:
#         return organize_mode, move_copy, string1, string2, generate_log

# result = get_organization_settings()

# if result == "cancelled":
#     print("User cancelled get_organization_settings")
#     exit()
# else:
#     organize_mode, move_copy, string1, string2, generate_log = result


# moved_copied_files = [("s1","d1"), ("s2","d2"), ("s3","d3"), ("s4","d4"), ("s5","d5")]
# errored_files = [("Error1","Reason1: lalalal"), ("Error2","Reason2: lalalal"), ("Error3","Reason3: lalalal"), ("Error4","Reason4: lalalal"), ("Error5","Reason5: lalalal")]

# if generate_log is True:
#     log_fp = os.path.join(os.path.dirname(os.getcwd()), "organization_log.txt")
#     print("Generated log file: " + log_fp)

#     with open(log_fp, "w") as log:
#         log.write("******FILES " + move_copy.upper() + "******\n")
#         for source, dest in moved_copied_files:
#             log.write(str(source) + " to " + str(dest) + "\n")

#         log.write("\n\n******ERRORS******\n")
#         for file, reason in errored_files:
#             log.write(str(file) + " errored, " + str(reason) + "\n")






























# def check_if_stack(imp, tif_file):

#     # Get the filepath to save the metadata information
#     info_file_path = os.path.join(os.getcwd(), "Info for Image")
#     info_file_path = info_file_path + ".txt"

#     # Run the show info macro and save the information to a .txt file
#     IJ.run(imp, "Show Info...", "")
#     basename_w_ext = os.path.basename(tif_file)
#     IJ.selectWindow("Info for " + basename_w_ext)
#     IJ.saveAs("Text", info_file_path)

#     # Close the info window
#     IJ.selectWindow("Info for " + basename_w_ext)
#     IJ.run("Close")

#     # Open the info txt and check that "voxel" is contained in it
#     try:
#         with open(info_file_path, 'r') as file:
#             for line in file:
#                 if 'voxel' in line.lower():
#                     print("check_if_stack: IS A STACK: " + basename_w_ext)
#                     return True
                
#         print("check_if_stack: NOT A STACK: " + basename_w_ext)
#         return False

#     except Exception as e:
#         print("ERROR check_if_stack: info_file_path is " + str(info_file_path) + "\n\n" + str(e))
#         exit()



# tif_file_list = [r"C:\Users\akmishra\Desktop\ImageJ_Automation_V2\test\BrightField_P16_1_005.tif", r"C:\Users\akmishra\Desktop\TdTomato_A4_1_001_Stack.tif"]

# for tif_file in tif_file_list:

#     IJ.open(tif_file)
#     imp = IJ.getImage()

#     if check_if_stack(imp, tif_file) is False:
#         print("Image is not a stack: " + tif_file)
#     else:
#         print("Image is a stack: " + tif_file)

#     imp.close()














# master_folder_path = os.getcwd()
# print(master_folder_path)
# if not master_folder_path.endswith("\\"):
#     master_folder_path = master_folder_path + "\\"
# string1 = "thingylalalala"
# string1_path = os.path.join(master_folder_path + string1)

# print(string1_path)



# def get_wellID_list(type:int):
#     """
#     type: 384 or 96
    
#     """

#     output_list = []

#     if type == 96:
#         for letter in "ABCDEFGH":
#             for number in range(1, 13):
#                 output_list.append(letter + str(number))
#     elif type == 384:
#         for letter in "ABCDEFGHIJKLMNOP":
#             for number in range(1, 25):
#                 output_list.append(letter + str(number))
#     else:
#         print("ERROR get_wellID_list: type not equal to 384 or 96. type is " + type)
#         return None

#     return output_list

# ns_list = get_wellID_list(96)

# print(ns_list)
# print(len(ns_list))

# import os

# def extract_well_id(filename):
#     # Split the filename using underscore as a delimiter
#     parts = filename.split('_')
    
#     # Find the part that represents the well_id
#     for part in parts:
#         if len(part) >= 2 and part[0].isalpha() and part[1:].isdigit():
#             return part
    
#     # If well_id is not found, you can handle it accordingly (e.g., return None or raise an exception)
#     return None

# def get_tif_files(folder_path):
#     tif_files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith(".tif")]
#     return tif_files



# for file in get_tif_files(r"C:\Users\akmishra\Desktop\ImageJ_Automation_V2\E351_TC00913534_Aligned"):
#     wellID = extract_well_id(file)

#     print(f"{file}: {wellID}")




# # Generate inputs/outputs
# tif_filename_w_ext = os.path.basename(tif_file)
# tif_filename_wo_ext = os.path.splitext(tif_filename_w_ext)[0]
# tif_basedir = os.path.dirname(tif_file)
# output_csv = (tif_basedir + "\\" + tif_filename_wo_ext + ".csv")
