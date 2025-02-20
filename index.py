from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = os.path.abspath('uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# MongoDB setup
client = MongoClient('mongodb+srv://cluster0.zs0hh34.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=Cluster0')#حط رابط الدلتا بيز بتاعتك
db = client['file_sharing']
users = db.users
files = db.files

# Create admin user if not exists
if not users.find_one({'username': 'admin'}):
    users.insert_one({
        'username': 'admin',
        'password': generate_password_hash('admin'),
        'is_admin': True,
        'created_at': datetime.now()
    })

# ========================
# CSS Styles
# ========================
common_css = '''
<style>
.btn-warning {
    background: #ffc107;
    color: black;
}

.btn-warning:hover {
    background: #e0a800;
}

.btn-secondary {
    background: #6c757d;
    color: white;
    cursor: not-allowed;
}
    :root {
        --primary: #2A6F97;
        --secondary: #468FAF;
        --light: #F0F4F8;
        --dark: #1A2F3D;
    }

    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        font-family: 'Inter', sans-serif;
    }

    body {
        background: var(--light);
        color: var(--dark);
    }

    .container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem 1rem;
    }

    .header {
        background: white;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        padding: 1rem 0;
        margin-bottom: 2rem;
    }

    .nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 1rem;
    }

    .logo {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--primary);
    }

    .nav-links a {
        color: var(--dark);
        text-decoration: none;
        margin-left: 2rem;
        font-weight: 500;
        transition: color 0.3s;
    }

    .nav-links a:hover {
        color: var(--primary);
    }

    .card {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 2rem;
    }

    .btn {
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 500;
        transition: transform 0.2s;
    }

    .btn-primary {
        background: var(--primary);
        color: white;
    }

    .btn-danger {
        background: #DC3545;
        color: white;
    }

    .file-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 1.5rem;
    }

    .file-table th,
    .file-table td {
        padding: 1rem;
        text-align: left;
        border-bottom: 1px solid #eee;
    }

    .file-table th {
        background: var(--light);
    }

    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 2rem;
        margin-top: 2rem;
    }

    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }

    .stat-card h3 {
        color: var(--secondary);
        margin-bottom: 0.5rem;
    }

    .download-page {
        text-align: center;
        padding: 4rem 0;
    }

    .download-box {
        max-width: 600px;
        margin: 0 auto;
        background: white;
        padding: 3rem;
        border-radius: 16px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    }

    .file-icon {
        font-size: 4rem;
        color: var(--primary);
        margin-bottom: 1rem;
    }
</style>
'''

# ========================
# Routes
# ========================

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('signin'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if users.find_one({'username': username}):
            return render_template_string(f'''
                {common_css}
                <div class="container">
                    <div class="card">
                        <h2>Username already exists!</h2>
                        <a href="/signup" class="btn btn-primary">Try Again</a>
                    </div>
                </div>
            ''')
        users.insert_one({
            'username': username,
            'password': generate_password_hash(password),
            'is_admin': False,
            'created_at': datetime.now()
        })
        return redirect(url_for('signin'))
    
    return render_template_string(f'''
        {common_css}
        <div class="header">
            <div class="nav">
                <div class="logo">FileShare</div>
            </div>
        </div>
        <div class="container">
            <div class="card">
                <h2>Create Account</h2>
                <form method="POST" style="margin-top: 1.5rem;">
                    <input type="text" name="username" placeholder="Username" required 
                        style="width: 100%; padding: 0.75rem; margin-bottom: 1rem; border: 1px solid #ddd; border-radius: 8px;">
                    <input type="password" name="password" placeholder="Password" required
                        style="width: 100%; padding: 0.75rem; margin-bottom: 1.5rem; border: 1px solid #ddd; border-radius: 8px;">
                    <button type="submit" class="btn btn-primary">Sign Up</button>
                </form>
                <p style="margin-top: 1rem;">Already have an account? <a href="/signin">Sign In</a></p>
            </div>
        </div>
    ''')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            session['is_admin'] = user.get('is_admin', False)
            return redirect(url_for('dashboard'))
        return render_template_string(f'''
            {common_css}
            <div class="container">
                <div class="card">
                    <h2>Invalid credentials!</h2>
                    <a href="/signin" class="btn btn-primary">Try Again</a>
                </div>
            </div>
        ''')
    
    return render_template_string(f'''
        {common_css}
        <div class="header">
            <div class="nav">
                <div class="logo">FileShare</div>
            </div>
        </div>
        <div class="container">
            <div class="card">
                <h2>Welcome Back</h2>
                <form method="POST" style="margin-top: 1.5rem;">
                    <input type="text" name="username" placeholder="Username" required
                        style="width: 100%; padding: 0.75rem; margin-bottom: 1rem; border: 1px solid #ddd; border-radius: 8px;">
                    <input type="password" name="password" placeholder="Password" required
                        style="width: 100%; padding: 0.75rem; margin-bottom: 1.5rem; border: 1px solid #ddd; border-radius: 8px;">
                    <button type="submit" class="btn btn-primary">Sign In</button>
                </form>
                <p style="margin-top: 1rem;">New user? <a href="/signup">Create Account</a></p>
            </div>
        </div>
    ''')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('signin'))
    
    user_files = list(files.find({'uploader': session['username']}))
    
    table_rows = []
    for file in user_files:
        # معالجة التواريخ المفقودة
        upload_date = file.get('upload_date', datetime.now())
        upload_date_str = upload_date.strftime("%Y-%m-%d %H:%M") if isinstance(upload_date, datetime) else 'N/A'
        
        row = f'''
        <tr>
            <td>{file["filename"]}</td>
            <td>{upload_date_str}</td>
            <td>{file.get("downloads", 0)}</td>
            <td>
                <a href="/download/{file["file_id"]}" class="btn btn-primary">Get Link</a>
                <a href="/delete/{file["file_id"]}" class="btn btn-danger">Delete</a>
            </td>
        </tr>
        '''
        table_rows.append(row)
    
    return render_template_string(f'''
        {common_css}
        <div class="header">
            <div class="nav">
                <div class="logo">FileShare</div>
                <div class="nav-links">
                    <a href="/dashboard">Dashboard</a>
                    <a href="/logout">Logout</a>
                </div>
            </div>
        </div>
        <div class="container">
            <div class="card">
                <h2>📁 Your Files</h2>
                <form method="POST" action="/upload" enctype="multipart/form-data" 
                    style="margin: 2rem 0; border: 2px dashed #ddd; padding: 2rem; text-align: center; border-radius: 12px;">
                    <input type="file" name="file" required 
                        style="margin-bottom: 1rem;">
                    <button type="submit" class="btn btn-primary">Upload File</button>
                </form>
                
                <table class="file-table">
                    <tr>
                        <th>File Name</th>
                        <th>Upload Date</th>
                        <th>Downloads</th>
                        <th>Actions</th>
                    </tr>
                    {''.join(table_rows)}
                </table>
            </div>
        </div>
    ''')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'username' not in session:
        return redirect(url_for('signin'))
    
    file = request.files['file']
    if file:
        file_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_id))
        files.insert_one({
            'file_id': file_id,
            'filename': filename,
            'uploader': session['username'],
            'downloads': 0,
            'upload_date': datetime.now()
        })
    return redirect(url_for('dashboard'))

