from flask import render_template, send_file, send_from_directory, request


import requests, os
from werkzeug.wrappers import Response
import json
import pandas as pd

from app import app
from app.odk_requests import odata_submissions, export_submissions, odata_submissions_machine, odata_submissions_table
from app.helper_functions import get_filters, nested_dictionary_to_df
from app.graphics import count_items, unique_key_counts, charts

secret_tokens = json.load(open('secret_tokens.json', 'r'))
email = secret_tokens['email']
password = secret_tokens['password']
aut = (email, password)

base_url = 'https://omdtz-data.org'
projectId = 2 
formId = "Tanzania_Mills_Mapping_Census_V_01"

auth_values =json.dumps({
    "email": email,
    "password": password
  })	

headers = {
  'Content-Type': 'application/json'
}


session_info = requests.post(url = f'{base_url}/v1/sessions', data=auth_values, headers=headers)
session_token = session_info.json()['token']

headers = {
  'Authorization': session_token
}
url = f'{base_url}/v1/projects/'
r =requests.get(url, headers=headers)

def dict_to_df(dict):
	return df

@app.route('/')
@app.route('/index')
@app.route('/home')
def index():

	submissions = odata_submissions(base_url, aut, projectId, formId)
	submissions_machine = odata_submissions_machine(base_url, aut, projectId, formId)
	charts(submissions_machine.json()['value'], submissions.json()['value'])
	submissions_table =  pd.DataFrame(submissions.json()['value'])
	submissions_machine_table =  pd.DataFrame(submissions_machine.json()['value'])

	# Dataframe with nested dictionaries to flat dictionary
	submissions_table = nested_dictionary_to_df(submissions_table)
	submissions_machine_table = nested_dictionary_to_df(submissions_machine_table)
	submissions_all = submissions_table.merge(submissions_machine_table, left_on = '__id', right_on = '__Submissions-id')

	mill_filter_list = ['mill_owner','flour_fortified', 'flour_fortified_standard']
	machine_filter_list = ['commodity_milled', 'mill_type', 'operational_mill', 'non_operational', 'energy_source']
	mill_filter_selection = get_filters(mill_filter_list, submissions_all)
	machine_filter_selection = get_filters(machine_filter_list, submissions_all)

	submissions_table_filtered = submissions_table.to_json(orient = 'index')
	return render_template('index.html', submissions_filtered = submissions_table_filtered, mill_filter_selection = mill_filter_selection, machine_filter_selection = machine_filter_selection, title='Map')

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
		submissions_machine = odata_submissions_machine(base_url, aut, projectId, formId)
		#charts(submissions_machine.json()['value'], submissions.json()['value'])
		submissions_table =  pd.DataFrame(odata_submissions_table(base_url, aut, projectId, formId, 'Submissions')['value'])
		submissions_machine_table =  pd.DataFrame(odata_submissions_table(base_url, aut, projectId, formId, 'Submissions.machines.machine')['value'])

		# Dataframe with nested dictionaries to flat dictionary
		submissions_table = nested_dictionary_to_df(submissions_table)
		submissions_machine_table = nested_dictionary_to_df(submissions_machine_table)
		submissions_all = submissions_table.merge(submissions_machine_table, left_on = '__id', right_on = '__Submissions-id')



		# Filtering based on the form for machines
		for dict_key, dict_values in zip(list(choices_dict.keys()), list(choices_dict.values())):
			submissions_machine_table = submissions_machine_table.loc[submissions_all[dict_key].isin(dict_values)]
		submissions_table_filtered_machine = submissions_machine_table.to_dict(orient = 'index')
		#submissions_table_filtered_machine_dict = json.loads(submissions_table_filtered_machine)
		#{k: [d[k] for d in dicts] for k in dicts[0]}

		# Filtering based on the form for all
		for dict_key, dict_values in zip(list(choices_dict.keys()), list(choices_dict.values())):
			submissions_table_filtered = submissions_table.loc[submissions_table[dict_key].isin(dict_values)]
		submissions_table_filtered.set_index('__id', inplace=True)
		submissions_filtered_dict = submissions_table_filtered.to_dict(orient='index')
		#submissions_table_filtered_dict = json.loads(submissions_table_filtered)

		# Make submissions_table_filtered into dictionary of dictionaries with machine information nested within
		submissions_dict = submissions_filtered_dict
		for submission_id in submissions_dict:
			for machine_index in submissions_table_filtered_machine:
				machine_submission_id = submissions_table_filtered_machine[machine_index]['__Submissions-id']
				machine_id = submissions_table_filtered_machine[machine_index]['__id']
				if machine_submission_id == submission_id:
					submissions_dict[submission_id][machine_id] = submissions_table_filtered_machine[machine_index]

		submissions_filtered_json = json.dumps(submissions_dict)


		#print(submissions_table_filtered_machine.head())

		mill_filter_list = ['mill_owner','flour_fortified', 'flour_fortified_standard']
		machine_filter_list = ['commodity_milled', 'mill_type', 'operational_mill', 'non_operational', 'energy_source']
		mill_filter_selection = get_filters(mill_filter_list, submissions_table)
		#machine_filter_selection = get_filters(machine_filter_list, submissions_all)


	return render_template('index.html', submissions_filtered = submissions_filtered_json, mill_filter_selection = mill_filter_selection, title='Map', choices_dict = choices_dict)
	#return render_template('filterform.html', choices = choices)

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
	response.headers.set("Content-Disposition", "attachment", filename=f"{file_name}.zip")
	return response

