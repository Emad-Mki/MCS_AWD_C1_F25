import os
import re
import uuid
import hashlib
import requests
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from db import get_connection

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-this-secret-in-production')

# إعدادات رفع الصور
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # حد أقصى 16 ميجابايت

# إنشاء المجلد إذا لم يكن موجوداً
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Unsplash API Configuration
# IMPORTANT: Keys added directly for PythonAnywhere compatibility. 
# For better security in the future, move these to Environment Variables.
UNSPLASH_ACCESS_KEY = "NdrEqeciEfQMmWjonxAn_yVQyMurc_wOhWP68frhvAo"
UNSPLASH_SECRET_KEY = "m_XTGgKcTBwz2UegVuGiodooDaMWtpBF8LlVV9e1mcI"
UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"
UNSPLASH_IMAGE_SIZE = '400x300'

# Keyword mapping for course titles to search terms
KEYWORD_MAPPING = {
    'python': 'python programming code',
    'web': 'web development website',
    'javascript': 'javascript coding programming',
    'data': 'data science analytics',
    'machine': 'machine learning artificial intelligence',
    'ai': 'artificial intelligence technology',
    'course': 'education learning classroom',
    'program': 'education training workshop',
    'service': 'business professional service',
    'design': 'design creative graphic',
    'mobile': 'mobile app smartphone',
    'cloud': 'cloud computing server',
    'database': 'database sql data',
    'security': 'cybersecurity protection lock',
    'network': 'networking internet connection',
    'devops': 'devops deployment server',
    'frontend': 'frontend web interface',
    'backend': 'backend server api',
    'full': 'fullstack development coding',
    'blockchain': 'blockchain cryptocurrency',
    'game': 'gaming video game',
    'android': 'android mobile development',
    'ios': 'ios iphone development',
    'react': 'react javascript frontend',
    'angular': 'angular typescript frontend',
    'vue': 'vue javascript frontend',
    'node': 'nodejs backend server',
    'django': 'django python web',
    'flask': 'flask python microframework',
    'sql': 'sql database query',
    'nosql': 'nosql database mongodb',
    'api': 'api rest webservice',
    'testing': 'software testing qa',
    'agile': 'agile scrum methodology',
    'management': 'project management business',
    'business': 'business corporate office',
    'marketing': 'marketing digital promotion',
    'finance': 'finance money investment',
    'accounting': 'accounting finance calculation',
}

def extract_keywords(title):
    """Extract keywords from title for image search"""
    title_lower = title.lower()
    keywords = []
    
    # Check for mapped keywords
    for key, value in KEYWORD_MAPPING.items():
        if key in title_lower:
            keywords.append(value)
    
    # If no mapped keywords, use title words
    if not keywords:
        # Remove special characters and split
        words = re.sub(r'[^a-zA-Z0-9\s]', '', title_lower).split()
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Return top 3 keywords joined
    return '+'.join(keywords[:3]) if keywords else 'education+learning'

