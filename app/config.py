import json, csv
from app.form_specific_data import mill_columns, machine_columns, columns, array_columns, single_columns, base_url

# TODO: move this to someplace more ovbiously
# related to the form-specific information
# because it'll change with different projects
secret_tokens = json.load(open('secret_tokens.json', 'r'))
email = secret_tokens['email']
password = secret_tokens['password']
aut = (email, password)

submission_files_path = 'app/submission_files'
figures_path = 'app/static/figures'
update_time = 60 #time in seconds to check and update new submissions
id_columns = ['__id', '__Submissions-id']
# Get the form configured data
# TODO: Do not create the form config file on the fly.
# This should be a database table ideally.
form_details = list()
with open('app/static/form_config.csv', newline='') as file:
    form_config = csv.DictReader(file)
    for row in form_config:
        form_details.append(row)
form_index = 0
projectId = form_details[form_index]['projectId']
formId = form_details[form_index]['formId']
lastNumberRecordsMills = form_details[form_index]['lastNumberRecordsMills']

#hardcoded from form

#hardcoded from form

