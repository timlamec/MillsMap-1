from flask import render_template, send_from_directory, request
import atexit
import csv
import requests, os
from werkzeug.wrappers import Response
import json
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from os.path import exists
import time
# Local imports
from app import app
from app.odk_requests import odata_submissions, get_submission_details, export_submissions, number_submissions, \
    odata_submissions_table, list_attachments, odata_attachments
from app.helper_functions import get_filters, nested_dictionary_to_df, flatten_dict
from app.graphics import count_items, unique_key_counts, charts

# Configured values
# todo: set these values to another config file that is read in the beginning
secret_tokens = json.load(open('secret_tokens.json', 'r'))
email = secret_tokens['email']
password = secret_tokens['password']
aut = (email, password)
base_url = 'https://omdtz-data.org'
mills_columns = ['__id', 'start', 'end', 'interviewee_mill_owner', 'mills_number_milling_machines',
                 'machines_machine_count', 'Packaging_flour_fortified',
                 'Packaging_flour_fortified_standard', 'Packaging_flour_fortified_standard_other',
                 'safety_cleanliness_protective_gear',
                 'safety_cleanliness_protective_gear_other', 'Location_mill_gps_coordinates']
machine_columns = ['']
submission_files_path = 'app/submission_files'
id_columns = ['__id', '__Submissions-id']
# Get the form configured data
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
#attachment_names = get_attachment_names(base_url, aut, projectId, formId)

def download_attachments(base_url, aut, projectId, formId, submission_ids):
    for instanceId in submission_ids:
        odata_attachments(base_url, aut, projectId, formId, instanceId)

# Get all the mills from the ODK server, flatten them and save them a csv file
def fetch_odk_csv(base_url, aut, projectId, formId, table='Submissions', sort_column = '__id'):
    # Fetch the data
    start_time = time.perf_counter()
    submissions_response = odata_submissions(base_url, aut, projectId, formId, table)
    mill_fetch_time = time.perf_counter()
    submissions = submissions_response.json()['value']
    flatsubs = [flatten_dict(sub) for sub in submissions]
    print(f'Fetched table {table} in {mill_fetch_time - start_time}s')
    # select only the wanted columns
    #form_data = [{key: row[key] for key in mills_columns} for row in flatsubs]
    #flatsubs = form_data

    # open a file for writing
    file_name = ''.join([formId, '.csv'])
    dir = 'app/submission_files'
    path = os.path.join(dir, table, file_name)
    with open(path, 'w') as data_file:
        csv_writer = csv.writer(data_file)
        # Counter variable used for writing
        count = 0
        flatsubs = sorted(flatsubs, key=lambda d: d[sort_column])
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

# Update the config file with the new number of submissions and the new current timestamp
def update_form_config_file(form_details):
    with open('app/static/form_config.csv', 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=form_details[form_index].keys())
        writer.writeheader()
        for row in form_details:
            writer.writerow(row)

# Check if the files folder exist, if not, create one and fetch the data from odk to fill it
path = 'app/submission_files'
if not os.path.exists('app/submission_files'):
    os.makedirs('app/submission_files')
if not os.path.exists('app/submission_files/figures'):
    os.makedirs('app/submission_files/figures')

# check if the folders exists, if not, fetch the data from ODK
table_names = ['Submissions', 'Submissions.machines.machine']
for table_name in table_names:
    path = os.path.join(submission_files_path, table_name)
    if exists(path):
        next
    else:
        os.makedirs(path)

# check if the files exists, if not, fetch the data from ODK
formId_list = list()
for i in range(0, len(form_details)):
    form_index = i
    formId = form_details[form_index]['formId']
    formId_list.append(formId)
    file_name = ''.join([formId, '.csv'])
    for (table_name, id) in zip(table_names, id_columns):
        path = os.path.join(submission_files_path, table_name, file_name)
        if exists(path):
            next
        else:
            # fetch all the mills data from odk
            fetch_odk_csv(base_url, aut, projectId, formId, table=table_name, sort_column = id)

# ONLY FOR TESTING PURPOSES, REMOVE FROM FINAL VERSION
# lastNumberRecordsMills = 1400
# submission_count = 100

def get_form_column(table, formId, column='__id'):
    """
    Retrieve a specific column from a csv file
    Return the column as a list
    """
    # get the ids of the submissions csv form as a list
    file_name = ''.join([formId, '.csv'])
    path = os.path.join(submission_files_path, table, file_name)
    with open(path, newline='') as data_file:
        csv_file = csv.DictReader(data_file)
        file = list()
        # combine the new and old data (new_submissions and new_flatsubs)
        for row in csv_file:
            file.append(row)
    data_file.close()
    # select only the wanted column
    formId_list = [row[column] for row in file]
    return formId_list