def get_unsplash_image_url(search_query, seed=None):
    """Get image URL from Unsplash based on search query"""
    if not seed:
        seed = hashlib.md5(search_query.encode()).hexdigest()[:8]
    
    if UNSPLASH_ACCESS_KEY:
        # Use official API with access key
        try:
            response = requests.get(
                UNSPLASH_API_URL,
                params={
                    'query': search_query.replace('+', ' '),
                    'orientation': 'landscape',
                    'per_page': 1,
                    'seed': seed
                },
                headers={'Authorization': f'Bearer {UNSPLASH_ACCESS_KEY}'},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('results') and len(data['results']) > 0:
                    # Get the regular size URL (400x300)
                    photo = data['results'][0]
                    return photo['urls']['regular'] or photo['urls']['small'] or photo['urls']['full']
        except Exception as e:
            print(f"Unsplash API error: {e}")
            pass
    
    # Fallback to local default image if API fails
    return None

def get_or_generate_image_url(title, offering_id=None):
    """
    Get or generate image URL for an offering.
    Returns Unsplash image URL or fallback to local default image.
    """
    # Extract keywords from title
    search_query = extract_keywords(title)
    
    # Generate consistent seed from title
    seed = hashlib.md5(title.encode()).hexdigest()[:8]
    
    # Get Unsplash image URL
    image_url = get_unsplash_image_url(search_query, seed)
    
    # Return Unsplash URL if available, otherwise return None (template will use fallback)
    return image_url


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('login'))
        if not session.get('is_admin'):
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('home'))
        return view_func(*args, **kwargs)
    return wrapper


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not name or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html', name=name, email=email)

        if len(password) < 4:
            flash('Password must be at least 4 characters.', 'error')
            return render_template('register.html', name=name, email=email)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT id FROM users WHERE email = %s', (email,))
        existing = cur.fetchone()

        if existing:
            cur.close()
            conn.close()
            flash('This email is already registered.', 'error')
            return render_template('register.html', name=name, email=email)

        password_hash = generate_password_hash(password)
        cur.execute(
            'INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)',
            (name, email, password_hash)
        )
        conn.commit()
        cur.close()
        conn.close()

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Email and password are required.', 'error')
            return render_template('login.html', email=email)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, name, email, password_hash, is_admin FROM users WHERE email = %s', (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user or not check_password_hash(user[3], password):
            flash('Invalid email or password.', 'error')
            return render_template('login.html', email=email)

        session['user_id'] = user[0]
        session['user_name'] = user[1]
        session['is_admin'] = bool(user[4])  # Set is_admin flag in session
        flash('Logged in successfully.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_connection()
    cur = conn.cursor()
    # Fetch subscription details including the offering ID for the unsubscribe button
    cur.execute(
        '''
        SELECT offerings.id, offerings.title, offerings.description, DATE_FORMAT(subscriptions.date, '%%Y-%%m-%%d %%H:%%i')
        FROM subscriptions
        INNER JOIN offerings ON subscriptions.offering_id = offerings.id
        WHERE subscriptions.user_id = %s
        ORDER BY subscriptions.date DESC
        '''
        ,
        (session['user_id'],)
    )
    subscriptions = cur.fetchall()
    cur.close()
    conn.close()

    return render_template(
        'dashboard.html',
        user_name=session.get('user_name'),
        subscriptions=subscriptions
    )


@app.route('/offerings')
def offerings():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, title, description, availability, image_url FROM offerings WHERE is_active = TRUE ORDER BY id ASC')
    offerings_list = cur.fetchall()

    subscribed_ids = []
    if session.get('user_id'):
        cur.execute('SELECT offering_id FROM subscriptions WHERE user_id = %s', (session['user_id'],))
        subscribed_ids = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()

    # Generate image URLs based on course titles using Unsplash with keyword matching
    # Fallback to local default image if external service fails
    offerings_with_images = []
    for offering in offerings_list:
        # Use stored image_url from database if available, otherwise generate one
        if offering[4]:  # image_url from database (5th column, index 4)
            image_url = offering[4]
        else:
            # Use the new Image Matching layer to get relevant images
            image_url = get_or_generate_image_url(offering[1], offering[0])
        
        # Ensure we have a valid image URL or use fallback
        if not image_url:
            image_url = url_for('static', filename='images/default-course.svg', _external=True)
        
        offerings_with_images.append({
            'id': offering[0],
            'title': offering[1],
            'description': offering[2],
            'availability': offering[3] or 'available',
            'image': image_url,
            'fallback_image': url_for('static', filename='images/default-course.svg', _external=True)
        })

    return render_template(
        'offerings.html',
        offerings=offerings_with_images,
        subscribed_ids=subscribed_ids
    )


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


@app.route('/api/offerings', methods=['GET'])
def api_offerings():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, title, description, availability, image_url FROM offerings WHERE is_active = TRUE ORDER BY id ASC')
    rows = cur.fetchall()
    cur.close()
    conn.close()

    data = []
    for row in rows:
        # Use stored image_url from database if available, otherwise generate one
        if row[4]:  # image_url from database (5th column, index 4)
            image_url = row[4]
        else:
            # Use the new Image Matching layer to get relevant images
            image_url = get_or_generate_image_url(row[1], row[0])
        
        # Ensure we have a valid image URL or use fallback
        if not image_url:
            image_url = url_for('static', filename='images/default-course.svg', _external=True)
        
        data.append({
            'id': row[0],
            'title': row[1],
            'description': row[2],
            'availability': row[3] or 'available',
            'image': image_url,
            'fallback_image': url_for('static', filename='images/default-course.svg', _external=True)
        })
    return jsonify(data)


@app.route('/ajax/subscribe', methods=['POST'])
@login_required
def ajax_subscribe():
    offering_id = request.form.get('offering_id')

    if not offering_id or not offering_id.isdigit():
        return jsonify({'status': 'error', 'message': 'Invalid offering ID.'}), 400

    offering_id = int(offering_id)
    user_id = session['user_id']

    conn = get_connection()
    cur = conn.cursor()

    cur.execute('SELECT id FROM offerings WHERE id = %s AND is_active = TRUE', (offering_id,))
    offering = cur.fetchone()
    if not offering:
        cur.close()
        conn.close()
        return jsonify({'status': 'error', 'message': 'Offering not found.'}), 404

    cur.execute(
        'SELECT id FROM subscriptions WHERE user_id = %s AND offering_id = %s',
        (user_id, offering_id)
    )
    existing = cur.fetchone()
    if existing:
        cur.close()
        conn.close()
        return jsonify({'status': 'error', 'message': 'You are already subscribed to this offering.'}), 409

    cur.execute(
        'INSERT INTO subscriptions (user_id, offering_id) VALUES (%s, %s)',
        (user_id, offering_id)
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'status': 'success', 'message': 'Subscribed successfully.'})


