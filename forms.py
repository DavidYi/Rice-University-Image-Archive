from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo
from wtforms import ValidationError
from wtforms_alchemy import ModelForm, ModelFieldList
from wtforms.fields import FieldList, FormField
from wtforms.ext.sqlalchemy.fields import QuerySelectField


from models import Tag, Pic

from collections import OrderedDict


def tag_select_choices():
        return Tag.query.filter_by(isFolder=False).all()

def folder_select_choices():
        return Tag.query.filter_by(isFolder=True).all()

'''
class AddTagForm(ModelForm):
	class Meta:
		model = Tag
		only = ['name']
	
	def validate_name(self, field):
		if Tag.query.filter_by(name=field.data).first():
			raise ValidationError('Tag with name \"' + field.data + '\" already exists')
'''
class AddTagForm(FlaskForm):
	name = StringField('Name', validators=[DataRequired()])
        submitTag = SubmitField("Add Tag")

        def validate_name(self, field):
                if Tag.query.filter_by(name=field.data).first():
                        raise ValidationError('Tag with name \"' + field.data + '\" already exists')

class AddTag2PicForm(FlaskForm):
	tags = FieldList(HiddenField('tags'))
	ids = HiddenField('')
	all_tags = QuerySelectField('tags', query_factory=tag_select_choices)
	addTag = SubmitField('Add Tags')

class MoveFolderForm(FlaskForm):
	ids = HiddenField('')
	all_folders = QuerySelectField('folders', query_factory=folder_select_choices)
	changeFolder = SubmitField('Change Folder')

class ModelOrderedForm(ModelForm):
	'''
   	 To apply add to Meta 'order' iterable
	'''
	'''
	def __init__(self, *args, **kwargs):
		super(OrderFormMixin, self).__init__(*args, **kwargs)
		print getattr(self.meta, 'model', None)
	'''
	def __iter__(self):	
		field_order = getattr(self.meta, 'order', [])
		ignore_order = getattr(self.meta, 'ignore_order', [])
		if field_order:
			new_fields = OrderedDict()
		
			for name in field_order:
				if name == '*':
					for name in self._fields:
						if name not in field_order and name not in ignore_order:
							new_fields[name] = self._fields[name]
				else:
					new_fields[name] = self._fields[name]

			self._fields = new_fields
		return super(ModelOrderedForm, self).__iter__()

class UpdateMetadataForm(ModelOrderedForm):
	submitMetadata = SubmitField("Update Metadata")

	class Meta:
		model = Pic
		exclude = ['region','size','rotation','quality']
		include = ['date_photo', 'added']
		order = ('*', 'submitMetadata')

	#tags = ModelFieldList(FormField(AddTagForm))
	#tags = SelectMultipleField(choices= [(tag.id, tag.name) for tag in Tag.query.all()])

class BatchUpdateForm(ModelOrderedForm):
	submitBatch = SubmitField("Update Batch")
	ids = HiddenField('')	

	class Meta:
		model = Pic
		exclude = ['path', 'path_modified', 'name', 'region', 'rotation', 'quality']
		include = ['date_photo', 'added']
		order = ('*', 'submitBatch')


class SearchForm(ModelOrderedForm):
	tags = QuerySelectField('Tags', query_factory=tag_select_choices)
	folder = QuerySelectField('Folder', query_factory=folder_select_choices)
	submitSearch = SubmitField("Search")
	class Meta:
                model = Pic
                exclude = ['path', 'path_modified', 'region', 'size','rotation', 'quality']
		include = ['date_photo', 'added']
                order = ('*', 'folder', 'tags', 'submitSearch')
		
	def validate_name(self):
		return
	
	def return_field_names(self):
		return self._fields.key()

class CropForm(FlaskForm):
	coor = HiddenField()
	submitCoor = SubmitField('Crop')

class AddFolderForm(FlaskForm):
	name = StringField('Name', validators=[DataRequired()])
	submitFolder = SubmitField("Add Folder")
	
	def validate_name(self, field):
		if Tag.query.filter_by(name=field.data).first():
			raise ValidationError('Tag with name \"' + field.data + '\" already exists')
