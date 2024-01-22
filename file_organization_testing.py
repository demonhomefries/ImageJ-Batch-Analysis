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

def warning_dialog(message):
    warning_dialog = GenericDialog("Warning")
    warning_dialog.addMessage(message)
    warning_dialog.showDialog()


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
            warning_dialog("The directory has not been set. Please select a valid directory.")
            continue

        if tif_organization_yn1 and orgListener.organization_settings is None:
            warning_dialog("Tif organization has been selected but organization settings have not been chosen.")
            continue

        if threshold_yn2 and threshListener.thresholding_settings is None:
            warning_dialog("Auto-thresholding has been selected but thresholding settings have not been chosen.")
            continue

        if analyze_particles_yn3 and analysisListener.analysis_settings is None:
            warning_dialog("Analyze particles has been selected but analysis settings have not been chosen.")
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


