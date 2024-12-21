from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.utils import secure_filename
import os
from pathlib import Path
import os.path

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'jpeg', 'jpg', 'ppt', 'pptx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('عذراً، لم يتم اختيار أي ملف. يرجى اختيار ملف للرفع.')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('عذراً، لم يتم اختيار أي ملف. يرجى اختيار ملف للرفع.')
            return redirect(request.url)
        
        if not allowed_file(file.filename):
            flash('عذراً، نوع الملف غير مسموح به. الأنواع المسموحة هي: PDF, Word, PowerPoint, JPEG')
            return redirect(request.url)
        
        try:
            file_name = request.form.get('file-name', '').strip()
            ext = file.filename.rsplit('.', 1)[1].lower()
            
            if not file_name:
                file_name = Path(file.filename).stem
            
            filename = secure_filename(f"{file_name}.{ext}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save the uploaded file
            file.save(file_path)
            flash('تم رفع الملف بنجاح! يمكنك الآن مشاهدته في صفحة عرض الملفات.')
            return redirect(url_for('view'))
            
        except Exception as e:
            print(f"Upload error: {e}")
            flash('حدث خطأ أثناء رفع الملف. يرجى المحاولة مرة أخرى.')
            return redirect(request.url)
            
    return render_template('upload.html')

@app.route('/view')
def view():
    try:
        files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) 
                if not f.startswith('.') and os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], f))]
        return render_template('view.html', files=files)
    except Exception as e:
        print(f"Error listing files: {e}")
        return render_template('view.html', files=[])

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin@4321':
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        flash('خطأ في اسم المستخدم أو كلمة المرور')
    return render_template('admin.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('admin_dashboard.html', files=files)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('home'))

@app.route('/delete_file/<filename>')
def delete_file(filename):
    if not session.get('admin'):
        return redirect(url_for('admin'))
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('تم حذف الملف بنجاح')
    except:
        flash('حدث خطأ أثناء حذف الملف')
    return redirect(url_for('admin_dashboard'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    try:
        # Add Content-Disposition header for PowerPoint files
        if filename.lower().endswith(('.ppt', '.pptx')):
            return send_from_directory(
                app.config['UPLOAD_FOLDER'], 
                filename,
                as_attachment=True  # This will force download
            )
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        print(f"Error serving file: {e}")
        flash('عذراً، لم يتم العثور على الملف')
        return redirect(url_for('view'))

@app.route('/debug/files')
def debug_files():
    try:
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        full_paths = [os.path.join(app.config['UPLOAD_FOLDER'], f) for f in files]
        exists = [os.path.exists(p) for p in full_paths]
        return {
            'upload_folder': app.config['UPLOAD_FOLDER'],
            'exists': os.path.exists(app.config['UPLOAD_FOLDER']),
            'files': files,
            'full_paths': full_paths,
            'file_exists': exists
        }
    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    # Create a .gitkeep file to ensure the directory is tracked by git
    with open(os.path.join(app.config['UPLOAD_FOLDER'], '.gitkeep'), 'a'):
        pass
    app.run(debug=True) 