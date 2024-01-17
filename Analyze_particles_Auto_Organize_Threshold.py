# Split the filename using underscore as a delimiter (this naming convention should not change from the Gen5 output)
# Well ID is identified as a len >= 2 string where the first character is a number and subsequent characters are digits

csv_merger_script_fp = r"C:\Users\Final Working Scripts\CSV_Merger.py"

from ij.gui import GenericDialog
from ij.io import OpenDialog
from ij import IJ
import subprocess
import threading
import shutil
import Queue
import os

class tc:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'

    @classmethod
    def red(cls, text):
        return cls.RED + text + cls.RESET

    @classmethod
    def green(cls, text):
        return cls.GREEN + text + cls.RESET

    @classmethod
    def yellow(cls, text):
        return cls.YELLOW + text + cls.RESET

    @classmethod
    def blue(cls, text):
        return cls.BLUE + text + cls.RESET

    @classmethod
    def magenta(cls, text):
        return cls.MAGENTA + text + cls.RESET

    @classmethod
    def cyan(cls, text):
        return cls.CYAN + text + cls.RESET

    @classmethod
    def white(cls, text):
        return cls.WHITE + text + cls.RESET

class customError(Exception):
    pass

def add_path_backslash(directory):
    # This function just adds a backslash because apparently os.path.join doesn't add strings as new folders, just concatenates them into the basename/basedir.
    if not directory.endswith("\\"):
        directory = directory + "\\"
    return directory

def get_wellID_list(type):
    """
    type: 384 or 96
    
    """

    output_list = []

    if type == 96:
        for letter in "ABCDEFGH":
            for number in range(1, 13):
                output_list.append(letter + str(number))
    elif type == 384:
        for letter in "ABCDEFGHIJKLMNOP":
            for number in range(1, 25):
                output_list.append(letter + str(number))
    else:
        print("ERROR get_wellID_list: type not equal to 384 or 96. type is " + type)
        return None

    return output_list

def extract_well_id(filename):

    # Split the filename using underscore as a delimiter (this naming convention should not change from the Gen5 output)
    parts = filename.split('_')
    
    # Well ID is identified as a len >= 2 string where the first character is a number and subsequent characters are digits
    for part in parts:
        if len(part) >= 2 and part[0].isalpha() and part[1:].isdigit():
            return part
    
    # If well_id is not found, return None to be processed as an error
    return None

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

def get_csv_files_to_merge(directory):

    if os.path.isfile(directory):
        print("ERROR get_csv_file_to_merge: directory is actually a file: " + directory + " Exiting...")
        exit()

    # Ensure the directory path ends with a separator
    if not directory.endswith(os.path.sep):
        directory += os.path.sep

    # Get a list of all files in the directory
    file_list = os.listdir(directory)

    # Filter the list to include only .csv files
    csv_files = [file for file in file_list if file.lower().endswith('.csv')]

    # Create full file paths
    csv_file_paths = [os.path.join(directory, file) for file in csv_files]

    return csv_file_paths

def get_script_path():
    try:
        # Use __file__ if it is defined
        script_path = os.path.abspath(__file__)
    except NameError:
        # If __file__ is not defined (e.g., in interactive mode), use sys.argv[0]
        script_path = os.path.abspath(sys.argv[0])
    return script_path

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

def find_tif_files(directory):
    tif_files = []

    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.tif'):
                tif_files.append(os.path.join(root, filename))

    return tif_files

def get_autothresholded_tifs(dir):
    master_list = find_tif_files(dir)
    master_list = [file for file in master_list if "auto-thresholded" in file]
    return master_list

def check_if_stack(imp, tif_file):

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

