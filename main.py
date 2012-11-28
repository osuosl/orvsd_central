from flask import Flask, render_template, request
from orvsd_central.misc.orvsd_central import User
import re

app = Flask(__name__)

@app.route("/")
def main_page():
    return reports()

@app.route("/report")
def report():
    return "A page for reports"

@app.route("/register", methods=['GET', 'POST'])
def register():
    user = True
    message = ""

    if request.method == "POST": 
        print request.form        
        # Can not test until the inital migration is pushed. 
        if User.query.filter_by(username=request.form['username']).first ():
            message="This username already exists!\n"
        elif request.form['password'] is not request.form['confirm_password']:
            message="The passwords provided did not match!\n"
        elif not re.match('^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$', request.form['email']):
            message="Invalid email address!\n"
        else:
            #Add user to db
            message=request.form['username']+" has been added successfully!\n"

    #Check for a good username
    return render_template('register.html', user=user, message=message)

if __name__ == "__main__":
    app.run(debug=True)

