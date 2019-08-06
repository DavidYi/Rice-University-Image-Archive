#!/bin/python
import os
from flask import Flask, request
from sqlalchemy.event import listen
from sqlalchemy import event
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate

from PIL import Image
from PIL.ExifTags import TAGS


app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = 'mysecretkey'


from flask_iiif import IIIF
from flask_restful import Api

api = Api(app=app)
ext = IIIF(app=app)

basedir = os.path.abspath(os.path.dirname(__file__))
ext.init_restful(api)


######### DATABASE #########
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:ricecrc@10.134.196.56/test'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False

db = SQLAlchemy(app)
ma = Marshmallow(app)
Migrate(app, db)

import models


######### FUNCTIONS #######

def get_exifs(paths):
        exifs = {}
        for path in paths:
                exifs[path] = {}
                img = Image.open(path)
                info = img._getexif()
                exifs[path]['type'] = img.format
                for tag, value in info.items():
                        decoded = TAGS.get(tag, tag)
                        exifs[path][decoded] = value
        return exifs

def setup():
	root = models.Tag('.root', hidden=True, isFolder=True)
	untagged = models.Tag('untagged')	

@event.listens_for(models.Tag.__table__, 'after_create')
def insert_initial_values(*args, **kwargs):
     setup()

def redirect_url(default='core.index'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)


########### WATCHER ##########
from multiprocessing import Process
import watcher

#@app.before_first_request
def activate_job():
	watch = watcher.Watcher()
	global p 
	p = Process(target=watch.run)
	p.start()

######### ROUTES ##########
from views import core
from resources import api_bp

app.register_blueprint(core)
app.register_blueprint(api_bp, url_prefix='/api')

if __name__=='__main__':
	#watcher = Watcher()
	print "*******starting \n\n"
	

	watcher_thread = threading.Thread(target=run_watcher)
	watcher_thread.start()
        app.run()
	watcher_thread.join()
	
	print "*******hey\n\n"
