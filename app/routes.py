from flask import render_template, send_file, send_from_directory, request

from flask_wtf import FlaskForm
from wtforms import SubmitField
import requests, os
from werkzeug.wrappers import Response
import json
import pandas as pd
from pandas.io.json import json_normalize
from apscheduler.schedulers.background import BackgroundScheduler
from os.path import exists

from app import app
from app.odk_requests import odata_submissions
from app.odk_requests import export_submissions
from app.odk_requests import odata_submissions_machine
from app.odk_requests import number_submissions
from app.odk_requests import get_newest_submissions
from app.odk_requests import odata_submissions_table
from app.odk_requests import list_attachments
from app.odk_requests import odata_attachments

from app.helper_functions import get_filters, nested_dictionary_to_df
from app.helper_functions import flatten_dict
from app.graphics import count_items, unique_key_counts, charts


import csv

#For time testing
import time
def timer(message, function):
    tic = time.perf_counter()
    tutorial = feed.get_article(0)
    toc = time.perf_counter()
    print(f"{message}' '{toc - tic:0.4f} seconds")

secret_tokens = json.load(open('secret_tokens.json', 'r'))
email = secret_tokens['email']
password = secret_tokens['password']
aut = (email, password)

auth_values =json.dumps({
    "email": email,
    "password": password
    })

headers = {
    'Content-Type': 'application/json'
    }

base_url = 'https://omdtz-data.org'

mills_columns = ['__id', 'start','end', 'interviewee.mill_owner', 'mills.number_milling_machines', 'machines.machine_count', 'Packaging.flour_fortified',
                 'Packaging.flour_fortified_standard', 'Packaging.flour_fortified_standard_other', 'safety_cleanliness.protective_gear',
                 'safety_cleanliness.protective_gear_other', 'Location.mill_gps.coordinates']

# get the form configured data
form_details = list()
form_index = 0
with open('app/static/form_config.csv', newline='') as file:
    form_config = csv.DictReader(file)
    for row in form_config:
        form_details.append(row)
projectId = form_details[form_index]['projectId']
formId = form_details[form_index]['formId']
lastNumberRecordsMills = form_details[form_index]['lastNumberRecordsMills']
lastNumberRecordsMachines = form_details[form_index]['lastNumberRecordsMachines']

# Functions for downloading attachments
def get_submission_ids(mills_table):
    submission_ids = [row['__id'] for row in mills_table]
    return submission_ids

def download_attachments(base_url, aut, projectId, formId, mills_table):
    submission_ids = get_submission_ids(mills_table)
    for instanceId in submission_ids:
        odata_attachments(base_url, aut, projectId, formId, instanceId)

def get_attachment_names(base_url, aut, projectId, formId):
    attachments = list_attachments(base_url, aut, projectId, formId).json()
    attachment_names = [row['name'] for row in attachments]
    return attachment_names

attachment_names = get_attachment_names(base_url, aut, projectId, formId)
def download_attachments(base_url, aut, projectId, formId, submission_ids):
    for instanceId in submission_ids:
        odata_attachments(base_url, aut, projectId, formId, instanceId)

# Get all the mills from the ODK server, flatten them and save them a csv file
def fetch_mills_csv(base_url, aut, projectId, formId):
    #Loop through the forms and combine them
    form_data = list()
    for i in range(1, len(form_details)):
        form_index = i - 1
        print(f'Form index is : {form_index}')
        formId = form_details[form_index]['formId']
        #Fetch the data
        start_time = time.perf_counter()
        submissions_response = odata_submissions(base_url, aut, projectId, formId)
        mill_fetch_time = time.perf_counter()
        submissions = submissions_response.json()['value']
        flatsubs = [flatten_dict(sub) for sub in submissions]
        print(f'Fetched mills in {mill_fetch_time - start_time}s')
        # select only the wanted columns
        flatsubs = [{key: row[key] for key in mills_columns} for row in flatsubs]
        form_data.append(flatsubs)
    flatsubs = [item for elem in form_data for item in elem]
    #open a file for writing
    data_file = open('app/submission_files/mills.csv', 'w')
    csv_writer = csv.writer(data_file)
    # Counter variable used for writing
    count = 0
    flatsubs = sorted(flatsubs, key=lambda d: d['__id'])
    # write the rows
    for emp in flatsubs:
        if count == 0:
            # Writing headers of CSV file
            header = emp.keys()
            csv_writer.writerow(header)
            count += 1
        # Writing data of CSV file
        csv_writer.writerow(emp.values())
    data_file.close()

