from app import app
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
from nogan_synthesizer import NoGANSynth
from nogan_synthesizer.preprocessing import wrap_category_columns, unwrap_category_columns
from genai_evaluation import multivariate_ecdf, ks_statistic
import pandas as pd
import numpy as np
import os
import random
import time
import re
import json

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/process', methods=['POST'])
def process():
    DATA_DIR = "./app/data"
    try:
        # Get user inputs from the form
        file = request.files['file']
        file_name = file.filename
        file_type = request.form['fileType']
        delimiter = request.form['delimiter']
        print(f"Current path is: {os. getcwd()}")

        # Save the uploaded file
        file.save(os.path.join(DATA_DIR, file_name))

        # Redirect to the second page for column selection and row generation
        return redirect(url_for('generate', file_name = file_name, file_type=file_type, delimiter=delimiter))

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
            
@app.route('/generate', methods=['GET', 'POST'])
def generate():
    DATA_DIR = "./app/data"
    if request.method == 'GET':
        DEBUG_LOCATION="Reading Data"
        try:
            file_name = request.args.get('file_name')
            file_type = request.args.get('file_type')
            delimiter = request.args.get('delimiter')
                         
            # Load data into a pandas DataFrame based on file type
            print(f"File Type: {file_type}")
            if file_type == 'csv':
                DEBUG_STEP="Reading CSV File"
                df = pd.read_csv(os.path.join(DATA_DIR, file_name), delimiter=delimiter)
            elif file_type == 'text':
                DEBUG_STEP="Reading Text File"
                df = pd.read_csv(os.path.join(DATA_DIR, file_name), delimiter=delimiter)
            elif file_type == 'excel':
                DEBUG_STEP="Reading Excel File"
                df = pd.read_excel(os.path.join(DATA_DIR, file_name))            

            # Get column names for category selection
            DEBUG_STEP="Getting Columns List from Data"
            columns = df.columns.tolist()
            print(f"Columns before going to Generate Page: {columns}")
            
            if re.search(r'[^a-zA-Z0-9_]', "".join(columns)):
                raise ValueError("Special Characters or Space present in Column Names. Please remove them & try again")

            return render_template('generate.html', columns = columns,
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
        try:
            action_selected = request.form['action']
            category_columns = request.form.getlist('category_columns')
            file_name = request.form["fileName"]
            file_type = request.form["fileType"]            
            delimiter = request.form["delimiter"]

            print(f"File Name in Post: {file_name}")
            
            # Set Random Seed
            seed = np.random.randint(low=1, high=9999999, size=1)
            
            if file_type == "excel":
                DEBUG_STEP="Reading Excel Data"
                orig_data = pd.read_excel(os.path.join(DATA_DIR, file_name))
            else:
                DEBUG_STEP="Reading Text/CSV Data"
                orig_data = pd.read_csv(os.path.join(DATA_DIR, file_name),
                                        delimiter=delimiter)
                                
            orig_data = orig_data.dropna()
            features = orig_data.columns
            print(f"Datafile Shape: {orig_data.shape}")

            if action_selected == 'validate':
                DEBUG_LOCATION="Data Validation"
                num_nodes = int(request.form['valNumNodes'])
                train_data = orig_data.sample(frac=0.5)
                val_data = orig_data.drop(train_data.index)
            
                if category_columns:
                    train_data, _ , _ = \
                            wrap_category_columns(train_data,
                                                  category_columns)                
                    val_data, _ , _ = \
                            wrap_category_columns(val_data,
                                                  category_columns)                               
                # Train NoGAN
                DEBUG_STEP="getting Bins"
                bins_json = request.form["binsText"]               
                if bins_json:
                    bins_json = json.loads(bins_json)
                    bins = [bins_json[key] for key in bins_json]
                else:
                    bins = [100] * len(train_data.columns)
                print(f"bins json: {bins_json}") 
                
                DEBUG_STEP="getting Stretch Type"
                stretch_type_json = request.form["StretchTypeText"]
                if stretch_type_json:
                    stretch_type_json = json.loads(stretch_type_json)
                    stretch_type = \
                        [stretch_type_json[key] for key in stretch_type_json]
                else:
                    stretch_type = ["Uniform"] * len(train_data.columns)
                print(f"stretch type json: {stretch_type_json}")
                
                DEBUG_STEP="getting Stretch Values"
                stretch_val_json = request.form["stretchValText"]
                if stretch_val_json:
                    stretch_val_json = json.loads(stretch_val_json)
                    stretch = \
                        [stretch_val_json[key] for key in stretch_val_json]
                else:
                    stretch = [1.0] * len(train_data.columns)
                print(f"stretch val json: {stretch_val_json}")
                
                DEBUG_STEP = "instantiating NoGAN Model"
                nogan = NoGANSynth(train_data,
                                random_seed=seed)
                
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
                _, ecdf_val1, ecdf_nogan_synth = \
                            multivariate_ecdf(val_data, 
                                              synth_data, 
                                              n_nodes = num_nodes,
                                              verbose = False,
                                              random_seed=seed)
                
                DEBUG_STEP="calculating ECDF for Validation and Training Data"
                _, ecdf_val2, ecdf_train = \
                            multivariate_ecdf(val_data, 
                                              train_data, 
                                              n_nodes = num_nodes,
                                              verbose = False,
                                              random_seed=seed)
                
                DEBUG_STEP="calculating KS Statistic for Validation and Synthetic Data"
                ks_stat = ks_statistic(ecdf_val1, ecdf_nogan_synth)
                
                DEBUG_STEP="calculating KS Statistic for Validation and Training Data"
                base_ks_stat = ks_statistic(ecdf_val2, ecdf_train)
                success_message = f"KS Statistic is: {ks_stat:0.4f}\nBase KS Statistic is: {base_ks_stat:0.4f}"

                # Redirect to the results page and pass the success message
                return jsonify({'success_message': success_message,
                                'file_location': None, 
                                'error_message': None})
            else:
                DEBUG_LOCATION = "Data Generation"
                num_rows = int(request.form['genNumRows'])
                print(f"Num Rows: {num_rows}")
                try:             
                    ks_stat_selected = request.form['genKSStats']
                except Exception as e:
                    ks_stat_selected = False
                print(f"KS Selected Value:{ks_stat_selected}")
                if category_columns:
                    DEBUG_STEP = "wrapping category columns"
                    wrapped_data, idx_to_key, _ = \
                            wrap_category_columns(orig_data,
                                                category_columns)
                    orig_data = wrapped_data
                
                # Train NoGAN
                bins_json = request.form["binsText"]
                
                DEBUG_STEP = "getting Bins"
                if bins_json:
                    bins_json = json.loads(bins_json)
                    bins = [bins_json[key] for key in bins_json]
                else:
                    bins = [100] * len(train_data.columns)
                
                DEBUG_STEP = "getting Stretch Type"
                stretch_type_json = request.form["StretchTypeText"]
                if stretch_type_json:
                    stretch_type_json = json.loads(stretch_type_json)
                    stretch_type = \
                        [stretch_type_json[key] for key in stretch_type_json]
                else:
                    stretch_type = ["Uniform"] * len(train_data.columns)
                
                DEBUG_STEP = "getting Stretch Values"
                stretch_val_json = request.form["stretchValText"]
                if stretch_val_json:
                    stretch_val_json = json.loads(stretch_val_json)
                    stretch = \
                        [stretch_val_json[key] for key in stretch_val_json]
                else:
                    stretch = [1.0] * len(train_data.columns)
                
                DEBUG_STEP = "instantiating NoGAN Model"
                nogan = NoGANSynth(orig_data,
                                random_seed=seed)
                
                DEBUG_STEP = "fitting NoGAN Model"                
                nogan.fit(bins = bins)
                
                DEBUG_STEP = "generating Synthetic Data"            
                synth_data = \
                    nogan.generate_synthetic_data(no_of_rows = num_rows,
                                                  stretch_type = stretch_type,
                                                  stretch = stretch)
                
                if ks_stat_selected:
                    num_nodes = int(request.form['genNumNodes'])
                    
                    DEBUG_STEP="calculating ECDF for Original and Synthetic Data"
                    # Calculate ECDFs & KS Stats 
                    _, ecdf_train, ecdf_nogan_synth = \
                                multivariate_ecdf(orig_data, 
                                                  synth_data, 
                                                  n_nodes = num_nodes,
                                                  verbose = False,
                                                  random_seed=seed)
                    
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
                print(f"Filname type: {type(file_name)}")
                csv_filename = f"result_{file_name.split('.')[0]}_{timestamp}.csv"
                generated_data.to_csv(os.path.join(DATA_DIR, csv_filename), index=False)
                file_location = f"/download/{csv_filename}"

                if ks_stat_selected:
                    success_message = f"Synthetic Data file {csv_filename} generated successfully.\nKS Statistic is: {ks_stat:0.4f}"
                else:
                    success_message = f'Synthetic Data file {csv_filename} generated successfully.'                    

                return jsonify({'success_message': success_message,
                                'file_location': file_location,
                                'error_message': None})

        except Exception as e:
            if DEBUG_STEP.lower() in ["getting bins", "getting stretch type", "getting stretch values"]:
                error_message = f'Error in {DEBUG_LOCATION}({DEBUG_STEP}): Please check the json format'
            else:                
                error_message = f'Error in {DEBUG_LOCATION}({DEBUG_STEP}): {str(e)}'
            
            return jsonify({'success_message': None,
                            'file_location': None,
                            'error_message': error_message})

@app.route('/download/<filename>')
def download(filename):
    DATA_DIR="./app/data"
    # Serve the file for download from the 'data' directory
    return send_from_directory(DATA_DIR, filename, as_attachment=True)
