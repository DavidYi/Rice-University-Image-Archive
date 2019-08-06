from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
import time
import os
from models import Pic, db
from testiiif import get_exifs

def run_watcher():
	watcher = Watcher()
	watcher.run()

class Watcher:
    DIRECTORY_TO_WATCH = "/var/www/testiiif/mnt/rdf/jcm10/crc_summer_dev/hi"

    def __init__(self):
        self.observer = PollingObserver()

    def run(self):
        print "starting watch woof woof!!!!!!"
        
	event_handler = Handler()       
	self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
	self.observer.start()
       
	try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print "Error"

        self.observer.join()


class Handler(FileSystemEventHandler):
        def on_created(self, event):
                path = event.src_path
		if os.path.splitext(os.path.basename(path))[0][0] == '.':
			return 
		print "************create new file at " + str(path)
		print os.stat(path)
		
		exif = get_exifs([path])[path]
        	date = exif['DateTime']
		print date
		new_pic = Pic(str(path), 'test', date=date)
                db.session.add(new_pic)
                db.session.commit()
                new_pic.get_thumbnail(200,200)
		

        def on_moved(self, event):
                print "************moved" + str(event.src_path) + "--->" + str(event.dest_path)
                if os.path.splitext(os.path.basename(event.src_path))[0][0] == '.':
                        return 
		pic_moved = Pic.query.filter_by(path=event.src_path)
                pic_moved.change_path(event.dest_path)
                db.session.commit()
		

        def on_deleted(self, event):
		if os.path.splitext(os.path.basename(event.src_path))[0][0] == '.':
                        return 
                print "************deleted" + str(event.src_path)
                print os.stat(event.src_path)
		
		pic_deleted = Pic.query.filter_by(path=event.src_path).first()
                db.session.delete(pic_deleted)
                db.session.commit()
		

#print os.stat('/var/www/testiiif/mnt/rdf/jcm10/crc_summer_dev/hi')
#run_watcher()
