import os
import time
import threading
import Queue
from ij import IJ
from ij.gui import GenericDialog


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
    
def find_tif_files(directory):
    tif_files = []

    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.tif'):
                tif_files.append(os.path.join(root, filename))

    return tif_files

def get_time_elapsed(start_time, process):
    current_time = time.time()
    time_elapsed_seconds = current_time - start_time
    time_elapsed_milliseconds = time_elapsed_seconds * 1000
    time_elapsed = "{:.2f} milliseconds".format(time_elapsed_milliseconds)

    print("Time elapsed: {} for {}".format(time_elapsed, process))
    start_time = time.time()
    return time_elapsed_milliseconds

def threshold_and_save_images_BACKUP(threshold_setting, tif_list):

    for tif_file in tif_list:

        # Open the file
        IJ.open(tif_file)
        imp = IJ.getImage()
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



settings = get_thresholding_settings()
if settings != "cancelled":
    threshold_setting, save_thresholded_images, _ = settings
else:
    print("get_thresholding_settings cancelled")
    exit()


dir = r"C:\Users\akmishra\Desktop\ImageJ_Automation_V2\test_concurrent"
filelist = find_tif_files(dir)
filelist = [file for file in filelist if "TdTomato" in file]

# CONCURRENT
start_time = time.time()
process_images_parallel(filelist, threshold_setting)
concurrent_time_elapsed = get_time_elapsed(start_time, "threshold_and_save_images CONCURRENT")


dir = r"C:\Users\akmishra\Desktop\ImageJ_Automation_V2\test_linear"
filelist = find_tif_files(dir)
filelist = [file for file in filelist if "TdTomato" in file]

# LINEAR
start_time = time.time()
for tif_file in filelist:
    threshold_and_save_images(threshold_setting, tif_file)
linear_time_elapsed = get_time_elapsed(start_time, "threshold_and_save_images LINEAR")

print("\n\nCONCURRENT TIME ELAPSED: " + concurrent_time_elapsed)
print("LINEAR TIME ELAPSED: " + linear_time_elapsed)

