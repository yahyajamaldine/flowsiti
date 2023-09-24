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

def buildFields(field, metadata):
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
	fieldMetadata.type = field.get('field_name')
	
	return fieldMetadata