def get_new_sub_ids(table, formId, odk_details_column, local_column):
    submission_id_list = get_form_column(table, formId, local_column)
    submission_odk_details = get_submission_details(base_url, aut, projectId, formId, table)
    submission_odk_ids = [row[odk_details_column] for row in submission_odk_details]
    submission_odk_ids = sorted(submission_odk_ids)
    new_submission_ids = list(set(submission_odk_ids) - set(submission_id_list))
    return new_submission_ids

def check_removed_forms(form_details):
    form_names = [form['formId'] for form in form_details]
    main_table_name = 'Submissions'
    path = os.path.join(submission_files_path, main_table_name)
    sub_files = os.listdir(path)
    for file in sub_files:
        file_name = os.path.splitext(file)[0]
        if file_name not in form_names:
            mills_path = os.path.join(path, file)
            os.remove(mills_path)
            machine_path = os.path.join(submission_files_path, 'Submissions.machines.machine', file)
            os.remove(machine_path)
            # todo include also removing the figures automatically



def check_new_submissions_odk(form_details=form_details):
    """
    Checks whether there are new submissions in the active forms and triggers fetching them if there are
    Checks if the config file has less forms and removes those
    Updates the config file based on the latest updates
    """
    for form_index in range(0, len(form_details)):
        # Check if there are files that are not in the config file and remove those
        check_removed_forms(form_details)

        # Check whether the form is active or not, or if it has not been checked before
        if form_details[form_index]['activityStatus'] == '1'or form_details[form_index]['lastChecked']=='':
            # Check if there are new submissions in the form
            if type(form_details[form_index][
                        'lastNumberRecordsMills']) != int:  # if it's not int, double check the submissions
                try:
                    form_details[form_index]['lastNumberRecordsMills'] = int(form_details[form_index]['lastNumberRecordsMills'])
                except:
                    form_details[form_index]['lastNumberRecordsMills'] = 0
            formId = form_details[form_index]['formId']
            old_submission_count = form_details[form_index]['lastNumberRecordsMills']
            new_submission_count = number_submissions(base_url, aut, projectId, formId)
            # If there are new submissions, get the submission ids that are missing
            if new_submission_count - old_submission_count > 0:
                print('New Submissions!')
                new_sub_ids = get_new_sub_ids(table='Submissions', formId=formId, odk_details_column='instanceId', local_column='__id')
                if len(new_sub_ids) + old_submission_count != new_submission_count:
                    print('Warning: the number of new submissions does not match')
                # Retrieve the missing submissions by fetching the form
                fetch_odk_csv(base_url, aut, projectId, formId, table='Submissions', sort_column = '__id')
                fetch_odk_csv(base_url, aut, projectId, formId, table='Submissions.machines.machine', sort_column = '__Submissions-id')
                # todo: find out if it is possible to get the submissions based on ids, and append them to the existing csv
            # Update form_config file
            form_details[form_index]['lastNumberRecordsMills'] = new_submission_count
            form_details[form_index]['lastChecked'] = time.localtime(time.time())
            update_form_config_file(form_details)

sched = BackgroundScheduler(daemon=True)
sched.add_job(check_new_submissions_odk, 'interval', seconds=300)
sched.start()
atexit.register(lambda: sched.shutdown())

def read_local_tables_together(folder):
    """
    Read all the csv files in a folder and combine them together
    Returns a list a dictionaries
    """
    path = os.path.join(submission_files_path, folder)
    form_names = os.listdir(path)
    # Combine the files together
    form_data = list()
    for form in form_names:
        start_time = time.perf_counter()
        file = list()
        table_path = os.path.join(path, form)
        with open(table_path, newline='') as data_file:
            csv_file = csv.DictReader(data_file)
            for row in csv_file:
                # transform the coordinates from a string to a list
                try:
                    row['Location_mill_gps_coordinates'] = row['Location_mill_gps_coordinates'][1:-1].split(',')
                except:
                    next
                file.append(row)
        data_file.close()
        form_data.append(file)
        form_reader_time = time.perf_counter()
        print(f'Fetched table {form} in {form_reader_time - start_time}s')
    return [item for elem in form_data for item in elem]

