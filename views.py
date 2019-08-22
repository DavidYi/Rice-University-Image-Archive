from flask import redirect, render_template, request, Blueprint, send_file, session, url_for
from flask_iiif.api import IIIFImageAPIWrapper,MultimediaImage
from urllib import urlretrieve
from PIL import Image
import os

from models import Tag, tag_identifier, Pic, Tag_Hierarchy, search
from testiiif import db, get_exifs,setup, basedir, redirect_url

from forms import EditTagForm, EditFolderForm, CropForm, BatchUpdateForm, AddTag2PicForm, MoveFolderForm, SearchForm, AddFolderForm, UpdateMetadataForm, AddTagForm

core = Blueprint('core', __name__)

@core.route('/',methods=["GET", "POST"])
def index():
        return redirect(url_for('core.home', folder='.root'))

#view for items in any folder
@core.route('/view/<folder>', methods=["GET", "POST"])
def home(folder):
	print "hi"
	folderForm = AddFolderForm()
	picForm = UpdateMetadataForm()
	searchForm = SearchForm()
	tagForm = AddTagForm()
	addTagForm = AddTag2PicForm()
	moveForm = MoveFolderForm()
	batchForm = BatchUpdateForm()
	editFolderForm = EditFolderForm()
	editTagForm = EditTagForm()
 	
	currentFolder = Tag.query.filter((Tag.name==folder) & (Tag.isFolder==True)).first_or_404()
	folder_hierarchy = Tag_Hierarchy.query.filter_by(node_id = currentFolder.id).order_by(Tag_Hierarchy.depth.desc()).all()
	folder_path = [Tag.query.filter_by(id = h.parent_id).first() for h in folder_hierarchy]
	
	moveForm.all_folders.data = currentFolder

	if folderForm.submitFolder.data and folderForm.validate_on_submit():
		name = folderForm.name.data
		new_folder = Tag(name, isFolder=True)
		currentFolder.hierarchy(new_folder.id)
		
		return redirect(url_for('core.home', folder=folder))
	if tagForm.submitTag.data and tagForm.validate_on_submit():
		name = tagForm.name.data
		new_tag = Tag(name)

	tag_list = Tag.query.filter_by(isFolder=False).all()
	children = currentFolder.get_direct_children()
	pics = Pic.query.filter(Pic.tags.any(id=currentFolder.id)).order_by(Pic.name).all()
	
	return render_template('home.html', editTagForm=editTagForm, editFolderForm=editFolderForm, batchForm=batchForm, moveForm=moveForm, addTagForm=addTagForm, tagForm=tagForm, searchForm=searchForm, picForm=picForm, folderForm=folderForm, tag_list=tag_list, folder_path=folder_path, pics=pics, folders=children)


#route to delete folder -> TO DO probably in resources 
@core.route('/view/<folder>/delete_folder/<delete_id>', methods=["GET", "POST"])
def delete_folder(folder, delete_id):
	tbd = Tag.query.filter_by(id=delete_id).first_or_404()
	

# route for what was searched
@core.route('/search', methods=["GET", "POST"])
def search_for():
        folderForm = AddFolderForm()
        picForm = UpdateMetadataForm()
        searchForm = SearchForm(request.form)
        tagForm = AddTagForm()
        addTagForm = AddTag2PicForm()
        moveForm = MoveFolderForm()
        batchForm = BatchUpdateForm()
	editTagForm = EditTagForm()

	tag_list = Tag.query.filter_by(isFolder=False).all()
	children = []
        pics = []
	
	if request.method == "POST" and searchForm.submitSearch.data:# and searchForm.validate():
                print "heeey"
                data = {}
                tb = searchForm.meta.model.__tablename__
		tb_tags = Tag.__table__.name
		
		tag_lst = []
		# go through searchForm and create a filter dictionary in the form of {"tablename.column": "data",...} to pass through search function located in models.py
                for field in searchForm:
		        if field != searchForm.submitSearch and field.data and field.data != "None":
				if field != searchForm.tags and field != searchForm.folder:
					data[tb+'.'+ field.name] = field.data
				else:
					tag_lst.append(str(field.data.id))
		data[tb_tags + '.id'] = tag_lst

               	print data
		if data:
			pics = search(data)
			print pics
                else:
			pics = {}
		return render_template('home.html', editTagForm= editTagForm, moveForm=moveForm, batchForm=batchForm, addTagForm=addTagForm, searchForm=searchForm, picForm=picForm, tagForm=tagForm, folderForm=folderForm, tag_list=tag_list, pics=pics, folders=[])
	'''
        print "searchForm"
        print searchForm.submitSearch.data
        print searchForm.validate()
        '''


        return render_template('home.html', moveForm=moveForm, batchForm=batchForm, editTagForm=editTagForm, searchForm=searchForm, addTagForm=addTagForm, tagForm=tagForm, picForm=picForm, folderForm=folderForm, pics=pics, folders=children)

