from flask import render_template, send_file, send_from_directory
from app import app
from app.odk_requests import odata_submissions, export_submissions, odata_submissions_machine
from flask_wtf import FlaskForm
from wtforms import SubmitField
import requests, os
from werkzeug.wrappers import Response
import json


secret_tokens = json.load(open('secret_tokens.json', 'r'))
email = secret_tokens['email']
password = secret_tokens['password']
aut = (email, password)

base_url = 'https://omdtz-data.org'
projectId = 2 
formId = "Tanzania Mills Mapping Census Form_V2"

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

@app.route('/')
@app.route('/index')
@app.route('/home')
def index():
	submissions = odata_submissions(base_url, aut, projectId, formId)
	submissions_machine = odata_submissions_machine(base_url, aut, projectId, formId)
	submissions_len = len(submissions.json()['value'])
	return render_template('index.html', submissions_len = submissions_len, submissions=submissions.json(), submissions_machine = submissions_machine.json(), title='Map')


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
