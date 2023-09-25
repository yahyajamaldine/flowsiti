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
	fieldMetadata.length = 50
	
	fieldMetadata.inlineHelpText ='add Helptext'
	fieldMetadata.description = 'add Helptext'
	fieldMetadata.type = field.get('field_type')
	
	if fieldMetadata.type == 'Checkbox':
		fieldMetadata.defaultValue = True if field['checkboxdefault'] == 'checked' else False

	elif fieldMetadata.type == 'Currency':
		if field['default']:
			fieldMetadata.defaultValue = field['default']
		fieldMetadata.precision = int(field['precision']) + int(field['decimal'])
		fieldMetadata.scale = int(field['decimal'])
		fieldMetadata.required = field['required']
	
	elif fieldMetadata.type == 'Email':
		if field['default']:
			fieldMetadata.default = 'nothing@email.com'
		fieldMetadata.externalId = field['external']
		fieldMetadata.required = field['required']
		fieldMetadata.unique = field['uniqueSetting']
		
	elif fieldMetadata.type == 'Text':
		if field['default']:
			fieldMetadata.defaultValue = field['default']
		fieldMetadata.length = field['length']
		fieldMetadata.externalId = field['external']
		fieldMetadata.required = field['required']
		fieldMetadata.unique = field['uniqueSetting']

	return fieldMetadata