import json, csv

secret_tokens = json.load(open('secret_tokens.json', 'r'))
email = secret_tokens['email']
password = secret_tokens['password']
aut = (email, password)
base_url = 'https://omdtz-data.org'

mill_columns = ['__id', 'start', 'end', 'interviewee_mill_owner', 'mills_number_milling_machines',
                 'machines_machine_count', 'Packaging_flour_fortified',
                 'Packaging_flour_fortified_standard', 'Location_mill_gps_coordinates']
machine_columns = ['__id', '__Submissions-id', 'commodity_milled', 'mill_type', 'operational_mill',
                   'energy_source', 'img_machines']
columns = {'Submissions': mill_columns, 'Submissions.machines.machine':machine_columns}

submission_files_path = 'app/submission_files'
figures_path = 'app/static/figures'
update_time = 60 #time in seconds to check and update new submissions
id_columns = ['__id', '__Submissions-id']
# Get the form configured data
form_details = list()
with open('app/static/form_config.csv', newline='') as file:
    form_config = csv.DictReader(file)
    for row in form_config:
        form_details.append(row)
form_index = 0
projectId = form_details[form_index]['projectId']
formId = form_details[form_index]['formId']
lastNumberRecordsMills = form_details[form_index]['lastNumberRecordsMills']