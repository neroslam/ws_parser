import sys
sys.path.append('/home/ws_parser')
from flsk_srv.app import app
app.run(debug = True, host='0.0.0.0')