@app.route('/download/<file_id>')
def download_file(file_id):
    file_data = files.find_one({'file_id': file_id})
    if not file_data:
        return render_template_string(f'''
            {common_css}
            <div class="header">
                <div class="nav">
                    <div class="logo">FileShare</div>
                    <div class="nav-links">
                        <a href="/dashboard">Dashboard</a>
                        <a href="/logout">Logout</a>
                    </div>
                </div>
            </div>
            <div class="download-page">
                <div class="download-box">
                    <h2>File Not Found</h2>
                    <p>The requested file does not exist.</p>
                </div>
            </div>
        '''), 404
    
    files.update_one({'file_id': file_id}, {'$inc': {'downloads': 1}})
    
    return render_template_string(f'''
        {common_css}
        <div class="header">
            <div class="nav">
                <div class="logo">FileShare</div>
                <div class="nav-links">
                    <a href="/dashboard">Dashboard</a>
                    <a href="/logout">Logout</a>
                </div>
            </div>
        </div>
        <div class="download-page">
            <div class="download-box">
                <div class="file-icon">📁</div>
                <h1>{file_data["filename"]}</h1>
                
                <div class="stats-grid" style="margin: 2rem 0;">
                    <div class="stat-card">
                        <h3>Uploaded By</h3>
                        <p>{file_data["uploader"]}</p>
                    </div>
                    
                    <div class="stat-card">
                        <h3>Total Downloads</h3>
                        <p>{file_data["downloads"] + 1}</p>
                    </div>
                    
                    <div class="stat-card">
                        <h3>Upload Date</h3>
                        <p>{file_data["upload_date"].strftime("%Y-%m-%d %H:%M")}</p>
                    </div>
                </div>

                <a href="/download-file/{file_id}" class="btn btn-primary" style="font-size: 1.2rem;">
                    Download Now
                </a>
            </div>
        </div>
    ''')

