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

	return render_template('index.html', title='Map')

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

