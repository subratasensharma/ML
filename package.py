
#!/usr/bin/env python3
import difflib
import sys
import os
import tkinter as tk
from tkinter import filedialog
import threading
import pandas as pd
import cv2
import re
from pdf2image import convert_from_path
import numpy as np
import pytesseract

from ultralytics import YOLO
from openpyxl import load_workbook
from openpyxl.styles import Alignment
import fuzzywuzzy.fuzz as fuzz

# from bom_generator import extract_bom_jpg
# from bom_generator import extract_bom_pdf
# from bom_generator import standardize_headers
# from bom_generator import bom_df_rev


def extract_bom_jpg(drg_folder):

    ## For log suppression :
    import sys
    import contextlib

    @contextlib.contextmanager
    def suppress_output():
        with open(os.devnull, 'w') as devnull:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = devnull
            sys.stderr = devnull
            try:
                yield
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

    # Load the trained YOLOv8 model
    #model = YOLO("runs/detect/train9/weights/best.pt")
    model = YOLO("/Users/subrata/Desktop/my_bom_extractor/my_yolo_model_1.pt")

    # Input Path to drawing folder (containing drawing images in .jpg)
    drawing_folder = drg_folder + '/'

    # Output Folder inside same drawing folder to save cropped images
    output_folder = drg_folder + "/cropped_bom_jpg/"
    os.makedirs(output_folder, exist_ok=True)  # Create folder if not exists

    # List of drawing images where 'bom' could not be detected
    no_bom_drgs = []

    # Process each image in the test folder
    for filename in os.listdir(drawing_folder):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):  # Check for image files
            drawing_image = os.path.join(drawing_folder, filename)

            # Run YOLO inference
            with suppress_output():
                results = model(drawing_image, conf=0.5, verbose = False)  ## Run YOLO INFERENCE
            x1 = 0
            y1 = 0
            x2 = 0
            y2 = 0
            crop_count = 0

            # Load the image using OpenCV
            image = cv2.imread(drawing_image)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB

            # Extract filename (without extension)
            image_name = os.path.splitext(filename)[0]

            # Process detection results
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
                    class_id = int(box.cls[0])  # Class index
                    confidence = float(box.conf[0])  # Confidence score

                    # Crop the detected object
                    cropped_obj = image[y1:(y2+10), x1:(x2+10)] # To increase cropped image size at right and bottom by 10 pixels

                    # Save the cropped image
                    cropped_filename_original = f"{output_folder}/{image_name}_crop_{crop_count}.jpg"
                    
                    cropped_filename = re.sub(r'_crop_\d+', '', cropped_filename_original)

                    cv2.imwrite(cropped_filename_original, cv2.cvtColor(cropped_obj, cv2.COLOR_RGB2BGR))  # Convert RGB to BGR for saving
                    crop_count += 1

            # If no 'bom' is detected, add the image to the list
            if x1 == 0:
                
                no_bom_drgs.append(filename)
                print(f"No 'bom' detected in {filename}.")

    # Save the list of 'no bom' images to a text file inside the same drawing folder :
    no_bom_file = drg_folder + "/no_bom_jpg.txt"
    with open(no_bom_file, "w") as f:
        for img in no_bom_drgs:
            f.write(img + "\n")

    #print(f"\n📂 List of 'no bom' images saved to {no_bom_file}")
    #print(f"📂 Cropped images saved in {output_folder}")

    return output_folder, no_bom_file

