# Rice University Image Archive

This is a file system interface web app for image archiving by designing a Python Flask/Bootstrap web app and workflow on a CentOS 7 VM on Rice University research computing infrastructure.

Researchers can drop pdf’s or image files in nested directories; the system imports them in the same directory structure and creates records of these in an SQL database. The images are then presented to the user through a IIIF (International Image Interoperability Framework) server to allow users to edit (crop, rotate) as well as organize, tag, and search on their collections.

Our current humanities research test clients on the app has ~40k images with ~38k OCR text transcriptions (in English and Portuguese) layered into the database. This app allows humanities researchers with massive collections of large images to take advantage of networked storage and computing resources.

We used [SQLAlchemy](https://www.sqlalchemy.org) as the ORM (to define the models and do most of the queries), defined the schema using [Marshmallow](https://flask-marshmallow.readthedocs.io/en/latest/) (object deserialization library), and watch the SMB share for file system events using [Watchdog](https://pythonhosted.org/watchdog/index.html).

The set up instructions for setting this app up can be found in the repository.
*********ONE WARNING: the way it is set up works only on Rice Network with permission because it uses Rice University's VM resource