# Check if the files folder exist, if not, create one and fetch the data from odk to fill it
path = 'app/submission_files'
isdir = os.path.isdir(path)
if isdir:
    next
else:
    os.makedirs('app/submission_files')
    os.makedirs('app/submission_files/figures')

# check if the mills file exists, if not, fetch the data from ODK
if os.path.exists('app/submission_files/mills.csv'):
    next
else:
    # fetch all the mills data from odk
    fetch_mills_csv(base_url, aut, projectId, formId)

# todo: finish this to get the list of submission ids that you have for each form
# Check which submission ids each form has
#submission_ids = submission_csv['__id']
#form_details[form_index]['formId']

session_info = requests.post(url = f'{base_url}/v1/sessions',
                             data=auth_values, headers=headers)
session_token = session_info.json()['token']

headers = {
    'Authorization': session_token
    }
url = f'{base_url}/v1/projects/'
r =requests.get(url, headers=headers)

# Check if there is new data at the odk server,and save the new count to the config file
for i in range(1,len(form_details)):
    form_index = i - 1
    formId = form_details[form_index]['formId']
    submission_count = number_submissions(base_url, aut, projectId, formId)
    form_details[form_index]['lastNumberRecordsMills'] = submission_count
    form_details[form_index]['lastChecked'] = time.localtime(time.time())
# Update the config file with the new number of submissions and the new current timestamp
with open('app/static/form_config.csv', 'w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=form_details[form_index].keys())
    writer.writeheader()
    for row in form_details:
        writer.writerow(row)

# ONLY FOR TESTING PURPOSES, REMOVE FROM FINAL VERSION
#lastNumberRecordsMills = 1400
submission_count = 100

# Check if there are any new submissions, if there are, add them to the csv file
new_records_flag = False

def check_new_submissions_odk(submission_count = submission_count, lastNumberRecordsMills = lastNumberRecordsMills):
    if submission_count - int(lastNumberRecordsMills) > 0:
        new_records_flag = True
        new_records_count = submission_count - int(lastNumberRecordsMills)
        print('New records!')
        newest_submissions_response = get_newest_submissions(base_url, aut, projectId, formId, new_records_count).json()
        print(len(newest_submissions_response['value']))

        #Write the new records to the csv file
        #transform the new submissions to flat
        new_submissions = newest_submissions_response['value']
        new_flatsubs = [flatten_dict(sub) for sub in new_submissions]
        # read the old submissions
        mills = list()
        with open('app/submission_files/mills.csv', newline='') as data_file:
            mills_csv = csv.DictReader(data_file)
            # combine the new and old data (new_submissions and new_flatsubs)
            for row in mills_csv:
                # transform the coordinates from a string to a list if they are not yet
                try:
                    row['Location.mill_gps.coordinates'] = row['Location.mill_gps.coordinates'][1:-1].split(',')
                    row['Location.mill_gps.coordinates'] = [float(ele) for ele in row['Location.mill_gps.coordinates']]
                except: print('already a list')
                mills.append(row)
        # select only the wanted column
        new_flatsubs = [{key: row[key] for key in mills_columns} for row in new_flatsubs]
        for row in new_flatsubs:
            mills.append(row)
        data_file.close()
        # write all the data to the csv
        with open('app/submission_files/mills.csv', 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=mills[0].keys())
            writer.writeheader()
            #sort the rows based on the id
            mills = sorted(mills, key=lambda d: d['__id'])
            for row in mills:
                writer.writerow(row)
        return(new_records_flag)
    else:
        print('No new records.')
        new_records_flag = False
        return(new_records_flag)

#new_records_flag = check_new_submissions_odk()

sched = BackgroundScheduler(daemon=True)
sched.add_job(check_new_submissions_odk,'interval',seconds=120)
sched.start()
# scheduler = BackgroundScheduler()
# scheduler.add_job(func=check_new_submissions_odk(submission_count, lastNumberRecordsMills), trigger="interval", seconds=60)
# scheduler.start()
# atexit.register(lambda: scheduler.shutdown())

@app.route('/mills')
def mills():
    # Read the data
    mills = list()
    with open('app/submission_files/mills.csv', newline='') as file:
        mills_csv = csv.DictReader(file)
        for row in mills_csv:
            # transform the coordinates from a string to a list
            row['Location.mill_gps.coordinates'] = row['Location.mill_gps.coordinates'][1:-1].split(',')
            mills.append(row)
    return json.dumps(mills)

@app.route('/machines')
def machines():
    start_time = time.perf_counter()
    machines_response = \
        odata_submissions_machine(base_url,
                                  aut,
                                  projectId,
                                  formId)
    machine_fetch_time = time.perf_counter()
    machines = machines_response.json()['value']
    flatmachines = [flatten_dict(mach) for mach in machines]
    print(f'Fetched machines in {machine_fetch_time - start_time}s')

    #open a file for writing
    data_file = open('app/submission_files/machines.csv', 'w')
    # create the csv writer object
    csv_writer = csv.writer(data_file)
    # Counter variable used for writing
    # headers to the CSV file
    count = 0
    for emp in flatmachines:
        if count == 0:
            # Writing headers of CSV file
            header = emp.keys()
            csv_writer.writerow(header)
            count += 1
        # Writing data of CSV file
        csv_writer.writerow(emp.values())
    data_file.close()
    return json.dumps(flatmachines)

@app.route('/sites')
def sites():
    import concurrent.futures

    results = []
    with concurrent.futures.ThreadPoolExecutor() as ex:
        futures = []
        futures.append(mills)
        futures.append(machines)
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())