def extract_bom_pdf(drg_folder):

    ## For log suppression :
    import sys
    import contextlib

    @contextlib.contextmanager
    def suppress_output():
        with open(os.devnull, 'w') as devnull:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = devnull
            sys.stderr = devnull
            try:
                yield
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

    ## Load the trained YOLOv8 model
    model = YOLO("/Users/subrata/Desktop/my_bom_extractor/my_yolo_model_1.pt")

    # Input Path to drawing folder (containing drawing images in .pdf)
    drawing_folder = drg_folder + '/'
    output_folder = drg_folder + "/cropped_bom_jpg/"  # Folder to save cropped images
    os.makedirs(output_folder, exist_ok=True)  # Create folder if not exists

    # List of PDF drawings where 'bom' could not be detected
    no_bom_drgs = []

    # Process each PDF in the test folder
    
    for filename in os.listdir(drawing_folder):
        if filename.lower().endswith(".pdf"):  # Check for PDF files
            pdf_path = os.path.join(drawing_folder, filename)

            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)  # Higher DPI for better OCR and detection

            pdf_has_bom = False  # Flag to track if BOM is detected in any page

            # Process each page
            for page_num, image in enumerate(images):
                # Convert PIL image to OpenCV format
                image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

                # Run YOLO inference
                with suppress_output():
                    results = model(image_cv, conf=0.5, verbose = False) # run YOLO inference

                x1, y1, x2, y2 = 0, 0, 0, 0
                crop_count = 0

                # Process detection results
                for result in results:
                    for box in result.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
                        class_id = int(box.cls[0])  # Class index
                        confidence = float(box.conf[0])  # Confidence score

                        # Crop the detected object
                        cropped_obj = image_cv[y1:(y2+10), x1:(x2+10)] # To increase cropped image size at right and bottom by 10 pixels

                        # Save the cropped image
                        cropped_filename = f"{output_folder}/{os.path.splitext(filename)[0]}_crop_{crop_count}.jpg"
                        cv2.imwrite(cropped_filename, cropped_obj)  # Save as BGR format
                        crop_count += 1
                        pdf_has_bom = True  # Mark that BOM was found

            # If no BOM was detected in any page, add to the list
            if not pdf_has_bom:
                
                no_bom_drgs.append(filename)
                #print(f"No 'bom' detected in {filename}.")

    # Save the list of PDFs with no BOM detected
    no_bom_file = drg_folder + "/no_bom_jpg.txt"
    with open(no_bom_file, "w") as f:
        for pdf in no_bom_drgs:
            f.write(pdf + "\n")

    return output_folder, no_bom_file

## Function to standardize column names using difflib
def clean_column_name(col):
    """Standardizes column names by removing special characters and extra spaces"""
    return re.sub(r'\W+', '', col).strip().upper()  # Remove non-alphanumeric characters and convert to uppercase. This does not

def standardize_headers(df, reference_headers):
    """Matches dataframe column names to reference headers"""
    # Preprocess reference headers
    clean_ref_headers = {clean_column_name(h): h for h in reference_headers}  # Dictionary to map cleaned -> original headers
    
    standardized_cols = {}
    for col in df.columns:
        clean_col = clean_column_name(col)  # Clean current column name
        if clean_col in clean_ref_headers:
            standardized_cols[col] = clean_ref_headers[clean_col]  # Exact match found
        else:
            # Use difflib to find the closest match
            matches = difflib.get_close_matches(clean_col, clean_ref_headers.keys(), n=1, cutoff=0.6)
            standardized_cols[col] = clean_ref_headers[matches[0]] if matches else col  # Assign closest match or keep original

    return df.rename(columns=standardized_cols)

