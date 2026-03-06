from datetime import datetime
from flask import Flask, jsonify, request, session,send_file
from reportlab.pdfgen import canvas
from docx import Document
import os.path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3
from werkzeug.utils import secure_filename
from fileinput import filename

UPLOAD_FOLDER = 'uploads'
app = Flask(__name__)
app.secret_key = "ashokkumaryadav"


# ---------------- DATABASE INIT ---------------- #

def init_db():
    conn = sqlite3.connect('notebook.db')
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS user(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        dob TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        delete_request_at DATETIME,
        is_deleted INTEGER DEFAULT 0
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS notebook(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT DEFAULT 'new_notebook',
        content TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        user_id INTEGER,
        is_deleted INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES user(id) ON DELETE CASCADE
    )
    ''')
    cur.execute('''CREATE TABLE user_profile(id INTEGER  PRIMARY KEY AUTOINCREMENT, user_id INTEGER UNIQUE, dob TEXT, mobile TEXT, photo_path TEXT, secret_key TEXT, bio TEXT, FOREIGN KEY(user_id) REFERENCES user(id) ON DELETE CASCADE )''')

    conn.commit()
    conn.close()


init_db()


# ---------------- HOME ---------------- #

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to Notebook API"})


# ---------------- SIGNUP ---------------- #

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    dob = data.get('dob')

    if not name or not email or not password:
        return jsonify({"message": "All fields required"}), 400

    hashed = generate_password_hash(password)

    conn = sqlite3.connect('notebook.db')
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO user(name,email,password,dob) VALUES(?,?,?,?)",
            (name, email, hashed, dob)
        )
        conn.commit()
    except:
        return jsonify({"message": "Email already exists"}), 400

    conn.close()

    return jsonify({"message": "User created"})


# ---------------- LOGIN ---------------- #

@app.route('/login', methods=['POST'])
def login():

    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    conn = sqlite3.connect('notebook.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    user = cur.execute(
        "SELECT * FROM user WHERE email=?",
        (email,)
    ).fetchone()

    if not user:
        return jsonify({"message": "User not found"}), 404

    if not check_password_hash(user['password'], password):
        return jsonify({"message": "Wrong password"}), 401

    if user['is_deleted'] == 1:
        return jsonify({"message": "Account scheduled for deletion. Recover within 30 days."})

    session['user_id'] = user['id']

    conn.close()

    return jsonify({"message": "Login successful"})


# ---------------- CREATE NOTE ---------------- #

@app.route('/create_note', methods=['POST'])
def create_note():

    if not session.get('user_id'):
        return jsonify({"message": "Login required"}), 401

    data = request.get_json()

    title = data.get('title')
    content = data.get('content')

    conn = sqlite3.connect('notebook.db')
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO notebook(title,content,user_id) VALUES(?,?,?)",
        (title, content, session['user_id'])
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Note created"})


# ---------------- SHOW NOTES ---------------- #

@app.route('/notes', methods=['GET'])
def show_notes():

    if not session.get('user_id'):
        return jsonify({"message": "Login required"}), 401

    conn = sqlite3.connect('notebook.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    notes = cur.execute(
        "SELECT * FROM notebook WHERE user_id=? AND is_deleted=0",
        (session['user_id'],)
    ).fetchall()

    conn.close()

    data = [dict(row) for row in notes]

    return jsonify({"notes": data})


# ---------------- UPDATE NOTE ---------------- #

@app.route('/update_note/<int:id>', methods=['PUT'])
def update_note(id):

    if not session.get('user_id'):
        return jsonify({"message": "Login required"}), 401

    data = request.get_json()

    title = data.get('title')
    content = data.get('content')

    conn = sqlite3.connect('notebook.db')
    cur = conn.cursor()

    cur.execute(
        "UPDATE notebook SET title=?,content=? WHERE id=? AND user_id=?",
        (title, content, id, session['user_id'])
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Note updated"})


# ---------------- MOVE TO TRASH ---------------- #

@app.route('/move_to_trash/<int:id>', methods=['PUT'])
def move_to_trash(id):

    if not session.get('user_id'):
        return jsonify({"message": "Login required"}), 401

    conn = sqlite3.connect('notebook.db')
    cur = conn.cursor()

    cur.execute(
        "UPDATE notebook SET is_deleted=1 WHERE id=? AND user_id=?",
        (id, session['user_id'])
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Moved to trash"})


# ---------------- TRASH NOTES ---------------- #

@app.route('/trash', methods=['GET'])
def trash():

    if not session.get('user_id'):
        return jsonify({"message": "Login required"}), 401

    conn = sqlite3.connect('notebook.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    notes = cur.execute(
        "SELECT * FROM notebook WHERE user_id=? AND is_deleted=1",
        (session['user_id'],)
    ).fetchall()

    conn.close()

    data = [dict(row) for row in notes]

    return jsonify({"trash": data})


# ---------------- RESTORE NOTE ---------------- #

@app.route('/restore_note/<int:id>', methods=['PUT'])
def restore_note(id):

    conn = sqlite3.connect('notebook.db')
    cur = conn.cursor()

    cur.execute(
        "UPDATE notebook SET is_deleted=0 WHERE id=? AND user_id=?",
        (id, session['user_id'])
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Note restored"})


# ---------------- SEARCH ---------------- #

@app.route('/search', methods=['POST'])
def search():

    if not session.get('user_id'):
        return jsonify({"message": "Login required"}), 401

    query = request.json.get('query')

    conn = sqlite3.connect('notebook.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    notes = cur.execute("""
    SELECT * FROM notebook
    WHERE user_id=? AND is_deleted=0
    AND (title LIKE ? OR content LIKE ?)
    """, (
        session['user_id'],
        '%' + query + '%',
        '%' + query + '%'
    )).fetchall()

    conn.close()

    result = [dict(row) for row in notes]

    return jsonify({"results": result})


# ---------------- FILTER ---------------- #

@app.route('/filter', methods=['POST'])
def filter_notes():

    method = request.json.get('method')

    conn = sqlite3.connect('notebook.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if method == "latest":
        query = "ORDER BY created_at DESC"

    elif method == "oldest":
        query = "ORDER BY created_at ASC"

    elif method == "title":
        query = "ORDER BY title ASC"

    else:
        return jsonify({"message": "Invalid method"})

    notes = cur.execute(
        f"SELECT * FROM notebook WHERE user_id=? AND is_deleted=0 {query}",
        (session['user_id'],)
    ).fetchall()

    conn.close()

    result = [dict(row) for row in notes]

    return jsonify({"notes": result})


# ---------------- DELETE ACCOUNT REQUEST ---------------- #

@app.route('/delete_account', methods=['POST'])
def delete_account():

    conn = sqlite3.connect('notebook.db')
    cur = conn.cursor()

    cur.execute(
        "UPDATE user SET is_deleted=1,delete_request_at=? WHERE id=?",
        (datetime.now(), session['user_id'])
    )

    conn.commit()
    conn.close()

    session.clear()

    return jsonify({"message": "Account will be deleted after 30 days"})


# ---------------- RECOVER ACCOUNT ---------------- #

@app.route('/recover_account', methods=['POST'])
def recover_account():

    data = request.json
    email = data.get('email')
    password = data.get('password')

    conn = sqlite3.connect('notebook.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    user = cur.execute(
        "SELECT * FROM user WHERE email=?",
        (email,)
    ).fetchone()

    if not user:
        return jsonify({"message": "User not found"})

    if not check_password_hash(user['password'], password):
        return jsonify({"message": "Wrong password"})

    cur.execute(
        "UPDATE user SET is_deleted=0,delete_request_at=NULL WHERE email=?",
        (email,)
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Account recovered"})


# ---------------- AUTO DELETE AFTER 30 DAYS ---------------- #

def delete_old_users():

    conn = sqlite3.connect('notebook.db')
    cur = conn.cursor()

    cur.execute("""
    DELETE FROM user
    WHERE is_deleted=1
    AND delete_request_at <= datetime('now','-30 days')
    """)

    conn.commit()
    conn.close()



@app.route('/export_note/<int:id>', methods=['GET'])
def export_note(id):

    if not session.get('user_id'):
        return jsonify({"message":"login required"})

    user_id = session['user_id']

    filetype = request.args.get("type")   # pdf / docx

    conn = sqlite3.connect('notebook.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    note = cur.execute(
        "SELECT * FROM notebook WHERE id=? AND user_id=?",
        (id,user_id)
    ).fetchone()

    conn.close()

    if not note:
        return jsonify({"message":"note not found"})

    title = note['title']
    content = note['content']

    os.makedirs("exports", exist_ok=True)

    # -------- PDF EXPORT -------- #

    if filetype == "pdf":

        filepath = f"exports/{title}.pdf"

        c = canvas.Canvas(filepath)
        c.setFont("Helvetica",12)

        y = 800
        for line in content.split("\n"):
            c.drawString(50,y,line)
            y -= 20

        c.save()

        return send_file(filepath, as_attachment=True)


    # -------- DOCX EXPORT -------- #

    elif filetype == "docx":

        filepath = f"exports/{title}.docx"

        doc = Document()
        doc.add_heading(title, level=1)
        doc.add_paragraph(content)

        doc.save(filepath)

        return send_file(filepath, as_attachment=True)

    else:
        return jsonify({"message":"invalid file type"})
        
        
@app.route('/share_note/<int:id>', methods=['POST'])
def share_note(id):

    if not session.get('user_id'):
        return jsonify({"message":"login required"})

    user_id = session['user_id']

    data = request.get_json()
    receiver_email = data['email']

    conn = sqlite3.connect('notebook.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    note = cur.execute(
        "SELECT * FROM notebook WHERE id=? AND user_id=?",
        (id,user_id)
    ).fetchone()

    conn.close()

    if not note:
        return jsonify({"message":"note not found"})

    title = note['title']
    content = note['content']

    # -------- EMAIL CONFIG -------- #

    sender_email = "yourgmail@gmail.com"
    sender_password = "your_app_password"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"Shared Note: {title}"

    body = f"""
Title: {title}

Content:
{content}
"""

    msg.attach(MIMEText(body,'plain'))

    try:

        server = smtplib.SMTP('smtp.gmail.com',587)
        server.starttls()
        server.login(sender_email,sender_password)

        server.send_message(msg)
        server.quit()

        return jsonify({"message":"note shared successfully via email"})

    except Exception as e:
        return jsonify({"error":str(e)})
        
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
                
scheduler = BackgroundScheduler()
scheduler.add_job(delete_old_users, 'interval', hours=24)
scheduler.start()


# ---------------- RUN SERVER ---------------- #

if __name__ == "__main__":
    app.run(debug=True)