@app.route('/ajax/unsubscribe', methods=['POST'])
@login_required
def ajax_unsubscribe():
    offering_id = request.form.get('offering_id')

    if not offering_id or not offering_id.isdigit():
        return jsonify({'status': 'error', 'message': 'Invalid offering ID.'}), 400

    offering_id = int(offering_id)
    user_id = session['user_id']

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        'DELETE FROM subscriptions WHERE user_id = %s AND offering_id = %s',
        (user_id, offering_id)
    )
    conn.commit()
    deleted_count = cur.rowcount
    cur.close()
    conn.close()

    if deleted_count > 0:
        return jsonify({'status': 'success', 'message': 'Unsubscribed successfully.'})
    else:
        return jsonify({'status': 'error', 'message': 'Subscription not found.'}), 404



if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true')


# Admin Routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, title, description, availability, image_url, is_active FROM offerings ORDER BY id DESC')
    offerings = cur.fetchall()
    cur.close()
    conn.close()
    
    # Format offerings for template
    offerings_list = []
    for offering in offerings:
        offerings_list.append({
            'id': offering[0],
            'title': offering[1],
            'description': offering[2],
            'availability': offering[3] or 'available',
            'image_url': offering[4],
            'is_active': offering[5]
        })
    
    return render_template('admin.html', offerings=offerings_list)


@app.route('/admin/add', methods=['POST'])
@admin_required
def admin_add_offering():
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    availability = request.form.get('availability', 'available')
    image_url = request.form.get('image_url', '').strip()
    is_active = request.form.get('is_active') == 'on'
    
    # Handle file upload
    if 'image_file' in request.files:
        file = request.files['image_file']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add unique prefix to avoid filename conflicts
            unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            # Store relative URL path
            image_url = url_for('static', filename=f'uploads/{unique_filename}', _external=True)
    
    if not title or not description:
        flash('Title and description are required.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # If no image URL provided (neither file nor URL), generate one automatically
    if not image_url or image_url.strip() == '':
        image_url = get_or_generate_image_url(title)
    else:
        # Clean and validate the image URL (only if it's not a local uploaded file)
        if image_url.startswith('http://') or image_url.startswith('https://'):
            # Remove leading slash if present (e.g., /https://... -> https://...)
            if image_url.startswith('/http') or image_url.startswith('/https'):
                image_url = image_url[1:]
            # Ensure URL starts with http:// or https://
            if not image_url.startswith('http://') and not image_url.startswith('https://'):
                image_url = 'https://' + image_url
    
    # Ensure image_url is not None
    if not image_url:
        image_url = None  # Template will use fallback
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO offerings (title, description, availability, image_url, is_active) VALUES (%s, %s, %s, %s, %s)',
        (title, description, availability, image_url, is_active)
    )
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Offering added successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/update/<int:offering_id>', methods=['POST'])
@admin_required
def admin_update_offering(offering_id):
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    availability = request.form.get('availability', 'available')
    image_url = request.form.get('image_url', '').strip()
    is_active = request.form.get('is_active') == 'on'
    
    if not title or not description:
        flash('Title and description are required.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Handle file upload for update
    uploaded_image_url = None
    if 'image_file' in request.files:
        file = request.files['image_file']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add unique prefix to avoid filename conflicts
            unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            # Store relative URL path
            uploaded_image_url = url_for('static', filename=f'uploads/{unique_filename}', _external=True)
    
    # Use uploaded image if provided, otherwise use URL from form or generate automatically
    if uploaded_image_url:
        image_url = uploaded_image_url
    elif not image_url or image_url.strip() == '':
        image_url = get_or_generate_image_url(title)
    else:
        # Clean and validate the image URL (only if it's not a local uploaded file)
        if image_url.startswith('http://') or image_url.startswith('https://'):
            # Remove leading slash if present (e.g., /https://... -> https://...)
            if image_url.startswith('/http') or image_url.startswith('/https'):
                image_url = image_url[1:]
            # Ensure URL starts with http:// or https://
            if not image_url.startswith('http://') and not image_url.startswith('https://'):
                image_url = 'https://' + image_url
    
    # Ensure image_url is not None
    if not image_url:
        image_url = None  # Template will use fallback
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        'UPDATE offerings SET title=%s, description=%s, availability=%s, image_url=%s, is_active=%s WHERE id=%s',
        (title, description, availability, image_url, is_active, offering_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Offering updated successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/delete/<int:offering_id>', methods=['POST'])
@admin_required
def admin_delete_offering(offering_id):
    conn = get_connection()
    cur = conn.cursor()
    
    # First delete any subscriptions related to this offering
    cur.execute('DELETE FROM subscriptions WHERE offering_id = %s', (offering_id,))
    
    # Then delete the offering
    cur.execute('DELETE FROM offerings WHERE id = %s', (offering_id,))
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Offering deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))