def get_organize_analyze_option():
    
    # Create a dialog box
    gd = GenericDialog("Select action")

    # Present the dialog box with the choices
    gd.addMessage("Organize tif files or continue to Analyze Particles")
    initial_options = ["Organize files", "Auto-threshold", "Analyze Particles", "Merge CSVs"]
    gd.addChoice("Action:", initial_options, initial_options[0])
    gd.showDialog()

    # Retrieve the value
    initial_action = gd.getNextChoice()

    # In case the user cancels out of the dialog box
    if gd.wasCanceled():
        print("get_particle_analysis_settings: CANCELLED ")
        return "cancelled"
    else:
        print("Initial Action Settings:\n\tAction: " + str(initial_action))
        return initial_action
    
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

    print("\nChosen Settings: \nsize_min: " + size_min + " \nsize_max: " + size_max + "\ninclude_holes: " + str(include_holes_checked) + "\nMerge Mode: " + merge_mode)

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
    print("Thresholding Settings:\n\tThresholding Mode: " + threshold_mode 
    + "\n\tDark Background: " + str(dark_bg) 
    + "\n\tStack Histogram: " + str(stack_hist) 
    + "\n\tDon't reset range: " + str(rst_range)
    + "\n\tSave thresholded image: " + str(save_thresholded_images))

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
    print("Organization Settings:\n\tOrganize Mode: " + str(organize_mode)
           + "\n\tMove/Copy: " + str(move_copy)
             + "\n\tString 1: " + str(string1) 
             + "\n\tString 2: " + str(string2)
             + "\n\tGenerate Log: " + str(generate_log))
    
    if gd.wasCanceled():
        print("get_organization_settings: CANCELLED ")
        return "cancelled"
    else:
        return organize_mode, move_copy, string1, string2, generate_log

def get_thresholded_or_not_choice():
    gd = GenericDialog("Threshold Settings")
    gd.addMessage("Organize tif files or continue to Analyze Particles")
    gd.addCheckbox("Use files with \'_auto-thresholded\' in name?", False)
    gd.showDialog()
    choice = gd.getNextBoolean()

    print("Get thresholded files?:\n\tChoice: " + str(choice))
    return choice
    
def organize_files(organize_mode, move_copy, string1, string2, master_folder_path):
    # master_folder_path is the user-selected directory containing all of the tifs.
        # master_folder_path + "_organized" will be the name of the organized folder.

    # For error logging, file move operation reversal
    moved_copied_list = [] # (Source, Destination) - only useful to reverse the operation
    error_list = []

    if not os.path.isdir(master_folder_path):
        raise customError("ERROR organize_files: master_folder_path is not a directory")
    

    # Create the folder for the organized files to live in.
    folder_name = os.path.dirname(master_folder_path)
    organized_folder_path = os.path.join(master_folder_path, folder_name + "_auto-organized")
    print(organized_folder_path)
    os.mkdir(organized_folder_path)

    if not os.path.isdir(organized_folder_path):
        raise customError("ERROR organize_files: failed to create directory " + organized_folder_path)

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

    if not os.path.isdir(string1_folder):
        raise customError("ERROR organize_files: failed to create string1 directory " + string1_folder)

    if not os.path.isdir(string2_folder):
        raise customError("ERROR organize_files: failed to create string2 directory " + string2_folder)

    # Define the error folder's path - should it need to be created for use
    error_folder = os.path.join(organized_folder_path + "Errors")
    error_folder = add_path_backslash(error_folder)
    print("error folder: " + error_folder)

    # Get tif file list from the master folder (remember this is filtered for filesize)
    file_list = find_tif_files(master_folder_path)

    # Determine the folder structure
    if organize_mode == "96-well":
        well_id_list = get_wellID_list(96)
    elif organize_mode == "384-well":
        well_id_list = get_wellID_list(384)
    
    for well_id in well_id_list:
        # In string1's folder
        well_id_folder_1 = os.path.join(string1_folder, well_id)
        print("Generating well_id_folder: " + well_id_folder_1)
        os.mkdir(well_id_folder_1)

        # In string2's folder
        well_id_folder_2 = os.path.join(string2_folder, well_id)
        print("Generating well_id_folder: " + well_id_folder_2)
        os.mkdir(well_id_folder_2)


    # Organize each of the tif files
    for tif_file in file_list:

        tif_filename_w_ext = os.path.basename(tif_file)
        print("organize_files Organizing " + tif_file + "...")
        wellid_from_filename = extract_well_id(tif_filename_w_ext)

        # Test this new structure
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
            error_list.append((tif_file, reason))
            moved_copied_list.append((tif_file, dest))
        
        # ERROR if the wellID  is found but does not exist in the well_id_list (possibly chosen 96-well organize_mode instead of 384-well)
        elif wellid_from_filename is not None and wellid_from_filename not in well_id_list:
            raise customError("ERROR: wellid_from_filename is not in well_id_list, wellid_from_filename: " + wellid_from_filename)

        # ERROR if both strings exists in the source tif filename
        elif string1 in tif_filename_w_ext and string2 in tif_filename_w_ext:
            reason = "Reason: both string1: " + string1 + " nor string2: " + string2 + " in tif filename"
            dest = send_to_error_folder(move_copy, tif_file, tif_filename_w_ext, reason, error_folder)
            error_list.append((tif_file, reason))
            moved_copied_list.append((tif_file, dest))

        # ERROR if neither string exists in the source tif filename
        elif string1 not in tif_filename_w_ext and string2 not in tif_filename_w_ext:
            reason = "Reason: neither string1: " + string1 + " nor string2: " + string2 + " in tif filename"
            dest = send_to_error_folder(move_copy, tif_file, tif_filename_w_ext, reason, error_folder)
            error_list.append((tif_file, reason))
            moved_copied_list.append((tif_file, dest))


    file_list.remove(tif_file)
    return moved_copied_list, error_list


