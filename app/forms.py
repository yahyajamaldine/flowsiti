from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, validators
from wtforms.validators import InputRequired
from suds.client import Client

class LoginForm(FlaskForm):
	environment = SelectField('environment', choices=[('Production', 'Production'), ('Developer', 'Developer'), ('Sandbox', 'Sandbox')], validators=[InputRequired()])
	access_token = StringField(validators=[validators.Optional()])
	instance_url = StringField(validators=[validators.Optional()])
	username = StringField(validators=[validators.Optional()])
	email = StringField(validators=[validators.Optional()])
	org_name = StringField(validators=[validators.Optional()])
	org_id = StringField(validators=[validators.Optional()])

def buildFields(field, metadata, objectName):
	"""
	Build the field metadata for the Metadata API, after we are going to use 
	"""
	#Creating a custom field using metadata API
	# Clear out all the fields that cause deployment issues when resolved to blank strings
	# So explicity need to be set to None/Null
	fieldMetadata = metadata.factory.create("CustomField")
	fieldMetadata.deleteConstraint = None
	fieldMetadata.fieldManageability = None
	fieldMetadata.maskChar = None
	fieldMetadata.maskType = None
	fieldMetadata.formulaTreatBlanksAs = None
	fieldMetadata.securityClassification = None
	fieldMetadata.summaryOperation = None

	#field values based on user Input

	fieldMetadata.label = field.get('field_label')
	fieldMetadata.fullName = objectName +'__c' + '.' + field.get('field_name') +'__c'
	
	fieldMetadata.inlineHelpText ='add Helptext'
	fieldMetadata.description = 'add Helptext'
	fieldMetadata.type = field.get('field_type')
	
	if fieldMetadata.type == 'Checkbox':
		fieldMetadata.defaultValue = False

	elif fieldMetadata.type == 'Currency':

		fieldMetadata.defaultValue = 0
		fieldMetadata.precision = 10
		fieldMetadata.scale = 4
		fieldMetadata.required = True
	
	elif fieldMetadata.type == 'Email':

		fieldMetadata.externalId = False
		fieldMetadata.required = True
		fieldMetadata.unique = False
		

	elif fieldMetadata.type == 'Date' or fieldMetadata.type == 'DateTime' or fieldMetadata.type == 'Phone' or fieldMetadata.type == 'TextArea' or fieldMetadata.type == 'Url':
		fieldMetadata.required = True
	
	elif fieldMetadata.type== 'Location':
		fieldMetadata.required = True
		fieldMetadata.scale = 18

	elif fieldMetadata.type == 'Number':

		fieldMetadata.externalId = False
		fieldMetadata.precision = 10
		fieldMetadata.scale = 4
		fieldMetadata.defaultValue=0
		fieldMetadata.required = False
		fieldMetadata.unique = False
		   
	elif fieldMetadata.type == 'Percent':

		fieldMetadata.precision = 10
		fieldMetadata.defaultValue= '10'
		fieldMetadata.scale = 2
		fieldMetadata.precision = 10	
		fieldMetadata.required = False
		fieldMetadata.unique = False 

	elif fieldMetadata.type == 'Text':
		
		fieldMetadata.length = 80
		fieldMetadata.externalId = False
		fieldMetadata.required = False
		fieldMetadata.unique = False   

	elif fieldMetadata.type == 'Picklist':
		fieldMetadata.valueSet = metadata.factory.create("ValueSet")
		fieldMetadata.valueSet.valueSetDefinition = build_picklist_values_metadata(field,metadata)

	elif fieldMetadata.type == 'MultiselectPicklist':

		fieldMetadata.valueSet = metadata.factory.create("ValueSet")
		fieldMetadata.visibleLines = 4
		fieldMetadata.valueSet.valueSetDefinition = build_picklist_values_metadata(field, metadata)
	
	elif fieldMetadata.type == 'LongTextArea':
	
		fieldMetadata.length = 80
		fieldMetadata.defaultValue = ''
		fieldMetadata.visibleLines = 4
		fieldMetadata.required = False
	
	elif fieldMetadata.type == 'Html':
		fieldMetadata.length = 100
		fieldMetadata.defaultValue = '<html></html>'
		fieldMetadata.visibleLines = 40
		fieldMetadata.required = False

	elif fieldMetadata.type == 'EncryptedText':

		fieldMetadata.length = 80
		fieldMetadata.required = False
		fieldMetadata.maskChar = 'asterisk'
		fieldMetadata.maskType =  'all'

	return fieldMetadata

#Since these data is not specified right now, we are going to use static data
def build_picklist_values_metadata(field_data, metadata_client):
	"""
	Build the valueSet metadata for picklist fields
	"""

	# Create the value set
	value_set = metadata_client.factory.create("ValueSetValuesDefinition")
	value_set.sorted = False
	value_set.value = []

	# The array of valeus to create picklist values for
	picklist_values_list = []
	#Here we define static data for fields 
	#Once ready we'll get data from a form and put it in place of Static
	Static = ['Value 1', 'Value 2', 'Value 3', 'Value4']
	# Split string for new lines
	for value in Static:

		# If value isn't blank or null, add to array
		if value:
			picklist_values_list.append(value)

	# Determine first value for the loop
	first_value = True

	for picklist in picklist_values_list:

		picklist_value = metadata_client.factory.create("CustomValue")
		picklist_value.label = picklist
		picklist_value.isActive = True
		picklist_value.fullName= picklist
		picklist_value.default = True if first_value else False # If first value and first value default is checked

		# Add to the value list
		value_set.value.append(picklist_value)

		# Remove the first value boolean
		first_value = False

	return value_set