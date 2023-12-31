from app import app, socketio
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, Response
from nogan_synthesizer import NoGANSynth
from nogan_synthesizer.preprocessing import wrap_category_columns, unwrap_category_columns
#from genai_evaluation import multivariate_ecdf, ks_statistic
from app.modules.genai_evaluation import multivariate_ecdf, ks_statistic
import pandas as pd
import numpy as np
import os
import random
import time
import re
import json

def validate_bins_stretch(form_element_type : str, 
                          form_element_checked : str, 
                          form_text_json: str,
                          col_len : int):
    # print(f"form_element_type: {form_element_type}")
    # print(f"form_element_checked: {form_element_checked}")
    # print(f"form_text_json: {form_text_json}")
    # print(f"col_len: {col_len}")
    
    if form_element_checked is None:
        # print(f"Form Element is null")
        if form_element_type == "bins":
            value_list = [100] * col_len
        elif form_element_type == "stretch_type":
            value_list = ["Uniform"] * col_len
        else:
            value_list = [1.0] * col_len

        return value_list, "Success"
    else:
        # print(f"Form Element is not null")
        if form_text_json:
            try:
                form_element_json = json.loads(form_text_json)
                value_list = [form_element_json[key] 
                              for key in form_element_json]
                
                if not form_element_json:
                    return None, "Error"
                
                if (form_element_type == "bins") and (min(value_list) <= 0):
                    return None, "Error"
                    
                if (form_element_type == "stretch_type") and (len(set(value_list) - app.config['STRETCH_TYPE']) > 0):
                    return None, "Error"
                  
                return value_list, "Success"
            except Exception as e:               
                return None, "Error"
        else:
            return None, "Error"
                    
