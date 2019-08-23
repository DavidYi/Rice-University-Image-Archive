from testiiif import db, ma
from datetime import datetime
from PIL import Image
import os

basedir = os.path.abspath(os.path.dirname(__file__))

tag_identifier = db.Table('tag_identifier',
        db.Column('pic_id', db.Integer, db.ForeignKey('pics.id')),
        db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'))
)


class Thumbnail(db.Model):
        __tablename__ = 'thumbnails'
        id = db.Column(db.Integer, primary_key=True)
        pic_id = db.Column(db.Integer, db.ForeignKey('pics.id'))
        name = db.Column(db.String(140))
        size = db.Column(db.String(20))
        path = db.Column(db.VARCHAR(250), nullable=False, unique=True)

        def __init__(self, pic_id, path, size, name=''):
                self.name = name
                self.pic_id = pic_id
                self.size = size
                self.path = path

	def get_relative_path(self):
		return 'thumbnails/' + str(os.path.basename(self.path))

class Pic(db.Model):
        __tablename__ = 'pics'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(140), info={'label': 'Name'})
        path = db.Column(db.VARCHAR(250), nullable=False, unique=True, info={'label': 'Path'})
        path_modified = db.Column(db.VARCHAR(250), unique=True, nullable=True, info={'label': 'Modified Path'})
	region = db.Column(db.String(140), nullable=False, default='/full')
	size = db.Column(db.String(140), nullable=False, default='/full')
	rotation = db.Column(db.String(140), nullable=False, default='/0')
	quality = db.Column(db.String(140), nullable=False, default='/default.')
	date_doc = db.Column(db.DateTime, info={'label': 'Date of Document'})
	date_photo = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, info={'label': 'Date of Picture'})
	date_added = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, info={'label': 'Date Added'})
	page_number = db.Column(db.Integer, info={'label': 'Page Number'})
	title = db.Column(db.VARCHAR(250), info={'label': 'Title'})
	author = db.Column(db.VARCHAR(250), info={'label': 'Author'})
	archive = db.Column(db.VARCHAR(250), info={'label': 'Archive'})
	collection = db.Column(db.VARCHAR(250), info={'label': 'Collection'})
	box = db.Column(db.VARCHAR(250), info={'label': 'Box'})
	folder = db.Column(db.VARCHAR(250), info={'label': 'Folder'})
	transcript = db.Column(db.Text, default="insert transcript", info={'label': 'Transcript'})
        
	#many to many tags
        tags = db.relationship("Tag", secondary=tag_identifier,back_populates="pics")
        
	#one to many thumbnail
        thumbnail_id = db.relationship('Thumbnail', backref='pic', lazy='dynamic')


        def __init__(self, path, name='', date=datetime.utcnow()):
                if name == '':
                        self.name = os.path.basename(path)
			#self.name = os.path.splitext(os.path.basename(path))[0]
                else:
                        self.name = name

		self.date_photo = date
		self.date_doc = date
		self.date_added = datetime.utcnow()
                self.path = str(path)
			
		self.add_tag(Tag.query.filter_by(name=".root").first())
		self.add_tag(Tag.query.filter_by(name="untagged").first())
		
		
        def get_thumbnail_name(self, size):
		return "thmb_"+str(self.id)+"_"+str(size)

        def get_thumbnail(self, width, height):
		size = str(width) + ',' + str(height)
                thumbnails = Thumbnail.query.filter((Thumbnail.pic_id==self.id) & (Thumbnail.size == size)).all()
		if not thumbnails:
                        image = Image.open(self.path)
                        image.thumbnail((width,height))
                        name = self.get_thumbnail_name(size)
                        path = basedir + '/static/thumbnails/' + name + ".jpg"
                        image.save(path)

                        tb = Thumbnail(self.id, path, size, name)
                        db.session.add(tb)
                        db.session.commit()

                        return tb
		else:
			return thumbnails[0]
	
        def __repr__(self):
                return "<br><br>Name: " + self.name + "<br> Path: " + self.path + "<br> tags: " + str(self.tags)

        def change_date(self, date):
                self.date_doc = date

        def edit_transcript(self, ocr):
                self.transcript = ocr

        def change_path(self, path):
                self.path = path
		name = os.path.splitext(os.path.basename(path))[0]
		if self.title != name:
			self.change_name(name)
	
	def change_name(self, name):
		self.title = name

        def add_tag(self, tag):
                if tag.isFolder:
			for t in self.tags:
				if t.isFolder:
					self.tags.remove(t)
		self.tags.append(tag)
                db.session.commit()
	
        def remove_tag(self, tag):
		self.tags.remove(tag)
		db.session.commit()