def all_boxes(pred_bom):
    
    boxes_list = []
    
    pred_bom_gray = cv2.cvtColor(pred_bom, cv2.COLOR_BGR2GRAY)

    ##thresholding the image to a binary image
    thresh,img_bin = cv2.threshold(pred_bom_gray,0,255,cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    #inverting the image 
    img_bin_invert = 255-img_bin
      
    # Length(width) of kernel as 100th of total width
    # kernel_len = pred_bom_gray.shape[1]//100
    # added on 19/3/2025
    kernel_len = 25

    ## Defining a vertical kernel to detect all vertical lines of image 
    ver_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_len))

    # Defining a horizontal kernel to detect all horizontal lines of image
    hor_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))

    #Use vertical kernel to detect and save the vertical lines in a jpg
    image_1 = cv2.erode(img_bin_invert, ver_kernel, iterations=3)
    vertical_lines = cv2.dilate(image_1, ver_kernel, iterations=3)

    #Use horizontal kernel to detect and save the horizontal lines in a jpg
    image_2 = cv2.erode(img_bin_invert, hor_kernel, iterations=3)
    horizontal_lines = cv2.dilate(image_2, hor_kernel, iterations=3)
    
    # Combine horizontal and vertical lines in a new third image, with both having same weight.
    img_vh = cv2.addWeighted(vertical_lines, 0.5, horizontal_lines, 0.5, 0.0)
    
    # A kernel of 2x2
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    img_vh_d = cv2.dilate(img_vh, kernel, iterations=2)

    # Defining the cell boxes
    contours, hierarchy = cv2.findContours(img_vh_d, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    boxes = np.zeros((len(contours), 4))

    for i in range(len(contours)):
    
        cnt = contours[i]
        x, y, w, h = cv2.boundingRect(cnt)
        boxes[i, 0] = x
        boxes[i, 1] = y
        boxes[i, 2] = w
        boxes[i, 3] = h

    boxes_list.append(boxes)
    
    return boxes_list, img_vh, img_vh_d   ## in format x, y, w, h. and boxes list is the list of horizontal lines in between 
                                            ## all vertical lines.

## Process LHS table boxes and find key information.
def text_lhs_boxes(bom_boxes, pred_bom):
    """
    Process LHS table boxes and find key information.

    :param boxes_list: List of (x, y, w, h) for each box.
    :return: Tuple (x, y, w, h) if '1' or '2' found, "Alphanumeric" if all are alphanumeric, else None.
    """
    lhs_text_list = []

    # Clean the bom_boxes for y = 0 and same y value >= 3
    boxes_1 = filter_arrays(bom_boxes)  
    boxes = sorted(boxes_1[0], key=lambda b: (b[1], b[0])) # boxes are sorted - reverse the bom_boxes
    #print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
    #print('filtered_boxes = ', boxes)
    # Convert list of arrays into a NumPy array
    boxes_np = np.array(boxes)

    # Step 1: Find the minimum x-value, excluding y=0
    min_x = np.min(boxes_np[:, 0])  # Get minimum x

    # Step 2: Get all boxes with this min_x value
    lhs_boxes = boxes_np[boxes_np[:, 0] == min_x]
    lhs_boxes_list = lhs_boxes.tolist()

    for box in lhs_boxes:
        
        x, y, w, h = map(int, box)  # Convert to int
        #print('===============================')
        #print(x, y, w, h)
        x_c = x + 2
        y_c = y + 2
        w_c = w - 4
        h_c = h - 4
        pred_bom_gray = cv2.cvtColor(pred_bom, cv2.COLOR_BGR2GRAY)
        roi = pred_bom_gray[y_c:y_c+h_c, x_c:x_c+w_c]  # Crop the region - increase of x,y and reduction of w,h is very 
        #important for text accuracy
        sharp_kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
        roi_sharp = cv2.filter2D(roi, -1, sharp_kernel)
        _, cell_bin = cv2.threshold(roi_sharp, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        text = pytesseract.image_to_string(cell_bin, config='--psm 6 --oem 3').strip()  # OCR
        lhs_text_list.append(text)

    return lhs_text_list, lhs_boxes_list

def filter_arrays(array_list):
    filtered_list = []  # List to store filtered arrays

    for arr in array_list:
        # Ensure the array is not empty
        if arr.size == 0:
            continue

        # Step 1: Identify y-values appearing at least 3 times
        y_values = arr[:, 1]
        unique_y, counts = np.unique(y_values, return_counts=True)

        # Keep only y-values appearing at least 3 times
        valid_y_values = {y for y, c in zip(unique_y, counts) if c >= 3}

        # Filter rows with these valid y-values
        filtered_arr = np.array([row for row in arr if row[1] in valid_y_values])

        # Step 2: Find the last occurrence of y = 0
        if filtered_arr.size > 0:
            last_zero_index = np.where(filtered_arr[:, 1] == 0)[0]
            if last_zero_index.size > 0:
                last_zero_index = last_zero_index[-1]  # Last occurrence index
                filtered_arr = filtered_arr[last_zero_index + 1:]  # Keep rows after

        # Add to the final list only if it's non-empty
        if filtered_arr.size > 0:
            filtered_list.append(filtered_arr)  # Corrected the append operation

    return filtered_list  # Return the list of filtered arrays

def process_table(pred_bom_id, pred_bom, lhs_box_list, lhs_text_list):
    """
    Process and draw necessary horizontal and vertical lines based on table box coordinates.
    
    Parameters:
    - image: Input image (BGR).
    - lines: Output of cv2.HoughLinesP.
    - box: Tuple (x, y, w, h) of one table cell.
    """
    def filter_lines(lines, orientation='horizontal', angle_threshold=5):
        filtered = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if orientation == 'horizontal' and abs(y2 - y1) <= angle_threshold:
                filtered.append((x1, y1, x2, y2))
            elif orientation == 'vertical' and abs(x2 - x1) <= angle_threshold:
                filtered.append((x1, y1, x2, y2))
        return filtered

    def get_longest_and_second_longest(lines, image_dim, is_horizontal=True):
        if not lines:
            return None, None
        lines_sorted = sorted(lines, key=lambda l: np.hypot(l[2] - l[0], l[3] - l[1]), reverse=True)
        longest = lines_sorted[0]
        span = abs(longest[2] - longest[0]) if is_horizontal else abs(longest[3] - longest[1])
        full_span = image_dim[0] if is_horizontal else image_dim[1]

        if span >= full_span - 2:  # Allow slight tolerance
            second_longest = lines_sorted[1] if len(lines_sorted) > 1 else None
            return longest, second_longest
        return longest, None

def header_and_item(pred_bom_id, pred_bom_corrected):
    
    bom_boxes_first,_,_ = all_boxes(pred_bom_corrected)
    bom_boxes = filter_arrays(bom_boxes_first)

    for i in range(len(bom_boxes)):   # for single bom drawings, len(bom_boxes) is always 1

        if i == 0:
            col_count_list = []
            header_boxes_list = []
            bom_boxes_list = []
            item_index_width_list = []

        boxes_1 = bom_boxes[0]
        
        ## Find number of columns i.e. max occurance of any y value :
        # Extract all y-values
        y_values = boxes_1[:, 1]
        y_list = y_values.tolist()
        #print('y_list = ', y_list)
        # Count occurrences from the top until a repeat is detected
        y_bmrm_cell = boxes_1[0][1]
        num_col = y_list.count(y_bmrm_cell)   ## no. of occurances of y_bmrm_cell value i.e.1st bottom most cell

        # Find max number of occurrences of any y-value
        col_count_array = np.bincount(np.array(y_list, dtype=int)) # modified by chat_gpt on 10/4/15
        # col_count_array = np.bincount(y_list)  ## no. of occurances of each y-value
        col_count_y = col_count_array.max()  ## max. no. of occurances of any one y-value

        #print('================================================================')
        #print('y_list_header = ', num_col)
        #print('y_list = ', col_count_y)
        #print('================================================================')
    
        if num_col != col_count_y :
            print('*** header columns are not equal to bom columns and hence BOM not created ***')

            # If no modifications were made, put the drawing in 'no_bom' file :
            base_filename = os.path.splitext(os.path.basename(pred_bom_id))[0]
            # Split the base filename and take the first part (before '_crop')
            pdf_base = base_filename.split('_crop')[0]
            # Return the PDF filename
            drg_file_name =  f"{pdf_base}.pdf"

            # Get the directory of the input file
            input_dir = os.path.dirname(pred_bom_id)
    
            # Go up one directory level
            parent_dir = os.path.dirname(input_dir)
    
            # Create the output file path
            output_file = os.path.join(parent_dir, "no_bom_jpg.txt")
    
            
            with open(output_file, "a") as f:
                f.write(drg_file_name + "\n")     

            return None, None, None, None

        # Now find the Header row :

        # In drawings, header row is always at the bottom.
        # Output of cv2.boundingRect always starts with the box of complete BOM
        # After this 1st row, the output starts with the bottom_most_right_most (in this order) box details.

        # So, y value of boxes[1] is the bottom_most-right_most (in this order) cell y value.

        y_bmrm_cell = boxes_1[0][1]  # y value of 1st bottom most cell

        # If occurances of this y value of 1st bottom most cell = number of columns, then this is the y value of Header Row

        num_col = y_list.count(y_bmrm_cell)   ## no. of occurances of y_bmrm_cell value i.e.1st bottom most cell

        if num_col == col_count_y:
    
            y_header_row = y_bmrm_cell
            item_index_width = boxes_1[col_count_y-1, 2]  # This is the width of the 1st column i.e. 'Item No.' column
            bom_boxes_1 = boxes_1[1:]   ## remove 1st header row for bom consideration
    
        else:
        
            y_next_cell = boxes_1[1][1]

            num_col = y_list.count(y_next_cell)

            if num_col == col_count_y:
    
                y_header_row = y_next_cell
                item_index_width = boxes_1[col_count_y, 2]
                bom_boxes_1 = boxes_1[2:]    ## remove 1st 2 rows for bom consideration

        header_boxes = boxes_1[boxes_1[:, 1] == y_header_row] 
    
        bom_boxes = bom_boxes_1[bom_boxes_1[:, 1] != y_header_row]
        
        col_count_list.append(col_count_y)
        item_index_width_list.append(item_index_width)
        header_boxes_list.append(header_boxes)
        bom_boxes_list.append(bom_boxes)
        
    return col_count_list, item_index_width_list, header_boxes_list, bom_boxes_list  ## all boxes in x, y, w, h format

def standardize_term_qty(term, threshold=65):
    if is_quantity_term(term, threshold):
        return 'qty', True  # Return the standardized term and a flag indicating it's a quantity term
    else:
        return term, False  # Return the original term and a flag indicating it's not

def is_quantity_term(term, threshold=65):
    quantity_variants = ['qty.', 'qty', 'no off', 'number of', 'ary']
    scores = [fuzz.ratio(term.lower(), variant) for variant in quantity_variants]
    return max(scores) > threshold

def is_material_term(term, threshold=65):
    quantity_variants = ['mat', 'material', 'spec', 'specification', 'make', 'matl/make']
    scores = [fuzz.ratio(term.lower(), variant) for variant in quantity_variants]
    return max(scores) > threshold

def standardize_term_material(term, threshold=65):
    if is_material_term(term, threshold):
        return 'material', True  # Return the standardized term and a flag indicating it's a quantity term
    else:
        return term, False  # Return the original term and a flag indicating it's not

def is_item_no_term(term, threshold=65):
    quantity_variants = ['item', 'item.no', 'sl.no.', 'item sl.']
    scores = [fuzz.ratio(term.lower(), variant) for variant in quantity_variants]
    return max(scores) > threshold

def standardize_term_item_no(term, threshold=65):
    if is_item_no_term(term, threshold):
        return 'item_no', True  # Return the standardized term and a flag indicating it's a quantity term
    else:
        return term, False  # Return the original term and a flag indicating it's not

def is_drg_no_term(term, threshold=65):
    quantity_variants = ['drawing no.', 'drg.no.', 'drg. no./sheet no', 'drg. no/sheet no']
    scores = [fuzz.ratio(term.lower(), variant) for variant in quantity_variants]
    return max(scores) > threshold

def standardize_term_drg_no(term, threshold=65):
    if is_drg_no_term(term, threshold):
        return 'drg_no', True  # Return the standardized term and a flag indicating it's a quantity term
    else:
        return term, False  # Return the original term and a flag indicating it's not
          
## Main BOM extraction module
def bom_df_rev(pred_bom_id):

    pred_bom = cv2.imread(pred_bom_id)

    if pred_bom is None:
        print("Error: Image not found or could not be loaded.")
        return None, None, None

    boxes_list, _, _ = all_boxes(pred_bom)

    lhs_text_list, lhs_boxes_list = text_lhs_boxes(boxes_list, pred_bom)
    
    # Run function and get modified image
    
    pred_bom_corrected = process_table(pred_bom_id, pred_bom, lhs_boxes_list, lhs_text_list)
    
    if pred_bom_corrected is None:
        return None, None, None
    
    else:
        # Extract header and item details
        col_count_list, item_index_width_list, header_boxes_list, bom_boxes_list = header_and_item(pred_bom_id, pred_bom_corrected)
        
        # Ensure we have header boxes
        if not header_boxes_list or len(header_boxes_list) == 0:
            print("Error: No header boxes found!")
            return None, None, None

        # Extract header column widths
        width_list = header_boxes_list[0][:, 2]  
        x_list = header_boxes_list[0][:, 0]
    
        # Find the frequency of column widths
        width_frequency = np.unique(width_list, return_counts=True)[1]  

        # Get all column widths from BOM items
        all_width_list = bom_boxes_list[0][:, 2].tolist()
        row_count_array = np.bincount(np.array(all_width_list, dtype=int)) # modified by chat_gpt on 10/4/25
        # row_count_array = np.bincount(all_width_list)  
        row_count_apparent = row_count_array.max()
    
        # Estimate row count
        row_count = row_count_apparent // np.max(width_frequency) if np.max(width_frequency) != 0 else 0

        sharp_kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])

        # Extract header text
        header_text = []
        bom_check_width = 0
        bom_qty_check_width = 0
        for box in header_boxes_list[0]:  
            x, y, w, h = map(int, box)  # Convert to integers
        
            x_c = x + 2
            y_c = y + 2
            w_c = w - 4
            h_c = h - 4

            pred_bom_gray = cv2.cvtColor(pred_bom_corrected, cv2.COLOR_BGR2GRAY)
            roi = pred_bom_gray[y_c:y_c+h_c, x_c:x_c+w_c]  # Crop the region - increase of x,y and reduction of w,h is very 
                                                            # important for text accuracy
            # Find the first column where any pixel value < 10
            col_indices = np.where(np.any(roi < 10, axis=0))[0]  # Get all matching column indices

            if col_indices.size > 0:  # Check if any column meets the condition
                col_index = col_indices[0]  # First column where condition is met
                start_col = max(0, col_index - 3)  # Keep 3 columns before
                modified_roi = roi[:, start_col:]
                
            else:
                modified_roi = roi  # Keep the original array unchanged

            roi_sharp = cv2.filter2D(modified_roi, -1, sharp_kernel)

            text = pytesseract.image_to_string(roi_sharp, config='--psm 6 --oem 3').strip()  # OCR
            text = text.lower().rstrip('.')
            text = text.replace("\n", " ")  

            # Check if text matches any variation of 'qty'
            
            text, is_qty_check = standardize_term_qty(text, threshold=65)
            text, is_check = standardize_term_material(text, threshold=65)
            text, is_check = standardize_term_item_no(text, threshold=65)
            text, is_drg_no_check = standardize_term_drg_no(text, threshold=65)

            if is_qty_check:
                bom_qty_check_width = w  # Set the width if it's a quantity term
    
            if is_check:
                bom_check_width = w  # Set the width if it's other terms
        
            header_text.append(text)
    
        # if no 'qty' column exists :
        if bom_check_width == 0 or bom_qty_check_width == 0:
            
            # If no modifications were made, put the drawing in 'no_bom' file :
            base_filename = os.path.splitext(os.path.basename(pred_bom_id))[0]
            # Split the base filename and take the first part (before '_crop')
            pdf_base = base_filename.split('_crop')[0]
            # Return the PDF filename
            drg_file_name =  f"{pdf_base}.pdf"

            # Get the directory of the input file
            input_dir = os.path.dirname(pred_bom_id)
    
            # Go up one directory level
            parent_dir = os.path.dirname(input_dir)
    
            # Create the output file path
            output_file = os.path.join(parent_dir, "no_bom_jpg.txt")
    
        
            with open(output_file, "a") as f:
                f.write(drg_file_name + "\n")
            
            return None, None, None    

        header_text.append('drg_id')
    
        serialised_header_text = header_text[::-1]  # Reverse order
        serialised_header_text[1]= "Item_No." # Change the name of the 2nd column

        # Extract BOM items
        bom_text = []
        for i, bom_boxes in enumerate(bom_boxes_list):
            y_unique = np.unique(bom_boxes[:, 1])[::-1]  # Reverse order
        
            for j in y_unique:
                bom_sub_text = []
                aa = np.ones((col_count_list[0], 4))  
                bb = bom_boxes[bom_boxes[:, 1] == j]  # Select only rows with matching Y
            
                for k in range(len(aa)):
                    for l in range(len(bb)):
                        if abs((bb[l][2] + bb[l][0]) - (width_list[k] + x_list[k])) <= 2:
                            aa[k, :] = bb[l, :]
                
                for k in range(len(aa)):
                    x, y, w, h = map(int, aa[k])

                    if x == 1 and y == 1 and w == 1 and h == 1:
                        text = ' '  
                    else:
                        x_c = x + 2
                        y_c = y + 2
                        w_c = w - 4
                        h_c = h - 4

                        cell_crop_image = pred_bom_gray[y_c:y_c+h_c, x_c:x_c+w_c]

                        if cell_crop_image is None or cell_crop_image.size == 0:
                            print("Error: cell_crop_image is empty or not loaded correctly.")

                        cell_crop_clr = cv2.cvtColor(cell_crop_image, cv2.COLOR_RGB2BGR)
                        cell_crop_bordered = cv2.copyMakeBorder(cell_crop_clr, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=[255, 255, 255])
                        cell_crop_gray = cv2.cvtColor(cell_crop_bordered, cv2.COLOR_BGR2GRAY)


                        # Find the first column where any value < 10
                        col_indices = np.where(np.any(cell_crop_gray < 10, axis=0))[0]  # Get all matching column indices

                        if col_indices.size > 0:  # Check if any column meets the condition
                            col_index = col_indices[0]  # First column where condition is met
                            start_col = max(0, col_index - 3)  # Keep 3 columns before
                            modified_arr = cell_crop_gray[:, start_col:]
                        else:
                            modified_arr = cell_crop_gray  # Keep the original array unchanged

                        # OCR text extraction
                        
                        # Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
                        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                        cell_crop_enhanced = clahe.apply(modified_arr)
                        #_, cell_bin = cv2.threshold(cell_crop_enhanced, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
                        #text = pytesseract.image_to_string(roi, config='--psm 6').strip()  # OCR
                        text = pytesseract.image_to_string(cell_crop_enhanced, config='--psm 6 --oem 3').strip()

                        """
                        # Check if text is NOT a digit and x is the minimum x in aa
                        if not text.isdigit() and x == int(min(x_list)):
                        
                            cell_crop_sharp = cv2.filter2D(cell_crop_image, -1, sharp_kernel)
                            _, cell_bin = cv2.threshold(cell_crop_sharp, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
                            text = pytesseract.image_to_string(cell_bin, config='--psm 6 --oem 3').strip()  # OCR
                        
                        # Check if quantity text is NOT a digit in the qty column
                        if not text.isdigit() and w == bom_qty_check_width:
                        
                            cell_crop_sharp = cv2.filter2D(cell_crop_image, -1, sharp_kernel)
                            _, cell_bin = cv2.threshold(cell_crop_sharp, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
                            text = pytesseract.image_to_string(cell_bin, config='--psm 6 --oem 3').strip()  # OCR
                        """
                    
                        text = text.replace("\n", " ")  # Remove newlines within extracted text
                    
                    # OCR text extraction
                    bom_sub_text.append(text)

                original_bom_id = ((pred_bom_id.split('/'))[-1].split('.'))[0] # making bom df with only drg no. and not with drg. path
                bom_id = re.sub(r'_crop_\d+$', '', original_bom_id)  # getting rid of '_crop_....'
                bom_sub_text.append(bom_id)  # Append image ID
                bom_text.append(bom_sub_text[::-1])  # Reverse order

        # Convert to DataFrame
        expected_cols = len(header_text)  # Expected column count
        filtered_bom_text = [row for row in bom_text if len(row) == expected_cols]

        # Convert to DataFrame
        df = pd.DataFrame(filtered_bom_text, columns=serialised_header_text)

        #df = pd.DataFrame(bom_text, columns=serialised_header_text)
        return df, bom_text, bom_sub_text