@app.route('/download-file/<file_id>')
def direct_download(file_id):
    file_data = files.find_one({'file_id': file_id})
    if not file_data:
        return 'File not found', 404
    
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        file_id,
        as_attachment=True,
        download_name=file_data['filename']
    )

from bson import ObjectId
from flask import abort

@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        return render_template_string(f'''
            {common_css}
            <div class="container">
                <div class="card">
                    <h2>⚠️ Access Denied</h2>
                    <p>You must be an admin to view this page</p>
                    <a href="/dashboard" class="btn btn-primary">Return to Dashboard</a>
                </div>
            </div>
        '''), 403
    
    try:
        all_files = list(files.find())
        all_users = list(users.find())
        
        # بناء جدول الملفات
        files_table = []
        for file in all_files:
            files_table.append(f'''
                <tr>
                    <td>{file.get("filename", "Unnamed File")}</td>
                    <td>{file.get("uploader", "Unknown")}</td>
                    <td>{file.get("downloads", 0)}</td>
                    <td>{(file.get("upload_date") or datetime.now()).strftime("%Y-%m-%d %H:%M")}</td>
                    <td>
                        <a href="/delete/{file["file_id"]}" class="btn btn-danger">Delete</a>
                    </td>
                </tr>
            ''')
        
        # بناء جدول المستخدمين مع التعديلات الجديدة
        users_table = []
        for user in all_users:
            user_id = str(user["_id"])
            is_admin = user.get("is_admin", False)
            
            action_btn = f'''
                <a href="/promote-user/{user_id}" class="btn {'btn-success' if not is_admin else 'btn-warning'}">
                    {'Promote' if not is_admin else 'Demote'}
                </a>
                
                <a href="/delete-user/{user_id}" class="btn btn-danger">Delete</a>
            ''' if user["username"] != "admin" else '<span class="btn btn-secondary">Root Admin</span>'
            
            users_table.append(f'''
                <tr>
                    <td>{user.get("username", "N/A")}</td>
                    <td>{"✅" if is_admin else "❌"}</td>
                    <td>{(user.get("created_at") or datetime.now()).strftime("%Y-%m-%d %H:%M")}</td>
                    <td>
                        {action_btn}
                        
                    </td>
                </tr>
            ''')
        
        return render_template_string(f'''
            {common_css}
            <div class="header">
                <div class="nav">
                    <div class="logo">Admin Panel</div>
                    <div class="nav-links">
                        <a href="/admin/settings" class="btn btn-primary">⚙️ Settings</a>
                        <a href="/create-admin" class="btn btn-primary">➕ New Admin</a>
                        <a href="/dashboard" class="btn">User Dashboard</a>
                        <a href="/logout" class="btn btn-danger">Logout</a>
                    </div>
                </div>
            </div>
            
            <div class="container">
                <div class="card">
                    <h2>📁 All Files ({len(all_files)})</h2>
                    <table class="file-table">
                        <tr>
                            <th>Filename</th>
                            <th>Uploader</th>
                            <th>Downloads</th>
                            <th>Upload Date</th>
                            <th>Actions</th>
                        </tr>
                        {''.join(files_table)}
                    </table>
                </div>

                <div class="card" style="margin-top: 2rem;">
                    <h2>👥 All Users ({len(all_users)})</h2>
                    <table class="file-table">
                        <tr>
                            <th>Username</th>
                            <th>Admin</th>
                            <th>Join Date</th>
                            <th>Actions</th>
                        </tr>
                        {''.join(users_table)}
                    </table>
                </div>
            </div>
        ''')
    
    except Exception as e:
        return render_template_string(f'''
            {common_css}
            <div class="container">
                <div class="card">
                    <h2>🚨 Error Occurred</h2>
                    <p>{str(e)}</p>
                    <a href="/admin" class="btn btn-primary">Try Again</a>
                </div>
            </div>
        '''), 500

