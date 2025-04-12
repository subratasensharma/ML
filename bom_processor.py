def process_images(input_folder, model_path=None):
    """
    Main function to process drawings and extract BOMs
    
    Args:
        input_folder (str): Path to folder containing drawings
        model_path (str, optional): Path to the YOLO model
    
    Returns:
        tuple: (cropped_folder_path, output_excel_path, no_bom_file_path)
    """
    import numpy as np
    import pandas as pd
    import cv2
    import os
    import re
    import ultralytics
    from pdf2image import convert_from_path

    from PIL import Image
    import pytesseract

    from ultralytics import YOLO
    import difflib # for fuzzy logic for closest match between strings
    from fuzzywuzzy import fuzz
    from openpyxl import load_workbook
    from openpyxl.styles import Alignment

    from bom_generator import extract_bom_jpg
    from bom_generator import extract_bom_pdf
    from bom_generator import all_boxes
    from bom_generator import filter_arrays
    from bom_generator import text_lhs_boxes
    from bom_generator import process_table
    from bom_generator import header_and_item
    from bom_generator import clean_column_name
    from bom_generator import standardize_headers
    from bom_generator import is_quantity_term
    from bom_generator import standardize_term_qty
    from bom_generator import is_material_term
    from bom_generator import standardize_term_material
    from bom_generator import is_item_no_term
    from bom_generator import standardize_term_item_no
    from bom_generator import is_drg_no_term
    from bom_generator import standardize_term_drg_no
    from bom_generator import bom_df_rev
    
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