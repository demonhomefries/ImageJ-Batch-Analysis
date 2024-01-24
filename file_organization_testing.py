import os
import time
import Queue
import shutil
import subprocess
import threading
from ij import IJ
from ij.io import OpenDialog
from ij.gui import GenericDialog
from java.awt.event import ActionListener

# ______________________________________________________________________________________USER INTERFACE FUNCTIONS
#***************************************************************************************
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
    merge_options = ["Don't merge", "Horizontal merge", merge_mode]
    gd.addChoice("Merge mode", merge_options, merge_options[2])
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
        return "384-well", "Move", "Confocal", "Brightfield", False
    else:
        return organize_mode, move_copy, string1, string2, generate_log
    
class OrganizationSettingsListener(ActionListener):
    def __init__(self):
        organize_mode = "384-well"
        move_copy = "Move"
        string1 = "Confocal"
        string2 = "Brightfield"
        generate_log = False
        self.organization_settings = organize_mode, move_copy, string1, string2, generate_log

    def actionPerformed(self, event):
        organize_mode, move_copy, string1, string2, generate_log = self.organization_settings
        self.organization_settings = get_organization_settings(organize_mode, move_copy, string1, string2, generate_log)

def get_settings_strings(step_list, organization_settings, thresholding_settings, analysis_settings, directory, print_settings):

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
    directory = None
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
        # Directory Input settings setup
        gd.addDirectoryField("Directory: ", directory, 50)

        gd.showDialog()
        tif_organization_yn1 = gd.getNextBoolean()
        threshold_yn2 = gd.getNextBoolean()
        analyze_particles_yn3 = gd.getNextBoolean()
        directory = gd.getNextString()
        
        # Step list as a list for easier unpacking
        step_list = [tif_organization_yn1, threshold_yn2, analyze_particles_yn3]

        # The following error conditions will show a warning dialog if met:
        if gd.wasCanceled():
            print("get_analysis_workflow: CANCELLED")
            return "cancelled"
        
        if directory == "" or directory is None:
            warning_dialog("The directory has not been set. Please select a valid directory.")
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
        confirmation = confirmation_dialog(step_list, orgListener.organization_settings, threshListener.thresholding_settings, analysisListener.analysis_settings, directory)
        
        # Exit out of the loop if the confirmation was OKed or go back to the main dialog if it was cancelled
        if confirmation == "ok":
            get_settings_strings(step_list, orgListener.organization_settings, threshListener.thresholding_settings, analysisListener.analysis_settings, directory, print_settings=False)
            return step_list, orgListener.organization_settings, threshListener.thresholding_settings, analysisListener.analysis_settings, directory

# ______________________________________________________________________________________ORGANIZATION FUNCTIONS
#***************************************************************************************
        
# ______________________________________________________________________________________AUTO THRESHOLDING FUNCTIONS
#***************************************************************************************
        
# ______________________________________________________________________________________ANALYZE PARTICLES FUNCTIONS
#***************************************************************************************
        
# ______________________________________________________________________________________RETRIEVE SETTINGS
#***************************************************************************************
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





# def organize_script(organize_mode, move_copy, string1, string2, generate_log):
#         # ______________________________________________________________________________________FILE ORGANIZATION
#     #***************************************************************************************
    
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