def process_images(input_folder, model_path=None):
    """
    Main function to process drawings and extract BOMs
    
    Args:
        input_folder (str): Path to folder containing drawings
        model_path (str, optional): Path to the YOLO model
    
    Returns:
        tuple: (cropped_folder_path, output_excel_path, no_bom_file_path)
    """

    
    # Set the model path if provided
    if model_path:
        # Add code to load your YOLO model with the provided path
        #model = YOLO("/Users/subrata/workstation/jupyterFiles/yolo_data_file/yolov8_dir/my_yolo_model_1.pt")
        #model_path =  "/Users/subrata/Desktop/my_bom_detector/my_yolo_model_1.pt"
        model = YOLO(model_path)
    
    print("BOM images are being created ................................")
    folder_name = os.path.basename(input_folder.rstrip('/')) # this gives folder_name = project_9_pdf
    
    # Determine if folder contains JPGs or PDFs
    if folder_name.endswith(("_jpg", "_png", "_jpeg")):
        output_cropped_folder, no_bom_file = extract_bom_jpg(input_folder)
    else:
        output_cropped_folder, no_bom_file = extract_bom_pdf(input_folder)
    
    print("All BOM images created................................")
    print('Beginning BOM creation for folder = ', folder_name)
    print('............................................................')
    # List to store DataFrames
    df_list = []
    
    # Loop through all images in the folder
    for file_name in os.listdir(output_cropped_folder):
        if file_name.endswith((".jpg", ".png", ".jpeg")):
            image_path = os.path.join(output_cropped_folder, file_name)
            bom_id = ((image_path.split('/'))[-1].split('.'))[0]
            print('BOM creation started for = ', bom_id)
            
            df, _, _ = bom_df_rev(image_path)  # Call your function
            
            if df is None:
                print('**** DF is none ****')
                continue
                
            if df is not None:
                print('BOM Created for = ', bom_id)
                print('.............................................................')
                df_list.append(df)
    
    output_bom_file = None
    if df_list:
        # Take the header of the first DataFrame as the reference
        reference_headers = ['drg_id', 'Item_No.', 'description', 'size', 'material', 'qty', 'unit', 'total', 'drg_no']
        
        # Apply standardization to all DataFrames
        df_list = [df_list[0]] + [standardize_headers(df, reference_headers) for df in df_list[1:]]
        
        # Concatenate all DataFrames
        final_df = pd.concat(df_list, ignore_index=True, join='outer')
        final_df = final_df.dropna(axis=1, how="all")  # Drop completely empty columns
        
        # Create Excel file from the dataframe
        output_bom_file = os.path.join(input_folder, "bill_of_material.xlsx")
        
        # Get column indices (safely)
        column_index_drg_id = final_df.columns.get_loc('drg_id') if 'drg_id' in final_df.columns else 0
        column_index_item_no = final_df.columns.get_loc('Item_No.') if 'Item_No.' in final_df.columns else 0
        column_index_description = final_df.columns.get_loc('description') if 'description' in final_df.columns else 0
        column_index_material = final_df.columns.get_loc('material') if 'material' in final_df.columns else 0
        column_index_qty = final_df.columns.get_loc('qty') if 'qty' in final_df.columns else 0
        
        # Sort data
        sort_columns_1 = [final_df.columns[column_index_drg_id]]
        sort_columns_2 = [final_df.columns[column_index_material], final_df.columns[column_index_description]]
        final_df_sorted_1 = final_df.sort_values(by=sort_columns_1, kind='stable')
        final_df_sorted_2 = final_df.sort_values(by=sort_columns_2, ascending=True)
        
        # Write to Excel
        with pd.ExcelWriter(output_bom_file) as writer:
            final_df_sorted_1.to_excel(writer, sheet_name="Original_Data", index=False)
            final_df_sorted_2.to_excel(writer, sheet_name="Sorted_Data", index=False)
    #======================================================================================================================
    # Load the existing workbook

        wb = load_workbook(output_bom_file)

    # List of sheets to modify
        sheets_to_modify = ["Original_Data", "Sorted_Data"]

        for sheet_name in sheets_to_modify:
            if sheet_name in wb.sheetnames:  # Check if the sheet exists
                ws = wb[sheet_name]

            # Apply center alignment for all rows in the specific column
                for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=column_index_drg_id, max_col=column_index_drg_id):
                    for cell in row:
                        cell.alignment = Alignment(horizontal="center")

                for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=column_index_qty, max_col=column_index_qty):
                    for cell in row:
                        cell.alignment = Alignment(horizontal="center")

    # Save the changes
        wb.save(output_bom_file)

    else:
        print("No valid DataFrames generated.")
    #=======================================================================================================================
    print(f"\n📂 List of 'no bom' PDFs saved to file no_bom_jpg.txt")
    print("Bill of Material file saved successfully with two sheets in folder bil_of_material.xlxs") 
    
    return output_cropped_folder, output_bom_file, no_bom_file

def select_folder():
    input_folder = filedialog.askdirectory(title="Select folder")
    print('.....................................................')
    print("Selected folder:", input_folder)
    return input_folder

def run_processing(input_folder, model_path):

    # Call the actual processing
    process_images(input_folder, model_path)

def on_click():
    input_folder = select_folder()
    # Find model path near the executable or script
    model_path = os.path.join(os.path.dirname(sys.executable), 'my_yolo_model_1.pt')
    if not os.path.exists(model_path):
        model_path = os.path.join(os.path.dirname(__file__), 'my_yolo_model_1.pt')
    # Run processing in a background thread to avoid GUI freezing
    thread = threading.Thread(target=run_processing, args=(input_folder, model_path))
    thread.start()

window = tk.Tk()
window.title("Test GUI")
window.geometry("300x150")

button = tk.Button(window, text="Pick Folder", command=on_click)
button.pack(pady=30)

window.mainloop()