def validate_data(orig_data, features, category_columns, bins_checked, 
                  bins_text, stretch_type_checked, stretch_type_text,
                  stretch_val_checked, stretch_val_text, num_nodes,
                  random_seed, ks_seed, data_dir, file_name):
    try:
        DEBUG_LOCATION="Data Validation"
        
        train_data = orig_data.sample(frac=0.5)
        val_data = orig_data.drop(train_data.index)
        
        # print("Train Data")
        # print(train_data.head())
        
        # print("Valid Data")
        # print(val_data.head())
        

        if category_columns:
            DEBUG_STEP = "wrapping Category Columns"
            train_data, idx_to_key, _ = \
                    wrap_category_columns(train_data,
                                            category_columns)                
            val_data, _ , _ = \
                    wrap_category_columns(val_data,
                                            category_columns)                               
        # Train NoGAN
        DEBUG_STEP="getting Bins"
        bins, bins_error_status = \
                validate_bins_stretch("bins",
                                      bins_checked,
                                      bins_text,
                                      len(train_data.columns))
        if bins_error_status == "Error":
            raise ValueError("Bins Error")
        
        print(f"Bins: {bins}")
                        
        DEBUG_STEP="getting Stretch Type"
                            
        stretch_type, stretch_type_error_status = \
                validate_bins_stretch("stretch_type",
                                      stretch_type_checked,
                                      stretch_type_text,
                                      len(train_data.columns))
        if stretch_type_error_status == "Error":
            raise ValueError("Stretch Type Error")
        
        print(f"Stretch Type: {stretch_type}")
        
        DEBUG_STEP="getting Stretch Values"
        stretch, stretch_error_status = \
                validate_bins_stretch("stretch",
                                      stretch_val_checked,
                                      stretch_val_text,
                                      len(train_data.columns))

        if stretch_error_status == "Error":
            raise ValueError("Stretch Values Error")  
        
        print(f"stretch val: {stretch}")
        
        DEBUG_STEP = "instantiating NoGAN Model"
        nogan = NoGANSynth(train_data,
                           random_seed=random_seed)
        
        DEBUG_STEP = "fitting NoGAN Model"
        nogan.fit(bins = bins)
        
        num_rows = len(train_data)
        
        DEBUG_STEP="generating Synthetic Data"
        synth_data = \
            nogan.generate_synthetic_data(no_of_rows = num_rows,
                                          stretch_type = stretch_type,
                                          stretch = stretch)
        
        # Calculate ECDFs & KS Stats
        DEBUG_STEP="calculating ECDF for Validation and Synthetic Data"
        for msg in multivariate_ecdf(val_data, 
                                     synth_data, 
                                     n_nodes = num_nodes,
                                     random_seed = ks_seed):
            
            #print(f"ECDF Message: {msg}")
            if msg["result_type"] == "update_progress":
                progress = f"Validation vs Synthetic - {msg['result']['progress']}"
                progress_perc = msg['result']['progress_perc']
                yield {"result_type": "update_progress", 
                       "result": {"progress": progress, 
                                  "progress_perc": progress_perc,}}
                # socketio.emit('update_progress', 
                #               {'progress': progress, 
                #                'progress_perc': progress_perc})
            else:
                ecdf_val1 = msg["result"]["ecdf_a"]
                ecdf_nogan_synth = msg["result"]["ecdf_b"]
        
        DEBUG_STEP="calculating ECDF for Validation and Training Data"

        # print(f"Val Data Shape: {val_data.shape}, Train Data Shape: {train_data.shape}")
        for msg in  multivariate_ecdf(val_data, 
                                      train_data, 
                                      n_nodes = num_nodes,
                                      random_seed = ks_seed):

            if msg["result_type"] == "update_progress":
                progress = f"Validation vs Training - {msg['result']['progress']}"
                progress_perc = msg["result"]["progress_perc"]
                yield {"result_type": "update_progress", 
                       "result": {"progress": progress, 
                                  "progress_perc": progress_perc,}}
                # socketio.emit('update_progress', 
                #               {'progress': progress, 
                #                'progress_perc': progress_perc})
            else:
                ecdf_val2 = msg["result"]["ecdf_a"]
                ecdf_train = msg["result"]["ecdf_b"]
                        
        DEBUG_STEP="calculating KS Statistic for Validation and Synthetic Data"
        ks_stat = ks_statistic(ecdf_val1, ecdf_nogan_synth)
        
        DEBUG_STEP="calculating KS Statistic for Validation and Training Data"
        base_ks_stat = ks_statistic(ecdf_val2, ecdf_train)

        # Generate a unique CSV file name
        DEBUG_STEP="generating csv file"
        if category_columns:
            DEBUG_STEP="unwrapping Category Columns"
            generated_data = \
            unwrap_category_columns(data=synth_data,
                                    idx_to_key=idx_to_key,
                                    cat_cols=category_columns)
        else:
            generated_data = synth_data                                 
        generated_data = generated_data[features]
        timestamp = int(time.time())
        csv_filename = f"result_{file_name.split('.')[0]}_{timestamp}.csv"
        generated_data.to_csv(os.path.join(data_dir, csv_filename), index=False)
        file_location = f"/download/{csv_filename}"
        
        success_message = f"<strong>KS Statistic</strong>: {ks_stat:0.4f}<br><strong>Base KS Statistic</strong>: {base_ks_stat:0.4f}<br><p><a href='{file_location}'>Download</a></p>"

        yield {"result_type": "update_message", 
               "result": {"message": success_message, 
                          "type": "success",}}
        # socketio.emit('update_message', 
        #               {'message': success_message, 'type': 'success'})
    except Exception as e:
        if DEBUG_STEP.lower() in ["getting bins", "getting stretch type", "getting stretch values"]:
            error_message = f'Error in {DEBUG_LOCATION}({DEBUG_STEP}): Please check the json format'

            if DEBUG_STEP.lower() in ["getting bins"]:
                error_message = error_message + "." + " Also Bin values should not be negative or zero"
                
            if DEBUG_STEP.lower() in ["getting stretch type"]:
                error_message = error_message + "." + f" Also Stretch type should have only {list(app.config['STRETCH_TYPE'])} entries"
                
        else:                
            error_message = f'Error in {DEBUG_LOCATION}({DEBUG_STEP}): {str(e)}'
        
        yield {"result_type": "update_message", 
               "result": {"message": error_message, 
                          "type": "error",}}
        # socketio.emit('update_message', 
        #               {'message': error_message, 'type': 'error'})
                             