# Concurrent autothresholding functions, just call process_images_parallel with params
def threshold_and_save_images(threshold_setting, tif_file):
    # Open the file
    #IJ.open(tif_file)
    #imp = IJ.getImage()
    imp = IJ.openImage(tif_file)

    IJ.run(imp, "8-bit", "")
    IJ.setAutoThreshold(imp, threshold_setting)
    IJ.run(imp, "Convert to Mask", "")

    tif_filename_w_ext = os.path.basename(tif_file)
    tif_filename_wo_ext = os.path.splitext(tif_filename_w_ext)[0]
    tif_basedir = os.path.dirname(tif_file)
    
    # Determine and save the file to the output path
    output_path = os.path.join(tif_basedir, tif_filename_wo_ext  + "_auto-thresholded.tif")
    IJ.saveAs(imp, "Tiff", output_path)
    imp.close()
    #print("Saved thresholded image to " + output_path)

def worker():
    while True:
        item = q.get()
        if item is None:
            # No more items to process
            break
        threshold_setting, tif_file = item
        threshold_and_save_images(threshold_setting, tif_file)
        q.task_done()
        print("\nThread {} completed processing {}".format(threading.current_thread().name, os.path.basename(tif_file)))

def process_images_parallel(tif_list, threshold_setting, max_threads=8):
    # Create a queue to hold tasks
    global q
    q = Queue.Queue()

    # Start worker threads
    threads = []
    for i in range(max_threads):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    # Enqueue tasks
    for tif_file in tif_list:
        q.put((threshold_setting, tif_file))

    # Block until all tasks are done
    q.join()

    # Stop workers
    for i in range(max_threads):
        q.put(None)
    for t in threads:
        t.join()



