import sys
import os

# Add your application directory to the path
sys.path.insert(0, '/srv/www/mds-review.ok.ubc.ca')

# Change to the application directory
os.chdir('/srv/www/mds-review.ok.ubc.ca')

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv('/srv/www/mds-review.ok.ubc.ca/.env')

# Import your Flask app
from main import app as application