def generate_data(orig_data, features, category_columns,
                  bins_checked, bins_text, stretch_type_checked,
                  stretch_type_text, stretch_val_checked,
                  stretch_val_text, ks_stat_selected, num_nodes, num_rows,
                  random_seed, ks_seed, data_dir, file_name
                  ):
    try:
        DEBUG_LOCATION = "Data Generation"
        
        print(f"Num Rows: {num_rows}")
        print(f"Category Columns: {category_columns}")  

        if category_columns:
            DEBUG_STEP = "wrapping category columns"                   
            wrapped_data, idx_to_key, _ = \
                    wrap_category_columns(orig_data,
                                          category_columns)
            orig_data = wrapped_data
            
        DEBUG_STEP="getting Bins"
        bins, bins_error_status = \
                validate_bins_stretch("bins",
                                      bins_checked,
                                      bins_text,
                                      len(orig_data.columns))
        if bins_error_status == "Error":
            raise ValueError("Bins Error")

        print(f"Bins: {bins}")

        DEBUG_STEP="getting Stretch Type"
        stretch_type, stretch_type_error_status = \
                validate_bins_stretch("stretch_type", 
                                      stretch_type_checked,
                                      stretch_type_text,
                                      len(orig_data.columns))
        if stretch_type_error_status == "Error":
            raise ValueError("Stretch Type Error")

        print(f"Stretch Type: {stretch_type}")

        DEBUG_STEP="getting Stretch Values"
        stretch, stretch_error_status = \
                validate_bins_stretch("stretch", 
                                      stretch_val_checked,
                                      stretch_val_text,
                                      len(orig_data.columns))
        if stretch_error_status == "Error":
            raise ValueError("Stretch Values Error")  

        print(f"stretch val: {stretch}")

        DEBUG_STEP = "instantiating NoGAN Model"
        nogan = NoGANSynth(orig_data,
                        random_seed=random_seed)

        DEBUG_STEP = "fitting NoGAN Model"                
        nogan.fit(bins = bins)

        DEBUG_STEP = "generating Synthetic Data"          
        synth_data = \
            nogan.generate_synthetic_data(no_of_rows = num_rows,
                                          stretch_type = stretch_type,
                                          stretch = stretch)

        
        print(f"KS Selected Value:{ks_stat_selected}")

        if ks_stat_selected is not None:
            
            DEBUG_STEP="calculating ECDF for Original and Synthetic Data"
            # Calculate ECDFs & KS Stats 
            
            for msg in multivariate_ecdf(orig_data, 
                                        synth_data, 
                                        n_nodes = num_nodes,
                                        random_seed = ks_seed):

                if msg["result_type"] == "update_progress":
                    progress = f"Original vs Synthetic - {msg['result']['progress']}"
                    progress_perc = msg["result"]["progress_perc"]
                    yield {"result_type": "update_progress", 
                        "result": {"progress": progress, 
                                    "progress_perc": progress_perc,}}
                    # socketio.emit('update_progress', 
                    #               {'progress': progress, 
                    #                'progress_perc': progress_perc})
                else:
                    ecdf_train = msg["result"]["ecdf_a"]
                    ecdf_nogan_synth = msg["result"]["ecdf_b"]            
                
            DEBUG_STEP="calculating KS Statistic for Original and Synthetic Data"
            ks_stat = ks_statistic(ecdf_train, ecdf_nogan_synth)

        if category_columns:
            DEBUG_STEP="unwrapping Category Columns"
            generated_data = \
            unwrap_category_columns(data=synth_data,
                                    idx_to_key=idx_to_key,
                                    cat_cols=category_columns)
        else:
            generated_data = synth_data                

        # Generate a unique CSV file name
        generated_data = generated_data[features]
        timestamp = int(time.time())
        csv_filename = f"result_{file_name.split('.')[0]}_{timestamp}.csv"
        generated_data.to_csv(os.path.join(data_dir, csv_filename), index=False)
        file_location = f"/download/{csv_filename}"

        if ks_stat_selected is not None:
            success_message = f"Synthetic Data file {csv_filename} generated successfully.<br><strong>KS Statistic</strong>: {ks_stat:0.4f}<br><p><a href='{file_location}'>Download</a></p>"
        else:
            success_message = f"Synthetic Data file {csv_filename} generated successfully.<br><p><a href='{file_location}'>Download</a></p>"               

        yield {"result_type": "update_message", 
               "result": {"message": success_message, 
                          "type": "success",}}
        # socketio.emit('update_message', {'message': success_message, 'type': 'success'})

    except Exception as e:
        if DEBUG_STEP.lower() in ["getting bins", "getting stretch type", "getting stretch values"]:
            error_message = f'Error in {DEBUG_LOCATION}({DEBUG_STEP}): Please check the json format'

        if DEBUG_STEP.lower() in ["getting bins"]:
            error_message = error_message + "." + " Also Bin values should not be negative or zero"
            
        if DEBUG_STEP.lower() in ["getting stretch type"]:
            error_message = error_message + "." + f" Also Stretch type should have only {list(app.config['STRETCH_TYPE'])} entries"
            
        else:                
            error_message = f'Error in {DEBUG_LOCATION}({DEBUG_STEP}): {str(e)}'

        yield {"result_type": "update_message", 
               "result": {"message": error_message, 
                          "type": "error",}}        
        # socketio.emit('update_message', {'message': error_message, 'type': 'error'})
       
