from flask import request, jsonify, Blueprint,redirect

from forms import BatchUpdateForm, MoveFolderForm, AddTag2PicForm, UpdateMetadataForm
from models import Tag, TagSchema, Pic, PicSchema, Tag_Hierarchy
from testiiif import db, redirect_url

import datetime
import dateutil.parser

api_bp = Blueprint('api_bp', __name__)

pic_schema = PicSchema()
tag_schema = TagSchema()
tags_schema = TagSchema(many=True)

@api_bp.route('/metadata/<pic_id>', methods=['GET'])
def get_metadata(pic_id):
	pic = Pic.query.filter_by(id=pic_id).first()
	tags = pic.tags

	pic = pic_schema.dump(pic).data
	#translate ISO 8601 date string into datetime object, but banks on fact that column name has date in it
	for field in pic:
		if "date" in field:
			pic[field] = dateutil.parser.parse(pic[field]).strftime("%m/%d/%Y, %H:%M:%S")
	tags = tags_schema.dump(tags).data
	return jsonify(pic=pic, tags=tags)

@api_bp.route('/addTag/<pic_id>', methods=['GET', 'POST'])
def addTag(pic_id):
	pic = Pic.query.filter_by(id=pic_id).first()
	addTagForm = AddTag2PicForm(request.form)
        pics = []
        for id in filter(None, addTagForm.ids.data.split(",")):
		pics.append(Pic.query.filter_by(id=int(id)).first())
        for pic in pics:
		pic.add_tag(addTagForm.all_tags.data)

	tags = pic.tags
	tags = tags_schema.dump(tags).data
	pic = pic_schema.dump(pic).data
        return jsonify(pic=pic, tags=tags)


@api_bp.route('/metadata/<pic_id>', methods=['GET','POST'])
def update_metadata(pic_id):
        pic = Pic.query.filter_by(id=pic_id).first_or_404()
	
	#print request.form
	#print "before"
	#print pic_schema.dump(pic).data

	picForm = UpdateMetadataForm(request.form, obj=pic)
	#print type(picForm.date_doc.data)
	#print type(request.form['date_doc'])
	
	if request.method=="POST":
		#picForm.populate_obj(pic)

	        for field in picForm:
        	        if field.data:
				setattr(pic, field.name, field.data)
                	elif not field.data:
				setattr(pic, field.name, None)


		# when addin obj and request.form, dates are not being inputed so need to do it manually
		pic.date_doc = request.form['date_doc']
		pic.added = request.form['added']
		pic.date_photo = request.form['date_photo']

		#db.session.add(pic)
        	db.session.commit()
		#return redirect(redirect_url())

		pic = pic_schema.dump(pic).data
		return jsonify(pic=pic)

@api_bp.route('/metadata_batch', methods=['POST'])
def update_batch():
	batchForm = BatchUpdateForm(request.form)
	pics = []
	print "########### request form for update batch #############"
	print request.form
	for id in filter(None, batchForm.ids.data.split(",")):
		pics.append(Pic.query.filter_by(id=int(id)).first())
	print "******************* list of pics**********"
	print pics
	for field in batchForm:
		print str(field.name) + "\t" + str(request.form[field.name])
		if request.form[field.name] and request.form[field.name] != "*******" and field != batchForm.ids:
			for pic in pics:
				setattr(pic, field.name, request.form[field.name])
		elif not request.form[field.name] and request.form[field.name]!= "*******":
			print "this is nothing in it" + str(field.name)
			for pic in pics:
				setattr(pic, field.name, None)

	db.session.commit()
	return redirect(redirect_url())
				

'''
from flask_restful import Resource

class PicResource(Resource):
	def get(self):
'''		