class Tag_Hierarchy(db.Model):
        __tablename__ = 'tag_hierarchy'
        parent_id = db.Column(db.Integer, db.ForeignKey('tags.id'), primary_key=True, nullable=False)
        node_id = db.Column(db.Integer, db.ForeignKey('tags.id'), primary_key=True, nullable=False)
        depth = db.Column(db.Integer)

        parent = db.relationship("Tag", back_populates="nodes", foreign_keys=[parent_id])
        node = db.relationship("Tag", back_populates = "parents", foreign_keys=[node_id])

        def __init__(self, parent_id, node_id, depth):
                self.parent_id = parent_id
                self.node_id = node_id
                self.depth = depth

        def __repr__(self):
                return "<br><br>parent: " + Tag.query.filter_by(id=self.parent_id).all()[0].name + "-->" + Tag.query.filter_by(id=self.node_id).all()[0].name+" DEPTH:" + str(self.depth)


class Tag(db.Model):
        __tablename__ = 'tags'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(140))
        
	pics = db.relationship("Pic", secondary= tag_identifier, back_populates="tags")
	
	isFolder = db.Column(db.Boolean)
	hidden = db.Column(db.Boolean)

        nodes = db.relationship("Tag_Hierarchy", back_populates="parent", foreign_keys="Tag_Hierarchy.node_id")
        parents = db.relationship("Tag_Hierarchy", back_populates="node", foreign_keys="Tag_Hierarchy.parent_id")

        def __init__(self, name, isFolder=False, hidden=False):
                self.name = name
		self.isFolder = isFolder
		self.hidden = hidden
                db.session.add(self)
                db.session.commit()
	
		if self.isFolder:
                	db.session.add(Tag_Hierarchy(self.id, self.id, 0))
			if name != ".root":
				db.session.add(Tag_Hierarchy(Tag.query.filter_by(name=".root").first().id, self.id, 1))
			db.session.commit()

        def __repr__(self):
                return self.name

	def get_direct_children(self):
		hierarchies = Tag_Hierarchy.query.filter((Tag_Hierarchy.parent_id==self.id) & (Tag_Hierarchy.depth==1)).all()
		return [Tag.query.filter_by(id=h.node_id).first() for h in hierarchies]
		
	def delete_parent_relation(self):
		for relation in Tag_Hierarchy.query.filter_by(node_id=self.id).all():
			if relation.parent_id != self.id:
				parent_del = Tag_Hierarchy.query.filter((Tag_Hierarchy.parent_id == relation.parent_id) & (Tag_Hierarchy.node_id == d.node_id)).first()
                                db.session.delete(parent_del)
		db.session.commit()
	
	def delete_folder(self):
		#parent = Tag_Hierarchy.query.filter((Tag_Hierarchy.node_id==folder.id) & (Tag_Hierarchy.depth==1)).first()
                #parent = Tag.query.filter_by(id = parent.parent_id).first()
		parent = Tag.query.filter_by(name='.root').first()
			
		#move folder to root
		children = self.get_direct_children()
		for child in children:
			parent.hierarchy(child.id)

		#get rid of any relationship
		relations = Tag_Hierarchy.query.filter((Tag_Hierarchy.parent_id==self.id) | (Tag_Hierarchy.node_id==self.id)).all()
		for relation in relations:
			db.session.delete(relation)
		db.session.commit()
	
		#move photos to root
		photos = Pic.query.filter(Pic.tags.any(id=self.id)).all()
		for photo in photos:
			photo.add_tag(self)
		
		db.session.delete(self)
		db.session.commit()

        def hierarchy(self, child_id):
		#changes the hierarchy of the tag, so need to delete the to be child tag and its subtags' relation with its current parent, and then create hierarchical relation with current tag

		descendents = Tag_Hierarchy.query.filter_by(parent_id=child_id).all()
		parents_past = Tag_Hierarchy.query.filter_by(node_id=child_id).all()
		parents_new = Tag_Hierarchy.query.filter_by(node_id=self.id).all()
		print "changing the hierarchy of the tag"
		print "descendents:\t" + str(descendents)
		print "parents_past:\t" + str(parents_past)
	
		#if to be child folder already is a child folder ignore\
		if Tag_Hierarchy.query.filter((Tag_Hierarchy.parent_id==self.id) & (Tag_Hierarchy.node_id == child_id) & (Tag_Hierarchy.depth == 1)).first():
			print "ABORT: CHILD IS ALREADY A CHILD OF CURRENT FOLDER"
			return

		#if the child folder is a parent of the current folder
		if Tag_Hierarchy.query.filter((Tag_Hierarchy.parent_id==child_id) & (Tag_Hierarchy.node_id == self.id)).first():
			print "CHILD IS A PARENT OF CURRENT FOLDER: ABORT"
			return

		#delete the current parent tags for child_id tag
		#goes through every descendent and delete relation with every parent of the child_id tag
		for d in descendents:
			for relation in parents_past:
				print relation
				if relation.parent_id != child_id:
                                        parent_del = Tag_Hierarchy.query.filter((Tag_Hierarchy.parent_id == relation.parent_id) & (Tag_Hierarchy.node_id == d.node_id)).first()
					print "deleting.... \t\t" + str(parent_del)
					if parent_del:
						db.session.delete(parent_del)
                db.session.commit()
	
		print "adding new relations"
		print "parents_new:\t" + str(parents_new)

		#add new relation for new parent tags(this tag and its parents) for child_id
                for relation in parents_new:
			for descendent in descendents:
				temp = Tag_Hierarchy(relation.parent_id, descendent.node_id, relation.depth + descendent.depth + 1)
				db.session.add(temp)
		
		db.session.commit()