@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/process', methods=['POST'])
def process():
    try:
        DEBUG_LOCATION = "Uploading Data"
        DATA_DIR = app.config['RESULT_DIR']
        SEED_CHECKED = request.form.get("sampleData")
        if SEED_CHECKED is None:
            # Get user inputs from the form
            file = request.files['file']
            file_name = file.filename
            file_type = request.form['fileType']
            delimiter = request.form['delimiter']
        else:
            # Retrieve Seed Data
            SEED_DATA_DIR = app.config['SEED_DATA_DIR']
            file_name = request.form['seedFileName']
            print(f"FileName: {file_name}")        
            seed_data = pd.read_csv(os.path.join(SEED_DATA_DIR, file_name))
            print(f"File read")
            file_type = "csv"
            delimiter = ","
                        
        print(f"Current path is: {os. getcwd()}")

        # Save the uploaded file
        DEBUG_STEP = "saving File"
        if SEED_CHECKED is not None:
            seed_data.to_csv(os.path.join(DATA_DIR, file_name), index=False)
        else:
            file.save(os.path.join(DATA_DIR, file_name))

        # Redirect to the second page for column selection and row generation
        return redirect(url_for('generate', 
                                file_name = file_name, 
                                file_type=file_type, 
                                delimiter=delimiter))

    except Exception as e:
            error_message = f'Error in {DEBUG_LOCATION}({DEBUG_STEP}): {str(e)}'
            return render_template('results.html', 
                                   success_message=None,
                                   error_message=error_message)
            
