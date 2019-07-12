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
        name = db.Column(db.String(140))
        path = db.Column(db.VARCHAR(250), nullable=False, unique=True)
        path_modified = db.Column(db.VARCHAR(250), unique=True, nullable=True)
	date_doc = db.Column(db.DateTime)
	date_photo = db.Column(db.DateTime, nullable=False)
        added = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
	page_number = db.Column(db.Integer)
	title = db.Column(db.VARCHAR(250))
	author = db.Column(db.VARCHAR(250))
	archive = db.Column(db.VARCHAR(250))
	collection = db.Column(db.VARCHAR(250))
	box = db.Column(db.VARCHAR(250))
	folder = db.Column(db.VARCHAR(250))
	transcript = db.Column(db.Text, default="insert transcript")
        
	#many to many tags
        tags = db.relationship("Tag", secondary=tag_identifier,back_populates="pics")
        
	#one to many thumbnail
        thumbnail_id = db.relationship('Thumbnail', backref='pic', lazy='dynamic')


        def __init__(self, path, name='', date=datetime.utcnow()):
                if name == '':
                        self.name = os.path.splitext(os.path.basename(path))[0]
                else:
                        self.name = name

		self.date_photo = date
		self.date_doc = date
		self.added = datetime.utcnow()
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
	
        def hierarchy(self, child_id):
		descendents = Tag_Hierarchy.query.filter_by(parent_id=child_id).all()
		print "hiiiii"
		print descendents	
		#delete the current parent tags for child_id tag
		#past_depth = Tag_Hierarchy.query.filter((Tag_Hierarchy.node_id==child_id) & (Tag_Hierarchy.parent_id==Tag.query.filter_by(name=".root").first().id)).first().depth
		
		for d in descendents:
			print "************* descdent"
			print d
			for relation in Tag_Hierarchy.query.filter_by(node_id=self.id).all():
				print "-------> r"
				print relation
				if relation.parent_id != self.id:
                                        parent_del = Tag_Hierarchy.query.filter((Tag_Hierarchy.parent_id == relation.parent_id) & (Tag_Hierarchy.node_id == d.node_id)).first()
                                        if parent_del:
						db.session.delete(parent_del)
                db.session.commit()	
	
		print "relations"
		#add new relation for new parent tags for child_id
                for relation in Tag_Hierarchy.query.filter_by(node_id=self.id).all():
			print relation
			print "*******"
			print descendents
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

def search(filters):
	first = True
	where = '(1=1)'
	for param in filters:
		where += '& (' + str(param) + ' = \'' + str(filters[param]) + '\')'
	return Pic.query.filter(db.text(where)).all()


#print search({Pic.title: 'test'})

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