def organize_script():
        # ______________________________________________________________________________________FILE ORGANIZATION
    #***************************************************************************************
    
    # Make empty filelist so that it can be assigned if files are organized
    # Filelist will otherwise default to the tif files in the user-selected directory (dir)
    organized_tif_filelist = []

    # Get the organization settings from user
    result = get_organization_settings()
    if result == "cancelled":
        print("User cancelled get_organization_settings, exiting...")
        exit()
    else:
        organize_mode, move_copy, string1, string2, generate_log = result


    # Get the directory containing all the tif files from user
    dir = IJ.getDirectory("ORGANIZE FILES: Select a directory containing .tif files to organize")
    if dir == None:
        print("User cancelled getDirectory, exiting...")
        exit()


    if organize_mode != "Don't Organize":
        # Organize the files and return the list of errors
        moved_copied_files, errored_files = organize_files(organize_mode, move_copy, string1, string2, dir)

        # Print out all the files that have been moved/copied
        for source, dest in moved_copied_files:
            print("Source: " + source + ", Destination: " + str(dest))
        print(len(moved_copied_files))

        # Print out all the files that have met error conditions
        for file, reason in errored_files:
            print("Source: " + file + ", " + reason)
        print(len(errored_files))

        # Return the list of files to iterate through if the files have been organized
        organized_tif_filelist = [dest for source, dest in moved_copied_files]

        if generate_log is True:
            log_fp = os.path.join(os.path.dirname(os.getcwd()), "organization_log.txt")
            print("Generated log file: " + log_fp)

            with open(log_fp, "w") as log:
                log.write("******FILES " + move_copy.upper() + "******\n")
                for source, dest in moved_copied_files:
                    log.write(str(source) + " to " + str(dest) + "\n")

                log.write("\n\n******ERRORS******\n")
                for file, reason in errored_files:
                    log.write(str(file) + " errored, " + str(reason) + "\n")


    if len(organized_tif_filelist) > 0:
        # Get the organized list of tif files
        filelist = organized_tif_filelist
    else:
        # Get the list of tif files to iterate through
        filelist = (find_tif_files(dir))
    
    return filelist

def threshold_script():
    # ______________________________________________________________________________________GET THRESHOLD SETTINGS
    #***************************************************************************************

    user_thresholding_settings = get_thresholding_settings()
    if user_thresholding_settings == "cancelled":
        print("User cancelled get_thresholding_settings, exiting...")
        exit()
    else:
        threshold_setting, save_thresholded_images, individual_threshold_settings = user_thresholding_settings

    # Get the directory containing all the tif files from user
    dir = IJ.getDirectory("THRESHOLD IMAGES: Select a directory containing .tif files to auto-threshold")
    if dir == None:
        print("User cancelled getDirectory, exiting...")
        exit()


    filelist = (find_tif_files(dir))

    # ______________________________________________________________________________________THRESHOLD IMAGES AND SAVE
    #***************************************************************************************

    if save_thresholded_images == True:
        thresholded_files = []
        error_list = []
        for index, tif_file in enumerate(filelist):
            
            # # COMMENTED OUT BECAUSE REDUNDANT, USE ONLY FOR DEBUGGING
            # # Validate the file as existing and quit if not
            # if not os.path.isfile(tif_file):
            #     print("ERROR: " + tif_file + " could not be found/does not exist")
            #     error_list.append(tif_file, "Reason: tif_file could not be found/does not exist")
            #     exit()

            # Acknowledge initialization
            print("\nThresholding " + str(tif_file) + "... " + str(index + 1) + "/" + str(len(filelist)))

            # Generate inputs/outputs
            tif_filename_w_ext = os.path.basename(tif_file)
            tif_filename_wo_ext = os.path.splitext(tif_filename_w_ext)[0]
            tif_basedir = os.path.dirname(tif_file)

            # Open the file
            IJ.open(tif_file)
            imp = IJ.getImage()

            # Convert the image to 8-bit
            IJ.run(imp, "8-bit", "")

            # Add the settings and run thresholding
            #threshold_mode = individual_threshold_settings[0] # May need this for thresholding run later? CURRENTLY UNUSED
            IJ.setAutoThreshold(imp, threshold_setting)
            IJ.run(imp, "Convert to Mask", "")
            
            # Determine and save the file to the output path
            output_path = os.path.join(tif_basedir, tif_filename_wo_ext  + "_auto-thresholded.tif")
            IJ.saveAs(imp, "Tiff", output_path)
            print("Saved thresholded image to " + output_path)

            # Close out the image
            imp.close()

            # Validate that the file has been saved and errror if it has not
            if not os.path.isfile(output_path):
                print("ERROR: Could not find saved thresholded image file " + tif_file)
                error_list.append(tif_file, "Reason: Could not find saved thresholded image file at: " + output_path)
                exit()

            thresholded_files.append(output_path)


    filelist = get_autothresholded_tifs(dir)

    return threshold_setting, filelist