@app.route('/file_names', methods=['POST'])
def get_main_tables():
    folder = 'mills'
    path = os.path.join(submission_files_path, folder)
    form_names = os.listdir(path)
    return json.dumps(form_names)

@app.route('/mills')
def mills():
    # Read the data
    mills = read_local_tables_together(folder='Submissions')
    return json.dumps(mills)


@app.route('/machines')
def machines():
    machines = read_local_tables_together(folder='Submissions.machines.machine')
    return json.dumps(machines)

@app.route('/get_merged_dictionaries')
def get_merged_dictionaries():
    start_time = time.perf_counter()
    machines = read_local_tables_together(folder='Submissions.machines.machine')
    mills = read_local_tables_together(folder='Submissions')
    reading_local_tables_time = time.perf_counter()
    print(f'Read local tables in {reading_local_tables_time - start_time}s')
    machine_i = 0
    start_time = time.perf_counter()
    for i in range(len(mills)):
        number_machines = int(mills[i]['machines_machine_count'])
        machine_list = list()
        for j in range(number_machines):
            machine_list.append(machines[machine_i])
            machine_i += 1
        mills[i]['machines'] = machine_list
    merging_time = time.perf_counter()
    print(f'Merged tables together in {merging_time - start_time}s')
    return json.dumps(mills)
    #
    # start_time = time.perf_counter()
    # machines_response = \
    #     odata_submissions(base_url,
    #                       aut,
    #                       projectId,
    #                       formId,
    #                       table='Submissions.machines.machine')
    # machine_fetch_time = time.perf_counter()
    # machines = machines_response.json()['value']
    # flatmachines = [flatten_dict(mach) for mach in machines]
    # print(f'Fetched machines in {machine_fetch_time - start_time}s')
    #
    # # open a file for writing
    # data_file = open('app/submission_files/machines.csv', 'w')
    # # create the csv writer object
    # csv_writer = csv.writer(data_file)
    # # Counter variable used for writing
    # # headers to the CSV file
    # count = 0
    # for emp in flatmachines:
    #     if count == 0:
    #         # Writing headers of CSV file
    #         header = emp.keys()
    #         csv_writer.writerow(header)
    #         count += 1
    #     # Writing data of CSV file
    #     csv_writer.writerow(emp.values())
    # data_file.close()
    # return json.dumps(flatmachines)


@app.route('/sites')
def sites():
    import concurrent.futures
    results = []
    with concurrent.futures.ThreadPoolExecutor() as ex:
        futures = [mills, machines]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())


@app.route('/mill_points')
def mill_points():
    start_time = time.perf_counter()
    submissions = odata_submissions(base_url, aut, projectId, formId, table='Submissions')
    submissions_machine = odata_submissions(base_url,
                                            aut, projectId, formId, table='Submissions.machines.machine')
    requests_complete_time = time.perf_counter()
    submissions_table = pd.DataFrame(submissions.json()['value'])
    submissions_machine_table = \
        pd.DataFrame(submissions_machine.json()['value'])
    pd_df_complete_time = time.perf_counter()
    charts(submissions_machine.json()['value'], submissions.json()['value'])
    charts_complete_time = time.perf_counter()

    # Dataframe with nested dictionaries to flat dictionary
    submissions_table = nested_dictionary_to_df(submissions_table)
    submissions_machine_table = \
        nested_dictionary_to_df(submissions_machine_table)
    submissions_all = submissions_table.merge(submissions_machine_table,
                                              left_on='__id',
                                              right_on='__Submissions-id')
    tables_to_flat_complete_time = time.perf_counter()

    mill_filter_list = ['mill_owner', 'flour_fortified', 'flour_fortified_standard']
    machine_filter_list = ['commodity_milled',
                           'mill_type', 'operational_mill',
                           'non_operational', 'energy_source']
    mill_filter_selection = get_filters(mill_filter_list, submissions_all)
    machine_filter_selection = get_filters(machine_filter_list,
                                           submissions_all)
    get_filters_complete_time = time.perf_counter()
    submissions_table_filtered_machine = \
        submissions_machine_table.to_dict(orient='index')
    submissions_filtered_dict = submissions_table.to_dict(orient='index')
    # submissions_table_filtered_dict = json.loads(submissions_table_filtered)
    # Make submissions_table_filtered into dictionary of dictionaries
    # with machine information nested within
    submissions_dict = submissions_filtered_dict
    for submission_id in submissions_dict:
        submissions_dict[submission_id]['machines'] = {}
        for machine_index in submissions_table_filtered_machine:
            machine_submission_id = \
                submissions_table_filtered_machine[machine_index] \
                    ['__Submissions-id']
            machine_id = \
                submissions_table_filtered_machine[machine_index]['__id']
            if machine_submission_id == submission_id:
                submissions_dict[submission_id]['machines'][machine_index] = \
                    submissions_table_filtered_machine[machine_index]
    submissions_filtered_json = json.dumps(submissions_dict)

    to_json_complete_time = time.perf_counter()
    print(f'Requests are complete at {requests_complete_time - start_time}s,' \
          f'pandas dataframes are complete at '
          f'{pd_df_complete_time - requests_complete_time}s, charts are complete' \
          f'at {charts_complete_time - pd_df_complete_time}s, tables are flat ' \
          f'in {tables_to_flat_complete_time - charts_complete_time}s, got ' \
          f'filters in ' \
          f'{get_filters_complete_time - tables_to_flat_complete_time}s, ' \
          f'and to_json in {to_json_complete_time - get_filters_complete_time}s')
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


