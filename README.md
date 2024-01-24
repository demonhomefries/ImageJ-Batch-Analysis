# ImageJ-Batch-Analysis
Batch processing script to organize and analyze images from a cell plate imager through Fiji ImageJ

# Notes:
- This script runs on Fiji ImageJ version 1.54f
- Python 3.7+ must be installed on your system as CSV_merger.py runs outside the Fiji Jython environment through the terminal with argparse.
- A run log containing the following items will be generated in the directory in which main() is being run:
    - User-chosen settings
    - File transactions (source, destination) filepaths if moved or copied
    - Errors encountered during the run

# Dependencies:
 - Pandas (will be installed upon running CSV_merger.py for the first time if not already present). This script was tested using Pandas 2.1.2

# Installation:
Clone or download this repository. That's it.
Use Pip to install Pandas (optional, see Notes above)

# Usage:
Open or drag Cell_plate_image_analysis.py into the Fiji ImageJ window and click Run.
The main settings UI dialog will appear and guide you through the settings and
Please test the settings individually for an understanding of their purpose before using this tool.