@app.route('/mill_points')
def mill_points():
    start_time = time.perf_counter()
    submissions = odata_submissions(base_url, aut, projectId, formId)
    submissions_machine = odata_submissions_machine(base_url,
                                                    aut, projectId, formId)
    requests_complete_time = time.perf_counter()
    submissions_table =  pd.DataFrame(submissions.json()['value'])
    submissions_machine_table =  \
        pd.DataFrame(submissions_machine.json()['value'])
    pd_df_complete_time = time.perf_counter()
    charts(submissions_machine.json()['value'], submissions.json()['value'])
    charts_complete_time = time.perf_counter()

    # Dataframe with nested dictionaries to flat dictionary
    submissions_table = nested_dictionary_to_df(submissions_table)
    submissions_machine_table = \
        nested_dictionary_to_df(submissions_machine_table)
    submissions_all = submissions_table.merge(submissions_machine_table,
                                              left_on = '__id',
                                              right_on = '__Submissions-id')
    tables_to_flat_complete_time = time.perf_counter()

    mill_filter_list = ['mill_owner','flour_fortified', 'flour_fortified_standard']
    machine_filter_list = ['commodity_milled',
                           'mill_type', 'operational_mill',
                           'non_operational', 'energy_source']
    mill_filter_selection = get_filters(mill_filter_list, submissions_all)
    machine_filter_selection = get_filters(machine_filter_list,
                                           submissions_all)
    get_filters_complete_time = time.perf_counter()
    submissions_table_filtered_machine = \
        submissions_machine_table.to_dict(orient = 'index')
    submissions_filtered_dict = submissions_table.to_dict(orient='index')
    #submissions_table_filtered_dict = json.loads(submissions_table_filtered)
    # Make submissions_table_filtered into dictionary of dictionaries
    # with machine information nested within
    submissions_dict = submissions_filtered_dict
    for submission_id in submissions_dict:
        submissions_dict[submission_id]['machines'] = {}
        for machine_index in submissions_table_filtered_machine:
            machine_submission_id = \
                submissions_table_filtered_machine[machine_index]\
                ['__Submissions-id']
            machine_id = \
                submissions_table_filtered_machine[machine_index]['__id']
            if machine_submission_id == submission_id:
                submissions_dict[submission_id]['machines'][machine_index] = \
                    submissions_table_filtered_machine[machine_index]
    submissions_filtered_json = json.dumps(submissions_dict)

    to_json_complete_time = time.perf_counter()
    print(f'Requests are complete at {requests_complete_time-start_time}s,'\
          f'pandas dataframes are complete at '
          f'{pd_df_complete_time-requests_complete_time}s, charts are complete'\
          f'at {charts_complete_time-pd_df_complete_time}s, tables are flat '\
          f'in {tables_to_flat_complete_time-charts_complete_time}s, got '\
          f'filters in '\
          f'{get_filters_complete_time-tables_to_flat_complete_time}s, '\
          f'and to_json in {to_json_complete_time-get_filters_complete_time}s')
    return submissions_filtered_json

@app.route('/json_test')
def json_test():
    test_submission = json.load(open('individual_test_submission.json', 'r'))
    return json.dumps(test_submission)

@app.route('/')
@app.route('/index')
@app.route('/home')
def index():
    return render_template('index.html', title='Map')

