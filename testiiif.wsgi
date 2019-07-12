import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,'/var/www/testiiif')

import testiiif
import threading

application = testiiif.app
#watcher = testiiif.Watcher()
#my_thread = threading.Thread(target=watcher.run)
#my_thread.start()
