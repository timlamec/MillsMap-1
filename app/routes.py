from flask import render_template, send_file, send_from_directory, request
from app import app
from app.odk_requests import odata_submissions, export_submissions, odata_submissions_machine, odata_submissions_table
from flask_wtf import FlaskForm
from wtforms import SubmitField
import requests, os
from werkzeug.wrappers import Response
import json
from app.graphics import count_items, unique_key_counts, charts
import pandas as pd
from pandas.io.json import json_normalize

secret_tokens = json.load(open('secret_tokens.json', 'r'))
email = secret_tokens['email']
password = secret_tokens['password']
aut = (email, password)

base_url = 'https://omdtz-data.org'
projectId = 2 
formId = "Tanzania_Mills_Mapping_Census_V_01"

values =json.dumps({
    "email": email,
    "password": password
  })

headers = {
  'Content-Type': 'application/json'
}


session_info = requests.post(url = f'{base_url}/v1/sessions', data=values, headers=headers)
session_token = session_info.json()['token']

headers = {
  'Authorization': session_token
}
url = f'{base_url}/v1/projects/'
r =requests.get(url, headers=headers)


submissions = odata_submissions(base_url, aut, projectId, formId)
submissions_machine = odata_submissions_machine(base_url, aut, projectId, formId)
submissions_len = len(submissions.json()['value'])
charts(submissions_machine.json()['value'], submissions.json()['value'])
submissions_table =  pd.DataFrame(odata_submissions_table(base_url, aut, projectId, formId, 'Submissions')['value'])
submissions_machine_table =  pd.DataFrame(odata_submissions_table(base_url, aut, projectId, formId, 'Submissions.machines.machine')['value'])
dictionary_columns = []
while True:
	data_types = []
	for col in submissions_table:
		data_types.append(type(submissions_table[col][0]))
	if dict not in data_types:
		break
	for col in submissions_table:
		if (type(submissions_table[col][0])) == dict:
			dictionary_columns.append(col)
			submissions_table = pd.concat([submissions_table.drop(col, axis=1), submissions_table[col].apply(pd.Series)], axis=1)
#submissions_table.to_csv('submissions_table.csv')


dictionary_columns = []
while True:
	data_types = []
	for col in submissions_machine_table:
		data_types.append(type(submissions_machine_table[col][0]))
	if dict not in data_types:
		break
	for col in submissions_machine_table:
		if (type(submissions_machine_table[col][0])) == dict:
			dictionary_columns.append(col)
			submissions_machine_table = pd.concat([submissions_machine_table.drop(col, axis=1), submissions_machine_table[col].apply(pd.Series)], axis=1)
#submissions_machine_table.to_csv('submissions_machine_table.csv')

submissions_all = submissions_table.merge(submissions_machine_table, left_on = '__id', right_on = '__Submissions-id')

# def merge_dicts(a, b, path = None):
# 	"merges b into a"
# 	a = a['value']
# 	b = b['value']
# 	print(b)
# 	if path is None: path = []
# 	for key in b:
# 		if key in a:
# 			if isinstance(a[key], dict) and isinstance(b[key], dict):
# 				print(key)
# 				merge(a[key], b[key], path + [str(key)])
# 			elif a[key] == b[key]:
# 				print(key)
# 				pass # same leaf value
# 			else:
# 				raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
# 		else:
# 			print(key)
# 			a[key] = b[key]
# 	return a


@app.route('/')
@app.route('/index')
@app.route('/home')
def index():
	filter_selection_dict = {} 
	filter_selections = ['mill_owner', 'commodity_milled', 'mill_type', 'operational_mill', 'non_operational', 'energy_source', 'flour_fortified', 'flour_fortified_standard']
	unique_values_filters = []
	filter_columns = submissions_all.loc[:,filter_selections]

	for col in filter_columns:
		values_list = []
		values_list = filter_columns.loc[:,col].str.split()
		unique_values_list =[]
		for item in (values_list):
			if type(item) == list:
				for sub_item in item:
					if sub_item not in unique_values_list:
						unique_values_list.append(sub_item)
			else:
				if sub_item not in unique_values_list:
					unique_values_list.append(sub_item)
		filter_selection_dict[col] = unique_values_list
		unique_values_filters.append(unique_values_list)
		print(filter_selection_dict)
	return render_template('index.html', filter_selection_dict = filter_selection_dict, submissions_len = submissions_len, submissions=submissions.json(), submissions_machine = submissions_machine.json(), title='Map')

@app.route('/filterform', methods = ['GET', 'POST'])
def filter_data():
	print('jee filterform')
	if request.method == 'POST':
		choices = request.form
		print(choices)
		print('jee FILTERFORM')
	return render_template('filterform.html', choices = choices)

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


@app.route('/plot.png')
def plot_png():
    fig = create_figure()
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

def create_figure():
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    xs = range(100)
    ys = [random.randint(1, 50) for x in xs]
    axis.plot(xs, ys)
    return fig