@app.route('/filterform', methods = ['GET', 'POST'])
def filter_data():
    if request.method == 'POST':
        choices = request.form
        choices_dict = {}
        for choice in choices:
            choice_element = choice.split(", ")[0]
            if choice_element not in choices_dict:
                choices_dict[choice_element] = []
            choices_dict[choice_element].append(choice.split(", ")[1])

            submissions = odata_submissions(base_url, aut, projectId, formId)
            submissions_machine = odata_submissions_machine(base_url,
                                                            aut, projectId,
                                                            formId)
            # charts(submissions_machine.json()['value'],
            #       submissions.json()['value'])
            submissions_table =  \
                pd.DataFrame(odata_submissions_table(base_url, aut,
                                                     projectId, formId,
                                                     'Submissions')['value'])
            submissions_machine_table =  \
                pd.DataFrame(odata_submissions_table(base_url, aut,\
                                                     projectId, formId,
                                                     'Submissions.machines.machine')['value'])
            # Dataframe with nested dictionaries to flat dictionary
            submissions_table = nested_dictionary_to_df(submissions_table)
            submissions_machine_table = \
                nested_dictionary_to_df(submissions_machine_table)
            submissions_all = \
                submissions_table.merge(submissions_machine_table,
                                        left_on = '__id',
                                        right_on = '__Submissions-id')
            mill_filter_list = ['mill_owner','flour_fortified',
                                'flour_fortified_standard']
            machine_filter_list = ['commodity_milled', 'mill_type',
                                   'operational_mill', 'non_operational',
                                   'energy_source']
            mill_filter_selection = get_filters(mill_filter_list,
                                                submissions_all)
            # Filtering based on the form for machines
            for dict_key, dict_values in zip(list(choices_dict.keys()),
                                             list(choices_dict.values())):
                if dict_key in submissions_machine_table.columns:
                    submissions_machine_table = \
                        submissions_machine_table.loc[submissions_machine_table[dict_key].isin(dict_values)]
            submissions_table_filtered_machine = \
                submissions_machine_table.to_dict(orient = 'index')
            #submissions_table_filtered_machine_dict = \
            #    json.loads(submissions_table_filtered_machine)
		#{k: [d[k] for d in dicts] for k in dicts[0]}

	    # Filtering based on the form for the mill
	    #if all the selections have been deselected from one category
            for mill_key in mill_filter_selection:
                if mill_key not in list(choices_dict.keys()):
                    submissions_table.drop(submissions_table.index, inplace=True)
		#filter based on the choices
            for dict_key, dict_values in zip(list(choices_dict.keys()), list(choices_dict.values())):
                if dict_key in submissions_table.columns:
                    submissions_table[dict_key] = \
                        list(map(str,list(submissions_table[dict_key])))
                    submissions_table = \
                        submissions_table.loc[submissions_table[dict_key].isin(dict_values)]
                submissions_table.set_index('__id', inplace=True)
                submissions_filtered_dict = \
                    submissions_table.to_dict(orient='index')
		#submissions_table_filtered_dict = \
                #    json.loads(submissions_table_filtered)


		# Make submissions_table_filtered into dictionary of
                # dictionaries with machine information nested within
                submissions_dict = submissions_filtered_dict
                for submission_id in submissions_dict:
                    submissions_dict[submission_id]['machines'] = {}
                    for machine_index in submissions_table_filtered_machine:
                        machine_submission_id = \
                            submissions_table_filtered_machine[machine_index]['__Submissions-id']
                        machine_id = \
                            submissions_table_filtered_machine[machine_index]['__id']
                        if machine_submission_id == submission_id:
                            submissions_dict[submission_id]['machines'][machine_index] = \
                                submissions_table_filtered_machine[machine_index]

        submissions_filtered_json = json.dumps(submissions_dict)
        return render_template('index.html',
                               submissions_filtered = submissions_filtered_json,
                               mill_filter_selection = mill_filter_selection,
                               title='Map', choices_dict = choices_dict)

@app.route('/download_data/')
def export_data():
    #Export all the data from ODK form
    r = export_submissions(base_url, aut, projectId, formId)
    file_name = formId
    if not os.path.exists('files'):
        outdir = os.makedirs('files')

	#Saves the file also locally
        with open(f'files/{file_name}.zip', 'wb') as zip:
            zip.write(r.content)
    basename = os.path.basename(f'files/{file_name}.zip')
    dirname = os.path.dirname(os.path.abspath(f'files/{file_name}.zip'))
    send_from_directory(dirname, basename, as_attachment=True)

    #Stream the response as the data is generated
    response = Response(r.content, content_type='zip')
    response.headers.set("Content-Disposition", "attachment",
                         filename=f"{file_name}.zip")
    return response