@app.route('/filterform', methods=['GET', 'POST'])
def filter_data():
    if request.method == 'POST':
        choices = request.form
        choices_dict = {}
        for choice in choices:
            choice_element = choice.split(", ")[0]
            if choice_element not in choices_dict:
                choices_dict[choice_element] = []
            choices_dict[choice_element].append(choice.split(", ")[1])

            submissions = odata_submissions(base_url, aut, projectId, formId, table='Submissions')
            submissions_machine = odata_submissions(base_url, aut, projectId, formId,
                                                    table='Submissions.machines.machine')
            # charts(submissions_machine.json()['value'],
            #       submissions.json()['value'])
            submissions_table = \
                pd.DataFrame(odata_submissions_table(base_url, aut,
                                                     projectId, formId,
                                                     'Submissions')['value'])
            submissions_machine_table = \
                pd.DataFrame(odata_submissions_table(base_url, aut, \
                                                     projectId, formId,
                                                     'Submissions.machines.machine')['value'])
            # Dataframe with nested dictionaries to flat dictionary
            submissions_table = nested_dictionary_to_df(submissions_table)
            submissions_machine_table = \
                nested_dictionary_to_df(submissions_machine_table)
            submissions_all = \
                submissions_table.merge(submissions_machine_table,
                                        left_on='__id',
                                        right_on='__Submissions-id')
            mill_filter_list = ['mill_owner', 'flour_fortified',
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
                submissions_machine_table.to_dict(orient='index')
            # submissions_table_filtered_machine_dict = \
            #    json.loads(submissions_table_filtered_machine)
            # {k: [d[k] for d in dicts] for k in dicts[0]}

            # Filtering based on the form for the mill
            # if all the selections have been deselected from one category
            for mill_key in mill_filter_selection:
                if mill_key not in list(choices_dict.keys()):
                    submissions_table.drop(submissions_table.index, inplace=True)
            # filter based on the choices
            for dict_key, dict_values in zip(list(choices_dict.keys()), list(choices_dict.values())):
                if dict_key in submissions_table.columns:
                    submissions_table[dict_key] = \
                        list(map(str, list(submissions_table[dict_key])))
                    submissions_table = \
                        submissions_table.loc[submissions_table[dict_key].isin(dict_values)]
                submissions_table.set_index('__id', inplace=True)
                submissions_filtered_dict = \
                    submissions_table.to_dict(orient='index')
                # submissions_table_filtered_dict = \
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
                               submissions_filtered=submissions_filtered_json,
                               mill_filter_selection=mill_filter_selection,
                               title='Map', choices_dict=choices_dict)


@app.route('/download_data/')
def export_data():
    # Export all the data from ODK form
    r = export_submissions(base_url, aut, projectId, formId)
    file_name = formId
    if not os.path.exists('files'):
        outdir = os.makedirs('files')

        # Saves the file also locally
        with open(f'files/{file_name}.zip', 'wb') as zip:
            zip.write(r.content)
    basename = os.path.basename(f'files/{file_name}.zip')
    dirname = os.path.dirname(os.path.abspath(f'files/{file_name}.zip'))
    send_from_directory(dirname, basename, as_attachment=True)

    # Stream the response as the data is generated
    response = Response(r.content, content_type='zip')
    response.headers.set("Content-Disposition", "attachment",
                         filename=f"{file_name}.zip")
    return response
