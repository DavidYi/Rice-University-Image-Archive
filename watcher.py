from watchdog.observers.polling import PollingObserver
from watchdog.events import RegexMatchingEventHandler, FileSystemEventHandler
import time
import os
import re
#from models import Pic, Tag, db
from testiiif import get_exifs
from models import Pic, Tag, db
from shutil import copyfile, move
from PIL import Image
import sys
import fitz


def run_watcher():
	watcher = Watcher()
	watcher.run()

DIRECTORY_TO_WATCH = "/var/www/testiiif/mnt/rdf/jcm10/crc_summer_dev/dropbox"


pattern = re.compile('[a-z|A-Z|0-9|.|\_|\-|]')



# FUNCTION TO SPLIT THE PDF
def split(pdf_filepath,jpg_dir):
	doc = fitz.open(pdf_filepath)

	#borrowed from https://stackoverflow.com/questions/2693820/extract-images-from-pdf-without-resampling-in-python?lq=1
	for i in range(len(doc)):
		print i
		for img in doc.getPageImageList(i):
			xref = img[0]
			pix = fitz.Pixmap(doc, xref)
			output_filename = "%s-%s.jpg" % (i, xref)
			output_filepath = os.path.join(jpg_dir,output_filename)
			print output_filepath
			
			pix = fitz.Pixmap(fitz.csRGB, pix)
			img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
			img.save(output_filepath,"JPEG")
	
			pix = None


def clean_path(path):
	components = path.split(os.sep)
	new_comps = []
	for component in components:
		new_comp = ''
		for letter in component:
			if re.match(pattern,letter):
				new_comp += letter
		new_comps.append(new_comp)
	return os.path.sep.join(new_comps)


class Watcher:

	def __init__(self):
		self.observer = PollingObserver()

	def run(self):
		print "starting watch woof woof!!!!!!"

		event_handler = Handler()       
		self.observer.schedule(event_handler, DIRECTORY_TO_WATCH, recursive=True)
		self.observer.start()

		try:
			while True:
				time.sleep(5)
		except:
			self.observer.stop()
			print "Error"

		self.observer.join()


class Handler(RegexMatchingEventHandler):

	def __init__(self):
		#TO IGNORE HIDDEN FILES AND FOLDERS
		super(Handler, self).__init__(ignore_regexes=["^\..*", ".*/\..*"])


        def on_created(self, event):
		path = os.path.normpath(event.src_path)
		print "************create new file at " + str(path)
	
		#IF DIRECTORY DO NOTHING
		if event.is_directory:
			return

		filename = str(os.path.basename(path))
		#print filename
		filename = clean_path(filename)
                filepath = str(os.path.dirname(path))
                #print filename
                #print filepath

		tmp = filepath.replace(DIRECTORY_TO_WATCH, '')

		name = os.path.splitext(filename)


		iiif_base = os.path.normpath(os.path.join(DIRECTORY_TO_WATCH, '../storage/'))
		mv_base = os.path.normpath(os.path.join(DIRECTORY_TO_WATCH, '../result/'))
		mv_filepath = filepath.replace(DIRECTORY_TO_WATCH, mv_base,1)
                #print "mv_filepath"
		#print tmp
		#print mv_filepath
		filepath_un = filepath
		filepath = os.path.normpath(filepath.replace(DIRECTORY_TO_WATCH, iiif_base, 1))

		type = name[1].lower()


		#IF THE FILE IS A PDF, create folder to put img in and split pdf into images to put into created folder
                if type == '.pdf':

                        jpg_dir = os.path.join(filepath_un,name[0])
			#print jpg_dir
                        if os.path.exists(jpg_dir):
                                return
                        os.makedirs(jpg_dir)

                        try:
                                split(path,jpg_dir)
				mv_base = os.path.normpath(os.path.join(mv_base, 'success/'))
                        except:
                                print("Failed on", path + ".pdf")
                                print("Unexpected error:", sys.exc_info()[0])
                                print sys.exc_info()
				mv_base = os.path.normpath(os.path.join(mv_base, 'error/'))

		


		# FOR IMAGES, create entry in db after checking if they are located in a folder (if they are then put the folder tag on it)
		elif type == '.jpg' or type == '.tif' or type == '.png':
			try:
				#print filepath
	                        tmp = filepath.replace(iiif_base, '')
				#print tmp
				new_tmp = clean_path(tmp)

				#print filepath
				filepath = os.path.normpath(filepath.replace(tmp, new_tmp))
				#print "new filepath after cleaning"
				#print filepath
	
				#split the file path into its components
				direct = new_tmp.split(os.sep)
				addition = direct[0]
			
				#print "yoooo"
				#print str(tmp) + "--->" + str(new_tmp)
				#print direct
				parent = ''
			
				#get rid of any empty quotes
				direct = list(filter(None, direct))
			
				#check if needs to create folder tag for its route
				for folder in direct:
					if not folder:
						continue
					f_tag = Tag.query.filter_by(name=str(folder)).first()
					if not f_tag:
						print "creating tag for" + str(folder)
						f_tag = Tag(str(folder), isFolder=True)
						if folder != direct[0]:
							parent.hierarchy(f_tag.id)
							db.session.commit()
							print 'creating heirarchy to ' + str(parent)
					parent = f_tag
					addition = os.path.join(addition, folder)
			
						
				new_path = os.path.normpath(os.path.join(filepath, filename))
				#print "new path"
				#print new_path

				#if picture already has entry then do nothing
				if Pic.query.filter_by(path=new_path).first():
					return
		
				if not os.path.exists(filepath):
					os.makedirs(filepath)
	
				copyfile(path,new_path)
			
				try:
					exif = get_exifs([new_path])[new_path]
		        		date = exif['DateTime']
					new_pic = Pic(str(new_path), date=date)
	        	        except:
					new_pic = Pic(str(new_path))
				db.session.add(new_pic)
		                db.session.commit()
		
				#if it has a parent folder then tag it
				if len(direct) > 0:
					new_pic.add_tag(f_tag)
					db.session.commit()

				mv_base = os.path.normpath(os.path.join(mv_base, 'success/'))
			except:
				mv_base = os.path.normpath(os.path.join(mv_base, 'error/'))
				print("Unexpected error:", sys.exc_info()[0])
				print sys.exc_info()
		else:
			print "NOT SUPPORTED TYPE #######################"
			return

		#print mv_base	
		mv_filepath = filepath_un.replace(DIRECTORY_TO_WATCH, mv_base,1)
		print mv_filepath
		if not os.path.exists(mv_filepath):
			os.makedirs(mv_filepath)

		mv_path = os.path.join(mv_filepath, filename)	
		move(path, mv_path)
			

        def on_deleted(self, event):
		if event.is_directory:
			return
		if os.path.splitext(os.path.basename(event.src_path))[0][0] == '.':
                        return 

                print "************deleted" + str(event.src_path)
                #print os.stat(event.src_path)
		
		#pic_deleted = Pic.query.filter_by(path=event.src_path).first()
                #db.session.delete(pic_deleted)
                #db.session.commit()
		

#print os.stat('/var/www/testiiif/mnt/rdf/jcm10/crc_summer_dev/hi')
run_watcher()
