from flask import Flask, request, redirect
from flask import render_template
from .forms import LoginForm
import json	
import requests
import secrets

# Generate a secure random secret key
secret_key = secrets.token_hex(16)

SALESFORCE_CONSUMER_KEY = '3MVG9DREgiBqN9WmkvM3yN3IVuL3AVGBSmf7SjpjZ3P6Za55OmT8i0VFDNK8t_vd9Dhj_oRqp.qqYZUMne.8N'
SALESFORCE_CONSUMER_SECRET = 'ED6B772975C07C92B2F8EDDBC6C5F1E012C7ED30A54C04C00B27AB6C33FD4C27'
SALESFORCE_REDIRECT_URI = 'https://www.google.com/'

SALESFORCE_API_VERSION =55


app = Flask(__name__)

# Set the secret key
app.secret_key = secret_key

@app.route('/', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)

    if request.method == 'POST' and login_form.validate():
        # Get Production or Sandbox value
        environment = login_form.environment.data

        # URL to send login request
        oauth_url = 'https://login.salesforce.com/services/oauth2/authorize'
        if environment == 'Sandbox':
            oauth_url = 'https://test.salesforce.com/services/oauth2/authorize'

        # Set up URL based on Salesforce Connected App details
        oauth_url = f'{oauth_url}?response_type=code&client_id={SALESFORCE_CONSUMER_KEY}&redirect_uri={SALESFORCE_REDIRECT_URI}&state={environment}'
        
        # Redirect to the login page
        return redirect(oauth_url)

    return render_template('index.html', form=login_form)

@app.route('/oauthrp', methods=['GET', 'POST'])
def oauth_response(request):
	"""
		Controller for the oauth_response page.
	"""

	# Default variables
	error_exists = False
	error_message = ''
	username = ''
	org_name = ''
	org_id = ''
	email = ''

	# On page load
	if request.GET:

		# Get OAuth response  values
		oauth_code = request.GET.get('code') 
		environment = request.GET.get('state')
		access_token = ''
		instance_url = ''

		if 'Sandbox' in environment:
			login_url = 'https://test.salesforce.com'
		else:
			login_url = 'https://login.salesforce.com'
		
		# Log in to REST API to obtain access token
		r = requests.post(login_url + '/services/oauth2/token', headers={ 'content-type':'application/x-www-form-urlencoded'}, data={'grant_type':'authorization_code','client_id':SALESFORCE_CONSUMER_KEY,'client_secret':SALESFORCE_CONSUMER_SECRET,'redirect_uri': SALESFORCE_REDIRECT_URI,'code': oauth_code})
		
		# Load JSON response
		auth_response = json.loads(r.text)

		# If login error - return error for user
		if 'error_description' in auth_response:
			error_exists = True
			error_message = auth_response['error_description']

		# Otherwise get session details
		else:
			access_token = auth_response['access_token']
			instance_url = auth_response['instance_url']
			user_id = auth_response['id'][-18:]
			org_id = auth_response['id'][:-19]
			org_id = org_id[-18:]

			# get username of the authenticated user
			r = requests.get(instance_url + '/services/data/v' + str(SALESFORCE_API_VERSION) + '.0/sobjects/User/' + user_id + '?fields=Username,Email', headers={'Authorization': 'OAuth ' + access_token})
			query_response = json.loads(r.text)

			if 'Username' in query_response:
				username = query_response['Username']

			if 'Email' in query_response:
				email = query_response['Email']

			# get the org name of the authenticated user
			r = requests.get(instance_url + '/services/data/v' + str(SALESFORCE_API_VERSION) + '.0/sobjects/Organization/' + org_id + '?fields=Name', headers={'Authorization': 'OAuth ' + access_token})
			
			if 'Name' in json.loads(r.text):
				org_name = json.loads(r.text)['Name']

		login_form = LoginForm(initial={'environment': environment, 'access_token': access_token, 'instance_url': instance_url, 'org_id': org_id, 'username': username, 'org_name':org_name, 'email': email})	

	# Run after user selects logout or get schema
	
	return render_template(
        request, 
        'oauthrp.html', 
        {
            'error': error_exists, 
            'error_message': error_message, 
            'username': username, 
            'org_name': org_name, 
            'login_form': login_form
		}
	)