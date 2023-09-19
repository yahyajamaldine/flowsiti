from flask import Flask, request, redirect, jsonify, url_for
from flask import render_template
from .forms import LoginForm
import json
import requests
from suds.client import Client
import ssl
import secrets

# Generate a secure random secret key
secret_key = secrets.token_hex(16)

#Since I had to implement a self-signed ssl certifcate for the web server 
#Python doesn't trust it
#To resolve this issue when dealing with a self-signed certificate, you have a few options:
"""Disable SSL Verification
   #This solution is not recommeneded for production(security issuess)
   #once fixing everthing this code will line must be deleted
   #ssl._create_default_https_context = ssl._create_unverified_context
"""
ssl._create_default_https_context = ssl._create_unverified_context

SALESFORCE_CONSUMER_KEY = '3MVG9DREgiBqN9WmkvM3yN3IVuL3AVGBSmf7SjpjZ3P6Za55OmT8i0VFDNK8t_vd9Dhj_oRqp.qqYZUMne.8N'
SALESFORCE_CONSUMER_SECRET = 'ED6B772975C07C92B2F8EDDBC6C5F1E012C7ED30A54C04C00B27AB6C33FD4C27'
SALESFORCE_REDIRECT_URI = 'https://13.37.66.143/oauthrp'

SALESFORCE_API_VERSION =58

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
def oauth_response():
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
    if request.method == 'GET':

        # Get OAuth response values
        oauth_code = request.args.get('code')
        environment = request.args.get('state')
        access_token = ''
        instance_url = ''

        if 'Sandbox' in environment:
            login_url = 'https://test.salesforce.com'
        else:
            login_url = 'https://login.salesforce.com'

        # Log in to REST API to obtain access token
        r = requests.post(login_url + '/services/oauth2/token', headers={'content-type': 'application/x-www-form-urlencoded'}, data={'grant_type': 'authorization_code', 'client_id': SALESFORCE_CONSUMER_KEY, 'client_secret': SALESFORCE_CONSUMER_SECRET, 'redirect_uri': SALESFORCE_REDIRECT_URI, 'code': oauth_code})

        # Load JSON response
        auth_response = json.loads(r.text)

        # If login error - return error for the user
        if 'error_description' in auth_response:
            error_exists = True
            error_message = auth_response['error_description']

        # Otherwise, get session details
        else:
            access_token = auth_response['access_token']
            instance_url = auth_response['instance_url']
            user_id = auth_response['id'][-18:]
            org_id = auth_response['id'][:-19]
            org_id = org_id[-18:]

            # Get username of the authenticated user
            r = requests.get(instance_url + '/services/data/v' + str(SALESFORCE_API_VERSION) + '.0/sobjects/User/' + user_id + '?fields=Username,Email', headers={'Authorization': 'OAuth ' + access_token})
            query_response = json.loads(r.text)

            if 'Username' in query_response:
                username = query_response['Username']

            if 'Email' in query_response:
                email = query_response['Email']

            # Get the org name of the authenticated user
            r = requests.get(instance_url + '/services/data/v' + str(SALESFORCE_API_VERSION) + '.0/sobjects/Organization/' + org_id + '?fields=Name', headers={'Authorization': 'OAuth ' + access_token})

            if 'Name' in json.loads(r.text):
                org_name = json.loads(r.text)['Name']

        login_form = LoginForm(environment=environment, access_token=access_token, instance_url=instance_url, org_id=org_id, username=username, org_name=org_name, email=email)

        return render_template('oauthrp.html', error=error_exists, error_message=error_message,
                               username=username, org_name=org_name, login_form=login_form)

    # POST method to get objects
    if request.method == 'POST' and 'get_metadata' in request.form:

        login_form = LoginForm(request.form)
        environment = login_form.environment.data
        access_token = login_form.access_token.data
        instance_url = login_form.instance_url.data
        org_id = login_form.org_id.data
        login_form = LoginForm(environment=environment, access_token=access_token, instance_url=instance_url,org_id = org_id)
        #You can now use these variables as needed
		#The list of standard objects that support custom fields
		#https://www.salesforce.com/us/developer/docs/object_reference/Content/sforce_api_objects_custom_objects.html
		# Define the list of supported standard objects
        supported_standard_objects = [
             'Account',
             'Asset',
             'Campaign',
             'CampaignMember',
             'Case',
             'Contact',
             'Contract',
             'Event',
             'Lead',
             'Opportunity',
             'OpportunityCompetitor',
             'OpportunityLineItem',
             'Order',
             'OrderItem',
             'Pricebook2',
             'PricebookEntry',
             'Product2',
             'Quote',
             'QuoteLineItem',
             'Task',
             'User',
             'WorkOrder',
             'WorkOrderLineItem',]
        request_url = instance_url + '/services/data/v' + str(SALESFORCE_API_VERSION) + '.0/'
        headers = {
			'Accept': 'application/json',
			'X-PrettyPrint': '1',
			'Authorization': 'Bearer ' + access_token
		}

        custom_objects_infos = []
        custom_objects = requests.get(request_url + 'sobjects', headers=headers).json()['sobjects']

        for record in custom_objects:
          custom_object_info = {
            'label': record['label'],
            'name': record['name'],
          }
          custom_objects_infos.append(custom_object_info)

        # Now, custom_objects is a list of dictionaries representing CustomObject instances
        return render_template('org_infos.html',
                               login_form=login_form,
                               custom_object =  custom_objects_infos
                               )
    if request.method == 'POST' and 'insert_object' in request.form:

        login_form = LoginForm(request.form)
        environment = login_form.environment.data
        access_token = login_form.access_token.data
        instance_url = login_form.instance_url.data
        org_id= login_form.org_id.data
        #Custom Object data
        objectfullName = request.form.get('object_full_name')
        label = request.form.get('label')
        metadata_client = Client('https://13.37.66.143/static/metadata-52.xml')
        metadata_url = instance_url + '/services/Soap/m/' +'52.0/'
        session_header = metadata_client.factory.create("SessionHeader")
        session_header.sessionId = access_token
        metadata_client.set_options(location=metadata_url, soapheaders=session_header)

        custom_object = metadata_client.factory.create("CustomObject")
        custom_object.fullName = objectfullName +'__c'
        custom_object.label = label
        custom_object.pluralLabel = 'Flowsits'
        custom_object.nameField =  metadata_client.factory.create("CustomField")
        custom_object.nameField.type = 'Text'
        custom_object.nameField.label = 'Flowsiti Record'
        custom_object.deploymentStatus = 'Deployed'
        custom_object.sharingModel = 'ReadWrite'
        try:

            result = metadata_client.service.createMetadata([custom_object])

            if result[0].success:

                page_response = {
						'success': True,
						'errorCode': None,
						'message': 'Successfully created Object.'
					}

            else:
                    page_response = {
						'success': False,
						'errorCode': result[0].errors[0].statusCode,
						'message': result[0].errors[0].message
					}

				# Return the POST response
            return render_template('client.html',custom_object = json.dumps(page_response))

        except Exception as ex:

                page_response = {
					'success': False,
					'errorCode': 'Error building field metadata',
					'message': ex
				}

                return render_template('client.html',custom_object = json.dumps(page_response))
        