@app.route('/promote-user/<user_id>')
def toggle_admin_status(user_id):
    if not session.get('is_admin'):
        return abort(403)
    
    try:
        user = users.find_one({'_id': ObjectId(user_id)})
        new_status = not user.get('is_admin', False)
        
        users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'is_admin': new_status}}
        )
        
        return redirect(url_for('admin_dashboard'))
    except:
        return abort(404)

@app.route('/create-admin', methods=['GET', 'POST'])
def create_admin():
    if not session.get('is_admin'):
        return render_template_string(f'''
            {common_css}
            <div class="container">
                <div class="card">
                    <h2>صلاحية مرفوضة!</h2>
                    <p>يجب أن تكون مديرًا للوصول إلى هذه الصفحة</p>
                    <a href="/admin" class="btn btn-primary">العودة للوحة التحكم</a>
                </div>
            </div>
        '''), 403

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if users.find_one({'username': username}):
            return render_template_string(f'''
                {common_css}
                <div class="container">
                    <div class="card">
                        <h2>اسم المستخدم موجود مسبقاً!</h2>
                        <a href="/create-admin" class="btn btn-primary">المحاولة مرة أخرى</a>
                    </div>
                </div>
            ''')
        
        users.insert_one({
            'username': username,
            'password': generate_password_hash(password),
            'is_admin': True,
            'created_at': datetime.now(),
            'last_login': datetime.now()
        })
        return redirect(url_for('admin_dashboard'))
    
    return render_template_string(f'''
        {common_css}
        <div class="header">
            <div class="nav">
                <div class="logo">إنشاء مدير جديد</div>
                <div class="nav-links">
                    <a href="/admin" class="btn">العودة</a>
                    <a href="/logout" class="btn btn-danger">تسجيل الخروج</a>
                </div>
            </div>
        </div>
        <div class="container">
            <div class="card">
                <h2>إنشاء حساب مدير جديد</h2>
                <form method="POST">
                    <div class="form-group">
                        <input type="text" name="username" placeholder="اسم المستخدم" required>
                    </div>
                    <div class="form-group">
                        <input type="password" name="password" placeholder="كلمة المرور" required>
                    </div>
                    <button type="submit" class="btn btn-primary">إنشاء الحساب</button>
                </form>
            </div>
        </div>
    ''')

@app.route('/delete/<file_id>')
def delete_file(file_id):
    if 'username' not in session:
        return redirect(url_for('signin'))
    
    file_data = files.find_one({'file_id': file_id})
    if not file_data:
        return 'File not found', 404
    
    if session.get('is_admin') or file_data['uploader'] == session['username']:
        files.delete_one({'file_id': file_id})
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file_id))
    
    return redirect(url_for('admin_dashboard' if session.get('is_admin') else 'dashboard'))
    
