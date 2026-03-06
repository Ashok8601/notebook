import os.path
import shutil
from datetime import datetime
from fileinput import filename

from flask import Flask,jsonify,request,session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app=Flask(__name__)
app.secret_key="ashokkumaryadav"
import sqlite3

UPLOAD_FOLDER = 'uploads'
conn=sqlite3.connect('notebook.db')
conn.row_factory=sqlite3.Row
cur=conn.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS user (id INTEGER PRIMARY KEY AUTOINCREMENT ,name TEXT, email TEXT NOT NULL UNIQUE , password TEXT NOT NULL,dob TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
cur.execute('''CREATE TABLE IF NOT EXISTS notebook (id INTEGER PRIMARY KEY AUTOINCREMENT ,title TEXT DEFAULT 'new_notebook', content TEXT ,created_at DATETIME DEFAULT CURRENT_TIMESTAMP,user_id INTEGER ,FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE)''')
cur.execute('''CREATE TABLE user_profile(id INTEGER  PRIMARY KEY AUTOINCREMENT, user_id INTEGER UNIQUE, dob TEXT, mobile TEXT, photo_path TEXT, secret_key TEXT, bio TEXT, FOREIGN KEY(user_id) REFERENCES user(id) ON DELETE CASCADE )''')
#cur.execute('ALTER TABLE user ADD COLUMN delete_request_at DATETIME')
#cur.execute('ALTER TABLE user ADD COLUMN is_deleted INTEGER DEFAULT 0')
conn.commit()
conn.close()
@app.route('/',methods=['GET'])
def home():
    return jsonify({"message":"welcome to the notebook app"})
@app.route('/signup',methods=['POST'])
def signup():
    data=request.get_json()
    name=data['name']
    email=data['email']
    password=data['password']
    dob=data['dob']
    if not name or not email or not password:
        return jsonify({"message":"please fill all fields"})
    hashed_password=generate_password_hash(password)
    conn=sqlite3.connect('notebook.db')
    conn.row_factory=sqlite3.Row
    cur=conn.cursor()
    cur.execute('''INSERT INTO user(name,email,password,dob,created_at)VALUES(?,?,?,?,?)''',(name,email,hashed_password,dob,datetime.now()))
    conn.commit()
    conn.close()
    return jsonify({"message":"user created successfully"})

@app.route('/login',methods=['POST'])
def login():
    data=request.get_json()
    email=data['email']
    password=data['password']
    if not email or not password:
        return jsonify({"message":"please fill all fields"})
    conn=sqlite3.connect('notebook.db')
    conn.row_factory=sqlite3.Row
    cur=conn.cursor()
    users=cur.execute('''SELECT * FROM user WHERE email=?''',(email,)).fetchone()
    if not users:
        return jsonify({"message":"user not found"})
    if not check_password_hash(users['password'],password):
        return jsonify({"message":"wrong password"})
    session['user_id']=users['id']
    conn.close()

    return jsonify({"message":"login successful"})

@app.route('/create_notebook',methods=['POST'])
def create_notebook():
    if not session.get('user_id'):
        return jsonify({"message":"login required"})
    id=session['user_id']
    data=request.get_json()
    title=data['title']
    content=data['content']
    conn=sqlite3.connect('notebook.db')
    conn.row_factory=sqlite3.Row
    cur=conn.cursor()
    cur.execute('INSERT INTO notebook (title,content,user_id) VALUES(?,?,?)',(title,content,id))
    conn.commit()
    conn.close()
    return jsonify({"message":"notebook created successfully"})
@app.route('/show_notebook',methods=['GET'])
def show_notebook():
    if not session.get('user_id'):
        return jsonify({"message":"login required"})
    id=session.get('user_id')
    conn=sqlite3.connect('notebook.db')
    conn.row_factory=sqlite3.Row
    cur=conn.cursor()
    notebooks=cur.execute('''SELECT * FROM notebook WHERE user_id =(?)''',(id,)).fetchall()
    if not notebooks:
        return jsonify({"message":"notebook not found"})
    data=[dict(row) for row in notebooks]
    return jsonify({"data":data})
@app.route('/update_notebook/<int:id>',methods=['PUT'])
def update_notebook(id):
    if not session.get('user_id'):
        return jsonify({"message":"login required"})
    user_id=session.get('user_id')
    data=request.get_json()
    title=data['title']
    content=data['content']
    conn=sqlite3.connect('notebook.db')
    conn.row_factory=sqlite3.Row
    cur=conn.cursor()
    cur.execute('UPDATE notebook SET title=?,content=? WHERE id=? AND user_id =?',(title,content,id,user_id))
    conn.commit()
    conn.close()
    return jsonify({"message":"notebook updated successfully"})

@app.route('/delete_notebook/<int:id>',methods=['DELETE'])
def delete_notebook(id):
    if not session.get('user_id'):
        return jsonify({"message":"login required"})
    user_id=session.get('user_id')
    conn=sqlite3.connect('notebook.db')
    cur=conn.cursor()
    cur.execute('DELETE FROM notebook WHERE id=? AND user_id =?',(id,user_id))
    conn.commit()
    conn.close()
    return jsonify({"message":"notebook deleted successfully"})

@app.route('/delete_user/<int:id>',methods=['POST'])
def delete_account(id):
    if not session.get('user_id'):
        return jsonify({"message":"login required"})
    user_id=session.get('user_id')
    conn=sqlite3.connect('notebook.db')
    cur=conn.cursor()
    cur.execute('UPDATE user SET delete_request_at =? ,is_deleted_at=1',(datatime.now(),user_id))
    conn.commit()
    session.clear()
    conn.close()
    return jsonify({"message":"Your will be deleted in next 30 days if you want to recover account you can do within 30 days "})

@app.route('/delete_account/<int:id>',methods=['DELETE'])
def delete_account(id):
    if not session.get('user_id'):
        return jsonify({"message":"login required"})
    user_id=session.get('user_id')
    conn=sqlite3.connect('notebook.db')
    cur=conn.cursor()
    cur.execute('DELETE FROM user WHERE id=?',(user_id,))

@app.route('/update_user/<int:id>', methods=['PUT'])
def update_account(id):

    if not session.get('user_id'):
        return jsonify({"message": "login required"})

    user_id = session.get('user_id')

    name = request.form.get('name')
    email = request.form.get('email')
    dob = request.form.get('dob')
    mobile = request.form.get('mobile')
    username = request.form.get('username')
    secret_key = request.form.get('secret_key')

    photo = request.files.get('photo')

    if not os.path.exists(UPLOAD_FOLDER):
        os.mkdir(UPLOAD_FOLDER)

    photo_path = None

    if photo:
        filename = secure_filename(photo.filename)
        photo_path = os.path.join(UPLOAD_FOLDER, filename)
        photo.save(photo_path)

    conn = sqlite3.connect('notebook.db')
    cur = conn.cursor()

    # update user table
    cur.execute("""
    UPDATE user 
    SET name=?, email=?, mobile=?, username=? 
    WHERE id=?
    """,(name,email,mobile,username,user_id))

    # check profile exist
    cur.execute("SELECT id FROM user_profile WHERE user_id=?", (user_id,))
    profile = cur.fetchone()

    if profile:
        # update profile
        cur.execute("""
        UPDATE user_profile
        SET dob=?, photo_path=?, secret_key=?
        WHERE user_id=?
        """,(dob,photo_path,secret_key,user_id))
    else:
        # insert profile
        cur.execute("""
        INSERT INTO user_profile (user_id,dob,photo_path,secret_key)
        VALUES (?,?,?,?)
        """,(user_id,dob,photo_path,secret_key))

    conn.commit()
    conn.close()

    return jsonify({"message":"updated successfully"})

@app.route('/update_password', methods=['PUT'])
def update_password():

    if not session.get('user_id'):
        return jsonify({"message": "login required"})

    user_id = session.get('user_id')

    data = request.get_json()
    email = data['email']
    old_password = data['old_password']
    new_password = data['password']

    conn = sqlite3.connect('notebook.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    result = cur.execute(
        'SELECT * FROM user WHERE id=?',
        (user_id,)
    ).fetchone()

    if not result:
        return jsonify({"message": "user not found"})

    # email check
    if email != result['email']:
        return jsonify({"message": "wrong email"})

    # old password check
    if not check_password_hash(result['password'], old_password):
        return jsonify({"message": "wrong old password"})

    # new password hash
    hashed_password = generate_password_hash(new_password)

    cur.execute(
        'UPDATE user SET password=? WHERE id=?',
        (hashed_password, user_id)
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "password updated successfully"})

@app.route('/profile_dashboard', methods=['GET'])
def profile_dashboard():

    if not session.get('user_id'):
        return jsonify({"message": "login required"})

    user_id = session.get('user_id')

    conn = sqlite3.connect('notebook.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    result = cur.execute("""
        SELECT 
            user.id,
            user.email,
            user_profile.name,
            user_profile.mobile,
            user_profile.username,
            user_profile.dob,
            user_profile.photo_path,
            user_profile.secret_key
        FROM user
        LEFT JOIN user_profile
        ON user.id = user_profile.user_id
        WHERE user.id = ?
    """, (user_id,)).fetchone()

    conn.close()

    if not result:
        return jsonify({"message": "user not found"})

    return jsonify(dict(result))

if __name__=='__main__':
    app.run(debug=True)