@app.route('/sclient', methods=['GET', 'POST'])
def sclient(): 
    if request.method == "GET":
        metadata_client = Client('http://purple-meadow-4fe551fde8804864b775979f53be8a42.azurewebsites.net/static/metadata-52.xml')
        metadata_url = 'https://resilient-fox-bv8mag-dev-ed.trailblaze.my.salesforce.com' + '/services/Soap/m/' +'52.0/'
        session_header = metadata_client.factory.create("SessionHeader")
        session_header.sessionId = '00D8d00000Aqcl0!ARUAQGuZK25CkICQMcMkuFUbTIDU1ajvZ3Vo_yTbqPIz.Az9jzhEL0OJpudAc4H4X4DPYMVOiUeZCkGqDwd0_yYC.h9gG4Gi'
        metadata_client.set_options(location=metadata_url, soapheaders=session_header)

        custom_object=  metadata_client.factory.create("CustomObject")
        custom_object.fullName = 'travel__c'
        custom_object.label = 'travel'
        custom_object.pluralLabel = 'travel'
        custom_object.nameField =  metadata_client.factory.create("CustomField")
        custom_object.nameField.type = 'Text'
        custom_object.nameField.label = 'Flowsi Record'
        custom_object.deploymentStatus = 'Deployed'
        custom_object.sharingModel = 'ReadWrite'
    
        try:

            result = metadata_client.service.createMetadata([custom_object])

            if result[0].success:

                page_response = {
						'success': True,
						'errorCode': None,
						'message': 'Successfully created field.'
					}

            else:
                    page_response = {
						'success': False,
						'errorCode': result[0].errors[0].statusCode,
						'message': result[0].errors[0].message
					}

				# Return the POST response
            return str(page_response)

        except Exception as ex:

                page_response = {
					'success': False,
					'errorCode': 'Error building field metadata',
					'message': ex
				}

                return str(page_response)
        
     