from bson import ObjectId

@app.route('/delete-user/<user_id>')
def delete_user(user_id):
    if not session.get('is_admin'):
        return abort(403)
    
    try:
        # حذف جميع ملفات المستخدم أولاً
        files.delete_many({'uploader': users.find_one({'_id': ObjectId(user_id)})['username']})
        
        # ثم حذف المستخدم
        users.delete_one({'_id': ObjectId(user_id)})
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        print(f"Error deleting user: {str(e)}")
        return abort(404)

@app.route('/promote-user/<user_id>')
def promote_user(user_id):
    if not session.get('is_admin'):
        return abort(403)
    
    try:
        users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'is_admin': True}}
        )
        return redirect(url_for('admin_dashboard'))
    except:
        return abort(404)

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if 'username' not in session or not session.get('is_admin'):
        return redirect(url_for('signin'))
    
    user = users.find_one({'username': session['username']})
    
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_username = request.form.get('new_username')
        new_password = request.form.get('new_password')
        
        # التحقق من كلمة المرور الحالية
        if not check_password_hash(user['password'], current_password):
            return render_template_string(f'''
                {common_css}
                <div class="container">
                    <div class="card">
                        <h2>كلمة المرور الحالية غير صحيحة!</h2>
                        <a href="/admin/settings" class="btn">المحاولة مرة أخرى</a>
                    </div>
                </div>
            ''')
        
        update_data = {}
        
        # تحديث اسم المستخدم إذا تم تغييره
        if new_username and new_username != user['username']:
            if users.find_one({'username': new_username}):
                return render_template_string(f'''
                    {common_css}
                    <div class="container">
                        <div class="card">
                            <h2>اسم المستخدم موجود مسبقاً!</h2>
                            <a href="/admin/settings" class="btn">المحاولة مرة أخرى</a>
                        </div>
                    </div>
                ''')
            update_data['username'] = new_username
            session['username'] = new_username
        
        # تحديث كلمة المرور إذا تم تغييرها
        if new_password:
            update_data['password'] = generate_password_hash(new_password)
        
        if update_data:
            users.update_one(
                {'_id': user['_id']},
                {'$set': update_data}
            )
        
        return redirect(url_for('admin_dashboard'))
    
    return render_template_string(f'''
        {common_css}
        <div class="header">
            <div class="nav">
                <div class="logo">إعدادات المدير</div>
                <div class="nav-links">
                    <a href="/admin" class="btn">العودة للوحة التحكم</a>
                    <a href="/logout" class="btn btn-danger">تسجيل الخروج</a>
                </div>
            </div>
        </div>
        
        <div class="container">
            <form class="profile-form" method="POST">
                <div class="form-group">
                    <label>اسم المستخدم الحالي: {user['username']}</label>
                    <input type="text" name="new_username" placeholder="اسم مستخدم جديد">
                </div>
                
                <div class="form-group">
                    <label>كلمة المرور الحالية</label>
                    <input type="password" name="current_password" required>
                </div>
                
                <div class="form-group">
                    <label>كلمة مرور جديدة (اختياري)</label>
                    <input type="password" name="new_password">
                </div>
                
                <div class="form-group">
                    <label>تأكيد كلمة المرور الجديدة</label>
                    <input type="password" name="confirm_password">
                </div>
                
                <div class="form-actions">
                    <button type="submit" class="btn btn-primary">حفظ التغييرات</button>
                </div>
            </form>
        </div>
    ''')

# في جزء عرض المستخدمين في الـ admin dashboard:
'''
<td>
    {% if not user.is_admin %}
    <a href="/promote-user/{{ user._id }}" class="btn btn-success">ترقية</a>
    {% endif %}
    <a href="/delete-user/{{ user._id }}" class="btn btn-danger" onclick="return confirm('هل أنت متأكد؟')">حذف</a>
</td>
'''

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('signin'))

if __name__ == '__main__':
    app.run(debug=True)
