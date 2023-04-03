from flask import Flask,flash,redirect,request,url_for,render_template,session,send_file
from flask_session import Session
from flask_mysqldb import MySQL
from otp import genotp
from mail import sendmail
import random
from io import BytesIO
app=Flask(__name__)
app.secret_key='876@#^%jh'
app.config['SESSION_TYPE']='filesystem'
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='admin'
app.config['MYSQL_DB']='spm'
Session(app)
mysql=MySQL(app)
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/registration',methods=['GET','POST'])
def register():
    if request.method=='POST':
        rollno=request.form['rollno']
        name=request.form['name']
        group=request.form['group']
        password=request.form['password']
        code=request.form['code']
        email=request.form['email']
        #define college code
        ccode='sdmsmkpbsc$#23'
        if ccode==code:
            cursor=mysql.connection.cursor()
            cursor.execute('select rollno from students')
            data=cursor.fetchall()
            cursor.execute('SELECT email from students')
            edata=cursor.fetchall()
            #print(data)
            if (rollno,) in data:
                flash('User already exists')
                return render_template('register.html')
            if (email,) in edata:
                flash('Email id already exists')
                return render_template('register.html')
            cursor.close()
            otp=genotp()
            sendmail(email,otp)
            return render_template('otp.html',otp=otp,rollno=rollno,name=name,group=group,password=password,email=email)
            return otp
        else:
            flash('Invalid college code')
            return render_template('register.html')
    return render_template('register.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('home'))
    if request.method=='POST':
        rollno=request.form['id']
        password=request.form['password']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from  students where rollno=%s and password=%s',[rollno,password])
        count=cursor.fetchone()[0]
        if count==0:
            flash('Invalid roll no or password')
            return render_template('login.html')
        else:
            session['user']=rollno
            return redirect(url_for('home'))
    return render_template('login.html')
@app.route('/studenthome')
def home():
    if session.get('user'):
        return render_template('home.html')
    else:
        return redirect(url_for('login'))
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return render_template('index')
    else:
        flash('already logged out')
        return redirect(url_for('login'))
    
@app.route('/otp/<otp>/<name>/<rollno>/<group>/<password>/<email>',methods=['GET','POST'])
def otp(otp,rollno,name,group,password,email):
    if request.method=='POST':
        uotp=request.form['otp']
        if otp==uotp:
            cursor=mysql.connection.cursor()
            lst=[rollno,name,group,password,email]
            query='insert into students values(%s,%s,%s,%s,%s)'
            cursor.execute(query,lst)
            mysql.connection.commit()
            cursor.close()
            flash('Details Registered')
            return redirect(url_for('login'))
        else:
            flash('Wrong OTP')
            return render_template('otp.html',otp=otp,rollno=rollno,name=name,group=group,password=password,email=email)
@app.route('/noteshome')
def notehome():
    if session.get('user'):
        rollno=session.get('user')
        cursor=mysql.connection.cursor()
        cursor.execute('select * from notes where rollno=%s',[rollno])
        notes_data=cursor.fetchall()
        print(notes_data)
        cursor.close()
        return render_template('addnotetable.html',data=notes_data)
    else:
        return redirect(url_for('login'))
@app.route('/addnotes',methods=['GET','POST'])
def addnote():
    if session.get('user'):
        if request.method=='POST':
            title=request.form['title']
            content=request.form['content']
            cursor=mysql.connection.cursor()
            rollno=session.get('user')
            cursor.execute('insert into notes(rollno,title,content)values(%s,%s,%s)',[rollno,title,content])
            mysql.connection.commit()
            cursor.close()
            flash(f'{title} added successfully')
            return redirect(url_for('notehome'))
        return render_template('notes.html')
    else:
        return redirect(url_for('login'))
@app.route('/viewnotes/<nid>')
def viewnotes(nid):
    cursor=mysql.connection.cursor()
    cursor.execute('select title,content from notes where nid=%s',[nid])
    data=cursor.fetchone()
    cursor.close()
    return render_template('notesview.html',data=data)
@app.route('/updatenotes/<nid>',methods=['GET','POST'])
def updatenotes(nid):
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('select title,content from notes where nid=%s',[nid])
        data=cursor.fetchone()
        cursor.close()
        if request.method=='POST':
            title=request.form['title']
            content=request.form['content']
            cursor=mysql.connection.cursor()
            cursor.execute('update notes set title=%s,content=%s where nid=%s',[title,content,nid])
            mysql.connection.commit()
            cursor.close()
            flash('Notes updated successfully')
            return redirect(url_for('notehome')) 
        return render_template('updatenotes.html',data=data)
    else:
        return redirect(url_for('login'))
@app.route('/deletenotes/<nid>')
def deletenotes(nid):
    cursor=mysql.connection.cursor()
    cursor.execute('delete from notes where nid=%s',[nid])
    mysql.connection.commit()
    cursor.close()
    flash(' Notes deleted successfully')
    return redirect(url_for('notehome'))
@app.route('/fileshome')
def fileshome():
    if session.get('user'):
        rollno=session.get('user')
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT fid,filename,date from files where rollno=%s',[rollno])
        data=cursor.fetchall()
        cursor.close()
        return render_template('fileuploadtable.html',data=data)
    else:
        return redirect(url_for('login'))
@app.route('/filehandling',methods=['POST'])
def filehandling():
    file=request.files['file']
    filename=file.filename
    bin_file=file.read()
    rollno=session.get('user')
    cursor=mysql.connection.cursor()
    cursor.execute('insert into files(rollno,filename,filedata) values(%s,%s,%s)',[rollno,filename,bin_file])
    mysql.connection.commit()
    cursor.close()
    flash(f'{filename} uploaded successfully')
    return redirect(url_for('fileshome'))
@app.route('/viewfile/<fid>')
def viewfile(fid):
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('select filename,filedata from files where fid=%s',[fid])
        data=cursor.fetchone()
        filename=data[0]
        bin_file=data[1]
        byte_data=BytesIO(bin_file)
        #return send_file(byte_data,download_name=filename,as_attachment=True)
        return send_file(byte_data,download_name=filename)
    else:
        return redirect(url_for('login'))
@app.route('/download/<fid>')
def download(fid):
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('select filename,filedata from files where fid=%s',[fid])
        data=cursor.fetchone()
        filename=data[0]
        bin_file=data[1]
        byte_data=BytesIO(bin_file)
        return send_file(byte_data,download_name=filename,as_attachment=True)
@app.route('/filedelete/<fid>')
def filedelete(fid):
    cursor=mysql.connection.cursor()
    cursor.execute('delete from files where fid=%s',[fid])
    mysql.connection.commit()
    cursor.close()
    flash('file deleted successfully')
    return redirect(url_for('fileshome'))
@app.route('/forgetpassword',methods=['GET','POST'])
def forget():
    if request.method=='POST':
        rollno=request.form['id']
        cursor=mysql.connection.cursor()
        cursor.execute('select rollno from students')
        data=cursor.fetchall()
        cursor.close()
        if(rollno,) in data:
            cursor.execute('select email from students where rollno=%s',[rollno])
            data=cursor.fetchone()[0]
            cursor.close()
            session['pass']=rollno
            send_mail(data,subject='Reset password',body=f'Reset thee password here-{request.base_url+"/"+url_for("createpassword")}')
        else:
            return 'Invalid user id'
    return render_template('forget.html')
@app.route('/createpassword')
def createpassword():
    if session.get('pass'):
        return render_template('newpassword.html')
    else:
        return redirect(url_for('login'))


app.run(debug=True,use_reloader=True)

 