@core.route('/editFolder', methods=["POST"])
def edit_folder():
	editForm = EditFolderForm(request.form)
	folder = Tag.query.filter((Tag.isFolder == True) & (Tag.id == editForm.id.data)).first_or_404()

	if request.method == "POST" and editForm.deleteFolder.data:
		folder.delete_folder()
	elif request.method == "POST" and editForm.submitEdit.data:
		folder.name = editForm.name.data
		new_parent = Tag.query.filter((Tag.isFolder == True) & (Tag.id == editForm.folder.data.id)).first_or_404()
		print new_parent
		new_parent.hierarchy(folder.id)
		db.session.commit()

	return redirect(redirect_url())


@core.route('/editTag', methods=["POST"])
def edit_tag():
	editForm = EditTagForm(request.form)
	tag = Tag.query.filter_by(id=editForm.id.data).first_or_404()
	
	if request.method == "POST" and editForm.deleteTag.data:
		if tag.name != 'untagged':
			db.session.delete(tag)
			db.session.commit()
	elif request.method == "POST" and editForm.submitChanges.data:
		tag.name = editForm.name.data
		db.session.commit()

	return redirect(redirect_url())

# single photo view route
@core.route('/view/photo/<photo>', methods=["GET", "POST"])
def single(photo):
	pic = Pic.query.filter_by(id=photo).first_or_404()
	picForm = UpdateMetadataForm(request.form, obj=pic)
	addTagForm = AddTag2PicForm()
	moveForm = MoveFolderForm()

	for t in pic.tags:
		if t.isFolder:
			print t
			moveForm.all_folders.data = t
			break

	if request.method=="POST" and picForm.submitMetadata.data:
		for field in picForm:
                        if not field.data:
				field.data = None
		picForm.populate_obj(pic)
		db.session.add(pic)
		db.session.commit()
		return redirect(redirect_url())
	print "hey"
	return render_template('photo_view.html', moveForm=moveForm, addTagForm=addTagForm, picForm=picForm, basedir=basedir, pic = pic)

#route to add tag
@core.route('/view/photo/<photo>/addTag', methods=["GET", "POST"])
def addingTag(photo):
        pic = Pic.query.filter_by(id=photo).first_or_404()
        addTagForm = AddTag2PicForm(request.form)

        if request.method=="POST" and addTagForm.addTag.data:
                pic.add_tag(addTagForm.all_tags.data)
        return redirect(url_for('core.single', photo=photo))

#route to move folder
@core.route('/view/photo/<photo>/move', methods=["GET", "POST"])
def movingFolder(photo):
        pic = Pic.query.filter_by(id=photo).first_or_404()
        moveForm = MoveFolderForm(request.form)

        if request.method=="POST" and moveForm.changeFolder.data:
		pics = []
                for id in filter(None, moveForm.ids.data.split(",")):
	                pics.append(Pic.query.filter_by(id=int(id)).first())

		for pic in pics:
			pic.add_tag(moveForm.all_folders.data)

        print "tagsdgaseg"
	return redirect(redirect_url())
        #return redirect(url_for('core.single', photo=photo))