def analyze_script(threshold_setting):

    # ______________________________________________________________________________________GET PARTICLE ANALYSIS SETTINGS
    #***************************************************************************************

    particle_analysis_settings = get_particle_analysis_settings()
    if particle_analysis_settings == "cancelled":
        print("User cancelled get_particle_analysis_settings")
        exit()
    else:
        size_min, size_max, include_holes_checked, merge_mode = particle_analysis_settings


    output_csv_list = []
    # Errors should be appended to this array as (errored file, reason)
    error_list = []


    # Get the directory containing all the tif files from user (RESELECT)
    dir = IJ.getDirectory("ANALYSE PARTICLES: Select a directory containing .tif files to analyze particles")
    if dir == None:
        print("User cancelled getDirectory, exiting...")
        exit()

    # Would you like to use previously auto-thresholded tif files? with _auto-thresholded
    choice = get_thresholded_or_not_choice()
    if choice == True:
        filelist = get_autothresholded_tifs(dir)
        threshold_confirm = True
    else:
        filelist = (find_tif_files(dir))
        threshold_confirm = False


    for index, tif_file in enumerate(filelist):

        # Validate the file as existing and quit if not
        if not os.path.isfile(tif_file):
            print("ERROR: " + tif_file + " could not be found/does not exist")
            error_list.append(tif_file, "Reason: tif_file could not be found/does not exist")
            exit()

        # Acknowledge initialization
        print("\nProcessing " + str(tif_file) + "..." + str(index + 1) + "/" + str(len(filelist)))

        # Generate inputs/outputs
        tif_filename_w_ext = os.path.basename(tif_file)
        tif_filename_wo_ext = os.path.splitext(tif_filename_w_ext)[0]
        tif_basedir = os.path.dirname(tif_file)
        output_csv = (tif_basedir + "\\" + tif_filename_wo_ext + ".csv")

        # Open the image
        IJ.open(tif_file)
        imp = IJ.getImage()

        # If the thresholding has not been performed, autothreshold before continuing
        if threshold_confirm == False:

            # Convert the image to 8-bit
            IJ.run(imp, "8-bit", "")

            # Add the settings and run thresholding
            #threshold_mode = individual_threshold_settings[0] # May need this for thresholding run later? CURRENTLY UNUSED
            IJ.setAutoThreshold(imp, threshold_setting)
            IJ.run(imp, "Convert to Mask", "")


        # ______________________________________________________________________________________ANALYZE PARTICLES
        #***************************************************************************************
            
        # Filter any tifs that are not a single image by setting the file size.
        file_stats = os.stat(tif_file)
        #print(file_stats.st_size)
        if check_if_stack(imp, tif_file):
            print(tif_filename_w_ext + " is a stack, skipping...")
            error_list.append(tif_file, "Reason: tif_file is a stack and was skipped")
            continue


        # Run the Analyze Particles Program
        # IJ.open(tif_file)
        # imp = IJ.getImage()
        analyze_particles_parameters = "size=" + size_min + "-" + size_max + " pixel show=Overlay display clear"

        # Pass the include holes option into the analysis parameters
        if include_holes_checked:
            analyze_particles_parameters = analyze_particles_parameters + " include"

        # Run the analysis and save the results
        IJ.run(imp, "Analyze Particles...", analyze_particles_parameters)
        IJ.saveAs("Results", output_csv)

        if os.path.isfile(output_csv):
            print("Completed " + tif_filename_w_ext + " Output CSV:" + output_csv + "")
            output_csv_list.append(output_csv)
        else:
            print("Process ran, but did not produce output CSV for " + tif_filename_wo_ext)

        print("Particle Analysis completed for " + tif_filename_w_ext + "!")

        imp.close()

    # for item in error_list:
    #     print(item)
    return error_list, output_csv_list, size_min, size_max, include_holes_checked, merge_mode







# filelist = organize_script()
# threshold_setting, filelist = threshold_script()
# error_list, output_csv_list, size_min, size_max, include_holes_checked, merge_mode = analyze_script()

# ______________________________________________________________________________________USER INITIAL CHOICE: ORGANIZE BEFORE ANALYSIS
#***************************************************************************************

