from flask import render_template, send_file, send_from_directory
from app import app
from app.odk_requests import odata_submissions, export_submissions, odata_submissions_machine
from flask_wtf import FlaskForm
from wtforms import SubmitField
import requests, os
from werkzeug.wrappers import Response
import json
import matplotlib.pyplot as plt

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

def count_items(dictionary, value, key1, key2 = None):
	count = 0
	if key2 != None:
		for item in dictionary:
		    if item[key1][key2] == value:
		        count += 1
	else: 
		for item in dictionary:
		    if item[key1] == value:
		        count += 1
	return count

def unique_key_counts(dictionary, key1, key2 = None):
	values = []
	if key2 != None:
		for item in dictionary:
		    values.append(item[key1][key2])
	else: 
		for item in dictionary:
		    values.append(item[key1])
	unique_values = list(set(values))
	value_counts = []
	for unique_value in unique_values:
		value_counts.append(count_items(dictionary, unique_value, key1, key2))
	return unique_values, value_counts


def charts(submissions_machine, submissions):
	operational_count = count_items(submissions_machine, key1 = 'operational_mill', value = 'yes')
	not_operational_count = count_items(submissions_machine, key1 = 'operational_mill', value = 'no')
	labels = 'Operational', 'Not operational'
	colors = ['#6495ED', '#EEDC82']
	sizes = [operational_count, not_operational_count]
	explode = (0, 0.03)  # only "explode" the 2nd slice (i.e. 'Hogs')

	fig, ax1 = plt.subplots()
	ax1.pie(sizes, labels=labels, explode = explode, colors=colors, autopct='%1.1f%%',
	        shadow=False, startangle=90)
	ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
	if not os.path.exists('app/static/figures'):
		outdir = os.makedirs('app/static/figures')
	fig.savefig('app/static/figures/piechart.jpg', bbox_inches='tight')   # save the figure to file
	plt.close(fig)   

	#Mill types
	mill_types, mill_type_counts = unique_key_counts(submissions_machine, key1 = 'mill_type')
	fig1, ax1 = plt.subplots()
	plt.barh(mill_types, mill_type_counts, align='center')
	for s in ['top', 'bottom', 'left', 'right']:
	    ax1.spines[s].set_visible(False)
	ax1.xaxis.set_ticks_position('none')
	ax1.yaxis.set_ticks_position('none')
	ax1.grid(b = True, color ='grey',
        linestyle ='-.', linewidth = 0.5,
        alpha = 0.2)
	ax1.invert_yaxis()
	# Add annotation to bars
	for i in ax1.patches:
	    plt.text(i.get_width()+0.2, i.get_y()+0.5,
	             str(round((i.get_width()), 2)),
	             fontsize = 10, fontweight ='bold',
	             color ='grey')
	fig1.savefig('app/static/figures/barplot.jpg', bbox_inches='tight')   # save the figure to file
	plt.close(fig)   

	#types of grains
	grain_types, grain_type_counts = unique_key_counts(submissions_machine, key1 = 'commodity_milled')
	fig2, ax2 = plt.subplots()
	plt.barh(grain_types, grain_type_counts, align='center')
	for s in ['top', 'bottom', 'left', 'right']:
	    ax2.spines[s].set_visible(False)
	ax2.xaxis.set_ticks_position('none')
	ax2.yaxis.set_ticks_position('none')
	ax2.grid(b = True, color ='grey',
        linestyle ='-.', linewidth = 0.5,
        alpha = 0.2)
	ax2.invert_yaxis()
	# Add annotation to bars
	for i in ax2.patches:
	    plt.text(i.get_width()+0.2, i.get_y()+0.5,
	             str(round((i.get_width()), 2)),
	             fontsize = 10, fontweight ='bold',
	             color ='grey')
	fig2.savefig('app/static/figures/barplot_commodity_milled.jpg', bbox_inches='tight')   # save the figure to file
	plt.close(fig)  

	#Flour fortification
	fortify_types, fortify_type_counts = unique_key_counts(submissions, key1 = 'Packaging', key2 = 'flour_fortified')
	fig2, ax2 = plt.subplots()
	plt.barh(fortify_types, fortify_type_counts, align='center')
	for s in ['top', 'bottom', 'left', 'right']:
	    ax2.spines[s].set_visible(False)
	ax2.xaxis.set_ticks_position('none')
	ax2.yaxis.set_ticks_position('none')
	ax2.grid(b = True, color ='grey',
        linestyle ='-.', linewidth = 0.5,
        alpha = 0.2)
	ax2.invert_yaxis()
	# Add annotation to bars
	for i in ax2.patches:
	    plt.text(i.get_width()+0.2, i.get_y()+0.5,
	             str(round((i.get_width()), 2)),
	             fontsize = 10, fontweight ='bold',
	             color ='grey')
	fig2.savefig('app/static/figures/barplot_flour_fortified.jpg', bbox_inches='tight')   # save the figure to file
	plt.close(fig)  





@app.route('/')
@app.route('/index')
@app.route('/home')
def index():
	submissions = odata_submissions(base_url, aut, projectId, formId)
	submissions_machine = odata_submissions_machine(base_url, aut, projectId, formId)
	submissions_len = len(submissions.json()['value'])
	charts(submissions_machine.json()['value'], submissions.json()['value'])

	#merged_dict = merge_dicts(submissions.json(), submissions_machine.json())
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

