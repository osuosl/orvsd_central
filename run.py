import sys
sys.dont_write_bytecode = True
from orvsd_central import app
app.run(debug=True)