# while True:
    initial_action = get_organize_analyze_option()
    if initial_action == "cancelled":
        print("User cancelled get_organize_analyze_option, exiting...")
        exit()
    elif initial_action.lower() == "organize files":
        filelist = organize_script()

    elif initial_action.lower() == "auto-threshold":
        threshold_setting, filelist = threshold_script()

    elif initial_action.lower() == "analyze particles":
        error_list, output_csv_list, size_min, size_max, include_holes_checked, merge_mode = analyze_script()

    elif initial_action.lower() == "merge csvs":
        print("MERGE CSV TIME LFGGGGGG")








"""
make a list dropdown-style UI

Dialog 1
    message: choose the order in which you would like to perform your analysis. each option may only be selected once.

    First action: organize files/auto-threshold/analyze particles/merge csvs/none
    Second action: organize files/auto-threshold/analyze particles/merge csvs/none
    Third action: organize files/auto-threshold/analyze particles/merge csvs/none
    Fourth action: organize files/auto-threshold/analyze particles/merge csvs/none

Dialog 2
    message: choose the directory the tif files will be processed from:

*Script runs as ordered*

1. import all the images
2. filter to see if all are stacks (must be done despite each process) using check_if_stack()
3. pass on filtered files to the first choice function
4. pass on processed files to the second choice function
5. pass on processed files to the third choice function


"""














# ______________________________________________________________________________________CSV OUTPUT PATH
#***************************************************************************************



get_csv_files_to_merge()


# Prompt user to enter filepath for merged output
open_dialog = OpenDialog("Save output CSV file")

if open_dialog.getPath() is not None:
    selected_file_path = open_dialog.getPath()
    selected_file_path = selected_file_path + ".csv"
    merged_csv_output_fp = selected_file_path
    print("User-selected CSV output path:", selected_file_path)

else:
    # User canceled the dialog
    print("Merge cancelled by user, exiting script...")
    exit()



# ______________________________________________________________________________________RUN MERGE SCRIPT EXTERNALLY
#***************************************************************************************

script_path = get_script_path()

script_dir = os.path.dirname(script_path)
script_file_list = list_files(script_dir)
print("Current script_path: " + script_path)

if "CSV_Merger.py" not in script_file_list:

    print("ERROR: Could not find CSV Merge script, prompting user...")

    # Prompt user to find the merge script
    open_dialog = OpenDialog("Select filepath for CSV_Merger.py")
    if open_dialog.getPath() is not None:
        csv_merger_script_fp = open_dialog.getPath()
    else:
        print("Failed to find CSV_Merger.py. Exiting program without merging CSVs.")
        exit()

elif "CSV_Merger.py" in script_file_list:
    for file in script_file_list:
        if "CSV_Merger.py" in file:
            print("Found CSV_Merger.py: " + file)
            csv_merger_script_fp = os.path.join(script_dir, file)
            break
    if not os.path.isfile(csv_merger_script_fp):
        print("ERROR: Could not auto-find csv_merger_script_fp: " + csv_merger_script_fp)

print("csv_merger_script_fp: " + csv_merger_script_fp)


print("\nExecuting merge script...")
csv_list_argument = ",".join(output_csv_list)
if csv_list_argument.startswith(","):
    csv_list_argument = csv_list_argument[1:]
if csv_list_argument.endswith(","):
    csv_list_argument = csv_list_argument[:-1]

# # Put the arguments in quotes so any spaces in the filepaths will not confuse argparse
csv_merger_script_fp = "\"" + csv_merger_script_fp + "\""
csv_list_argument =  "\"" + csv_list_argument + "\""
merged_csv_output_fp =  "\"" + merged_csv_output_fp + "\""
command = "python " + csv_merger_script_fp + " --outputPath " + merged_csv_output_fp + " --CSVlist " + str(csv_list_argument) + " --mergeMode " + merge_mode


print(csv_merger_script_fp)
print(csv_list_argument)
print(merged_csv_output_fp)
print(command)

output_message = subprocess.check_output(command)
print(output_message)
print("Completed")