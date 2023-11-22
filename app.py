from flask import Flask, jsonify, render_template, request, url_for, flash, redirect, session
import joblib
import pandas as pd
import numpy as np
from pandas_profiling import ProfileReport
import mysql.connector
import os


app = Flask(__name__)
app.secret_key = os.urandom(24)
conn = mysql.connector.connect(host="localhost", user="saleslogin", password="123456", database="users")
cursor = conn.cursor()
# app.secret_key = "SECRETKEY"


def handle_missing_values(df):
    # Replace missing values with NaN
    df = df.replace(['', 'NA', 'N/A', 'NULL', 'NaN'], np.nan)

    # Remove rows with all missing values
    df = df.dropna(how='all')
    

    # Remove columns with more than 50% missing values
    threshold = len(df) * 0.5
    df = df.dropna(thresh=threshold, axis=1)

    # Fill missing values with the mean for numerical columns
    for col in df.select_dtypes(include=['float', 'int']).columns:
        df[col] = df[col].fillna(df[col].mean())

    # Fill missing values with the mode for categorical columns
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].fillna(df[col].mode()[0])

    return df

def clean_data(df):
    # Remove unnecessary columns
    unnecessary_columns = []
    df = df.drop(columns=unnecessary_columns)
    \
    # Convert date columns to datetime format
    for col in df.select_dtypes(include=['object']).columns:
        if 'date' in col.lower():
            df[col] = pd.to_datetime(df[col], infer_datetime_format=True)

    # Remove duplicates
    df = df.drop_duplicates()

    return df


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/logsin')
def logsin():
    return render_template('logsin.html')

@app.route('/uploader')
def uploader():
    if 'USER_ID' in session:
        return render_template('uploader.html')
    else:
        return redirect('/logsin')

@app.route("/Prediction")
def Prediction():
    return render_template("Prediction.html")

@app.route("/gallery")
def gallery():
    return render_template("gallery.html")

@app.route('/login_validation', methods=['POST'])
def login_validation():
    #if request.method == 'POST':
    email = request.form['email']
    password = request.form['password']

    cursor.execute("""SELECT * FROM `user` WHERE `E-MAIL` LIKE '{}' AND `PASSWORD` LIKE '{}'"""
                   .format(email, password))
    users = cursor.fetchall()

    print(users)
    if len(users) > 0:
        session['USER_ID'] = users[0][0]
        return redirect('/uploader')
    else:
        flash("USER NOT FOUND !! ENTER CREDENTIALS TO BE A MEMBER", "pass")
        # flash("NOT A VALID USER !! ENTER VALID CREDENTIALS", "pass")
        return redirect('/logsin')
    #return f"The email is {email} and the password is {password}"


@app.route('/signup_user', methods=['POST'])
def signup_user():
    name = request.form['sname']
    email = request.form['semail']
    password = request.form['spassword']

    cursor.execute("""INSERT INTO `user` (`USER_ID`, `USERNAME`, `E-MAIL`, `PASSWORD`) VALUES
                    (NULL, '{}', '{}', '{}')""".format(name, email, password))
    conn.commit()

    cursor.execute("""SELECT * FROM `user` WHERE `E-MAIL` LIKE '{}'""".format(email))
    user_added = cursor.fetchall()
    session['USER_ID'] = user_added[0][0]
    return redirect('/uploader')
    #return f'User generated successfully with name-{name} and email-{email} and password-{password}'
    #return render_template('signup.html')


@app.route('/logout')
def logout():
    session.pop('USER_ID')
    return redirect('/logsin')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    # Check if files are uploaded
    if 'train_file' not in request.files :
        flash('Please upload train dataset!', 'error')
        return redirect(url_for('uploader'))

    train_file = request.files['train_file']

    # Check if files are valid
    if train_file.filename == '':
        flash('Please select a valid train dataset!', 'error')
        return redirect(url_for('uploader'))

    # Load datasets into pandas DataFrames
    train_df = pd.read_csv(train_file)

    # Handle missing values
    train_df = handle_missing_values(train_df)

    # Clean the data
    train_df = clean_data(train_df)

    # Generate EDA reports using Pandas profiling
    train_profile = ProfileReport(train_df, title='Pandas Profiling Report', explorative=True)

    return render_template('report.html', train_profile_html=train_profile.to_html())


# # Define a route for error handling
# @app.errorhandler(Exception)
# def handle_error(error):
#     # Display a custom error message
#     flash('An error occurred: ' + str(error), 'error')
#     return redirect(url_for('uploader'))

# Define a route for the EDA page
@app.route('/report')
def report():
    return render_template('report.html')


@app.route('/predict',methods=['POST','GET'])
def result():

    item_weight= float(request.form['item_weight'])
    item_fat_content=float(request.form['item_fat_content'])
    item_visibility= float(request.form['item_visibility'])
    item_type= float(request.form['item_type'])
    item_mrp = float(request.form['item_mrp'])
    outlet_establishment_year= float(request.form['outlet_establishment_year'])
    outlet_size= float(request.form['outlet_size'])
    outlet_location_type= float(request.form['outlet_location_type'])
    outlet_type= float(request.form['outlet_type'])

    X= np.array([[ item_weight,item_fat_content,item_visibility,item_type,item_mrp,
                  outlet_establishment_year,outlet_size,outlet_location_type,outlet_type ]])

    scaler_path= r'C:\Users\hp\OneDrive\Desktop\MAJOR PROJECT\models\sc.sav'

    sc=joblib.load(scaler_path)

    X_std= sc.transform(X)

    model_path= r'C:\Users\hp\OneDrive\Desktop\MAJOR PROJECT\models\lr.sav'

    model= joblib.load(model_path)

    Y_pred=model.predict(X_std)

    return render_template('result.html', prediction=float(Y_pred))

if __name__ == "__main__":
    app.run(debug=True, port=9457)