########### SCHEMAS #####################

class PicSchema(ma.ModelSchema):
	class Meta:
		model = Pic

class TagSchema(ma.ModelSchema):
	class Meta:
		model = Tag

########### HELPER FUNCTIONS #############
def get_pics():
	return Pic.query.all()

def get_tags():
	return Tag.query.all()


# given the filters in a dictionary format, this function searches the pictures based on the filters
# should be given in this format {"tablename.column": "data", ...}
def search(filters):
	where = '(1=1)'
	group = ''
	having = ''
	for param in filters:
		#this if function is to check for the tag and folder filter
		if filters[param] and isinstance(filters[param], list):
			where += ' AND ' + str(param) + ' in (' + ','.join(filters[param]) + ')'
			having = ' HAVING COUNT(DISTINCT tags.id) =' + str(len(filters[param]))
			group = ' GROUP BY pics.id'
		elif not isinstance(filters[param],list):
			where += ' AND ' + str(param) + ' = \'' + str(filters[param]) + '\''
	
	sqlquery = db.text('SELECT DISTINCT pics.id, tags.name '
				'FROM pics '
				'INNER JOIN tag_identifier AS ti ON pics.id=ti.pic_id '
				'INNER JOIN tags ON tags.id=ti.tag_id '
				'WHERE' + where + group + having + ';')
	print sqlquery
	result = db.session.execute(sqlquery).fetchall()
	tmp = {}
	ids = []
	# translate the row proxy object into a dictionary so that we can print and a list of just the id to get pictures as pic model object
	for r in result:
		ids.append(r['id'])
                tmp[r[0]] = dict(r.items())
	print tmp

	return Pic.query.filter(Pic.id.in_(ids)).order_by(Pic.name).all()

	'''
	first = True
	where = '(1=1)'
	for param in filters:
		where += '& (' + str(param) + ' = \'' + str(filters[param]) + '\')'

	return Pic.query.filter(db.text(where)).all()
	'''
	
	

# get the hierarchy of t
def get_hierarchy():
	h = Tag_Hierarchy.query.filter_by(depth=1).all()
	hier = {}
	for relation in h:
		key = h.parent_id
		if key in hier:
			hier[key].append(h.node_id)
		else:
			hier[key] = [h.node_id]
	return hier

def get_subtags(tag):
	return Tag_Hierarchy.query.filter_by(parent_id=tag.id).order_by(Tag_Hierarchy.depth)

def get_root(tag):
	return Tag_Hierarchy.query.filter(Tag_Hierarchy.node_id==parent_id).order_by(Tag_Hierarchy.depth.desc()).first()

def get_path_hierarchy(tag):
	Tag_Hierarchy.query.filter_by(node_id=parent_id)