#route ot remove tag: TO BE ADDED
@core.route('/view/photo/<photo>/deleteTag/<tag>',methods=["GET", "POST"])
def remove_tag(photo, tag):
	pic = Pic.query.filter_by(id=photo).first_or_404()
	t = Tag.query.filter_by(id=tag).first_or_404()
	pic.remove_tag(t)
	print "removed tag"
	return redirect(url_for('core.single', photo=photo))

#test stuff 
@core.route('/test', methods=["GET", "POST"])
def iiif():
	form = UpdateMetadataForm()
        return render_template('hi.html', form=form)
	#image = IIIFImageAPIWrapper.from_file(basedir+'/statmnt/IMG_9761.JPG')
        image = IIIFImageAPIWrapper.from_file(basedir+'/mnt/rdf/jcm10/crc_summer_dev/photo_dump_1/IMG_9763.JPG')
        #image = IIIFImageAPIWrapper.from_file(basedir+'/mnt/rdf/jcm10/crc_summer_dev/miller_wright/HRC_Image_Archiving_Interface/AESP-IT-7.pdf')

        # Rotate the image
        image.rotate(90)

        # Resize the image
        image.resize('300,200')

        # Crop the image
        image.crop('20,20,400,300')

        # Make the image black and white
        image.quality('grey')

        # Finaly save it to /tm
        image.save(basedir + '/static/test_pdf.jpg')

        return send_file(image.serve(), mimetype='image/jpeg')


#more testing for db
@core.route('/testdb', methods=["GET", "POST"])
def testdb():
        #pic = Pic.query.all()[0]
        #tag = Tag.query.filter_by(name='pictag').first()
        #print tag
        #print pic
        #pic.remove_tag(tag)
        #return redirect(url_for('core.printdb'))
	return '<h1>' + str(search({'pics.title': 'test', 'pics.id':11})) + '</h1>'
        '''
        tb = pic.get_thumbnail(200,200)
        if tb == -1:
                return "nope"
        image = IIIFImageAPIWrapper.from_file(tb.path)
        return send_file(image.serve(), mimetype='image/jpeg')
        #return str(Tag_Hierarchy.query.filter_by(depth=0).all())
        '''

# clear db: FOR TESTING PURPOSE IN THE CASE OF DEPLOYMENT, PROBS GET RID OF IT
@core.route('/cleardb', methods=["GET", "POST"])
def cleardb():
        meta = db.metadata
        for table in reversed(meta.sorted_tables):
                print 'Clear table %s' % table
                db.session.execute(table.delete())
        db.session.commit()
	setup()
        return redirect(url_for('core.printdb'))

#rotating the photo
@core.route('/rotate/<photo>/<dir>')
def rotate(photo, dir):
	pic = Pic.query.filter_by(id=photo).first_or_404()
	rotate = int(pic.rotation[1:])
	if dir == 'l':
		rotate -= 90
		while rotate < 0:
			rotate += 360
	elif dir == 'r':
		rotate += 90
		while rotate >= 360:
			rotate -= 360
	pic.rotation = pic.rotation[0] + str(rotate)
	db.session.commit()
	return redirect(redirect_url())

#ROUTE TO CROP VIEW
@core.route('/view/crop/<photo>', methods=["GET","POST"])
def crop(photo):
	pic = Pic.query.filter_by(id=photo).first_or_404()
	cropForm = CropForm(request.form)

	if request.method=="POST" and cropForm.submitCoor.data:
		pic.region = cropForm.coor.data
		db.session.commit()
		return redirect(url_for('core.single',photo=photo))
	
	return render_template('crop_view.html', cropForm=cropForm, pic = pic)


#to print what is in the database
@core.route('/printdb', methods=['GET','POST'])
def printdb():
        return str(Pic.query.all()) + "<br><br> tags:" + str(Tag.query.all()) + "<br><br> hierarchy:" + str(Tag_Hierarchy.query.all())
