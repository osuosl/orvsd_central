import sys
sys.dont_write_bytecode = True
from site import app
app.run(debug=True)