@app.route('/generate', methods=['GET', 'POST'])
def generate():
    DATA_DIR = app.config['RESULT_DIR']
    if request.method == 'GET':
        DEBUG_LOCATION="Reading Data"
        try:
            file_name = request.args.get('file_name')
            file_type = request.args.get('file_type')
            delimiter = request.args.get('delimiter')
                         
            # Load data into a pandas DataFrame based on file type
            print(f"File Type: {file_type}")
            na_values_list = app.config["NA_VALUES_LIST"]
            if file_type == 'csv':
                DEBUG_STEP="Reading CSV File"
                df = pd.read_csv(os.path.join(DATA_DIR, file_name), 
                                 delimiter=delimiter, 
                                 na_values=na_values_list)
            elif file_type == 'text':
                DEBUG_STEP="Reading Text File"
                df = pd.read_csv(os.path.join(DATA_DIR, file_name), 
                                 delimiter=delimiter, 
                                 na_values=na_values_list)
            elif file_type == 'excel':
                DEBUG_STEP="Reading Excel File"
                df = pd.read_excel(os.path.join(DATA_DIR, file_name),
                                   na_values=na_values_list
                                   )            

            # Get column names for category selection
            DEBUG_STEP="Getting Columns List from Data"
            columns = df.select_dtypes(include=['number']).columns.tolist()
            non_numeric_cols_count = \
                    len(df.select_dtypes(exclude=['number']).columns)
            
            if not columns:
                raise ValueError("No Numerical Columns Present!!")
            
            if re.search(r'[^a-zA-Z0-9_]', "".join(columns)):
                raise ValueError("Special Characters or Space present in Column Names. Please remove them & try again")

            return render_template('generate.html', 
                                   data_head = df.head(10),
                                   row_count = df.shape[0],
                                   columns = columns,
                                   non_numeric_cols_count = non_numeric_cols_count,
                                   file_name = file_name,
                                   file_type = file_type,
                                   delimiter = delimiter,
                                   success_message = None,
                                   error_message = None
                                   )
        
        except Exception as e:
            error_message = f'Error in {DEBUG_LOCATION}({DEBUG_STEP}): {str(e)}'
            return render_template('results.html', 
                                   success_message=None,
                                   error_message=error_message)              

    elif request.method == 'POST':
        DEBUG_LOCATION = "Processing Data"
        t = 0.01
        try:
            action_selected = request.form['action']
            selected_columns = request.form.getlist('category_columns')
            file_name = request.form["fileName"]
            file_type = request.form["fileType"]            
            delimiter = request.form["delimiter"]
            random_seed = int(request.form["seed"])
            ks_seed = int(request.form["KSSeed"])
            bins_checked = request.form.get("bins")
            bins_text = request.form["binsText"]
            stretch_type_checked = request.form.get("stretchType")
            stretch_type_text = request.form["StretchTypeText"]
            stretch_val_checked = request.form.get("stretchVal")
            stretch_val_text = request.form["stretchValText"]            
            
            # Set Random Seed
            # seed = np.random.randint(low=1, high=9999999, size=1)
            na_values_list = app.config["NA_VALUES_LIST"]
            if file_type == "excel":
                DEBUG_STEP="Reading Excel Data"
                orig_data = pd.read_excel(os.path.join(DATA_DIR, file_name),
                                          na_values = na_values_list)
            else:
                DEBUG_STEP="Reading Text/CSV Data"
                orig_data = pd.read_csv(os.path.join(DATA_DIR, file_name),
                                        delimiter=delimiter,
                                        na_values = na_values_list)
                print("Read csv/txt data")
                                
            orig_data = orig_data.dropna()
            features = orig_data.columns
            cat_cols = \
                orig_data.select_dtypes(exclude=['number']).columns.tolist()
            
            category_columns = selected_columns + cat_cols
            
            print(f"Datafile Shape: {orig_data.shape}")
            print(f"Category Columns: {category_columns}")

            if action_selected == 'validate':
                num_nodes = int(request.form['valNumNodes'])

                for msg in validate_data(orig_data, features, 
                                          category_columns, bins_checked, bins_text, stretch_type_checked, stretch_type_text,stretch_val_checked, stretch_val_text, num_nodes,random_seed, ks_seed, DATA_DIR, file_name):
                    time.sleep(t)
                    if msg["result_type"] == "update_progress":
                        socketio.emit('update_progress', msg["result"])
                    else:
                        socketio.emit('update_message', msg["result"])
                return Response(status=204)
                
            else:
                DEBUG_LOCATION = "Data Generation"
                num_rows = int(request.form['genNumRows'])
                ks_stat_selected = request.form.get('genKSStats')
                if ks_stat_selected:
                    num_nodes = int(request.form['genNumNodes'])
                else:
                    num_nodes = ""
                
                for msg in generate_data(orig_data, features, 
                                          category_columns,
                                          bins_checked, bins_text, stretch_type_checked,stretch_type_text, stretch_val_checked,stretch_val_text, ks_stat_selected, 
                                          num_nodes, num_rows,
                                          random_seed, ks_seed, DATA_DIR, file_name):
                    time.sleep(t)
                    if msg["result_type"] == "update_progress":
                        socketio.emit('update_progress', msg["result"])
                    else:
                        socketio.emit('update_message', msg["result"])

                return Response(status=204)

        except Exception as e:            
            error_message = f'Error in {DEBUG_LOCATION}({DEBUG_STEP}): {str(e)}'
            socketio.emit('update_message', 
                          {'message': error_message, 'type': 'error',})
            
            # return jsonify({'success_message': None, 'error_message': None})
            return None

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['RESULT_DIR'],
                               filename, 
                               as_attachment=True)
