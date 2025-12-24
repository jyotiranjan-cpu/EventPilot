from flask import Flask, request, session, render_template, redirect, url_for, flash
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText
from threading import Thread
import random
from datetime import datetime, timedelta
import os
import uuid


app = Flask(__name__)
app.secret_key = "Jyoti2005"

# --- CONFIGURATION ---
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "jyotiranjann135@gmail.com"
SMTP_PASS = "lofe lsnz byqs ndly"

# --- DATABASE CONNECTION ---
def connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="Jyoti2005", # <--- UPDATE THIS TO YOUR DB PASSWORD
        database="EventPilot",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True  # <--- FIXED: Ensures data is actually saved
    )

# --- EMAIL HELPER ---
def send_email_smtp(to_email: str, subject: str, body: str):
    server = None
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
        server.ehlo()
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        
        # ---------------------------------------------------------
        # THE FIX: "html" is the second argument here.
        # If this is missing or set to "plain", you will see raw tags.
        # ---------------------------------------------------------
        msg = MIMEText(body, "html", _charset="utf-8")
        
        msg["Subject"] = subject
        msg["From"] = f"EventPilot <{SMTP_USER}>"
        msg["To"] = to_email
        server.send_message(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass

# --- OTP HELPERS ---
def save_otp_for_email(conn, cursor, email, otp, purpose):
    expires_at = datetime.now() + timedelta(minutes=10)
    cursor.execute(
        "INSERT INTO otp_store (email, otp_code, purpose, expires_at) VALUES (%s, %s, %s, %s)",
        (email, otp, purpose, expires_at),
    )

def get_otp_for_email(conn, cursor, email):
    cursor.execute(
        "SELECT otp_code, expires_at FROM otp_store WHERE email=%s ORDER BY id DESC LIMIT 1", 
        (email,)
    )
    return cursor.fetchone()

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- ROUTES ---

@app.route('/')
def homepage():
    return render_template('homepage.html') # Ensure this file exists

# 1. LOGIN ROUTE (Fixed Table Names)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']

            conn = connection()
            cursor = conn.cursor()
            
            # 1. Check User Table
            cursor.execute("SELECT * FROM user_data WHERE email=%s", (email,))
            user = cursor.fetchone()
            role = 'user'

            # 2. If not User, Check Vendor Table
            if not user:
                cursor.execute("SELECT * FROM vendor_data WHERE email=%s", (email,))
                user = cursor.fetchone()
                role = 'vendor'

            # 3. If not Vendor, Check Admin Table (NEW ADDITION)
            if not user:
                cursor.execute("SELECT * FROM admin_data WHERE email=%s", (email,))
                user = cursor.fetchone()
                role = 'admin'

            # 4. Verify Password
            if user and check_password_hash(user['password_hash'], password):
                
                # Set specific session keys based on role
                session['role'] = role
                session['name'] = user.get('firstname') or user.get('username') # Admins usually have 'username'

                if role == 'admin':
                    session['admin_id'] = user['id'] # Crucial for your dashboard check
                    session['admin_role'] = user['role'] # Store admin role
                    return redirect(url_for('admin_dashboard')) # Send Admin directly to Dashboard
                else:
                    session['id'] = user['id'] # Regular ID for users/vendors
                    return redirect(url_for('homepage'))
            else:
                flash('Invalid email or password', 'error')
                return redirect(url_for('login'))

        except Exception as e:
            print(f"Login Error: {e}")
            flash('An error occurred during login.')
            return redirect(url_for('login'))
        finally:
            if 'conn' in locals(): conn.close()
            
    return render_template("login.html")

# 2. EMAIL VERIFICATION (Step 1 - Send OTP)
@app.route("/email_verification", methods=["POST", "GET"])
def email_verification():
    if request.method == "POST":
        user_email = request.form.get("email", "").strip()
        if not user_email:
            flash("Enter a valid email.", "error")
            return redirect(url_for("email_verification"))

        conn = connection()
        try:
            with conn.cursor() as cursor:
                # FIXED: Check if email already exists in REAL tables
                #checkng both user_data and vendor_data tables
                cursor.execute("SELECT id FROM user_data WHERE email=%s UNION SELECT id FROM vendor_data WHERE email=%s", (user_email, user_email))
                existing = cursor.fetchone()

                #checking admin_data table as well
                if not existing:
                    cursor.execute("SELECT id FROM admin_data WHERE email=%s", (user_email,))
                    existing = cursor.fetchone()

                if existing:
                    flash("Email already registered. Please Login.", "error")
                    return redirect(url_for("login"))
                
                # Generate and Save OTP
                otp = str(random.randint(100000, 999999))
                save_otp_for_email(conn, cursor, user_email, otp, 'registration')
                
                # Send Email
                Thread(target=send_email_smtp, args=(user_email, "OTP Verification", f"Your OTP: {otp}")).start()
                
                flash("OTP sent to your email.", "success")
                return render_template("otp_verification.html", email=user_email)

        except Exception as e:
            print("Error in /email_verification:", e)
            flash("Error, please try again.", "error")
            return redirect(url_for("email_verification"))
        finally:
            conn.close()

    return render_template("email_verification.html")

# 3. OTP VERIFICATION (Step 2 - Verify & Temp Store)
@app.route("/otp_verification", methods=["POST"])
def otp_verification():
    otp_input = request.form.get("otp", "").strip()
    email = request.form.get("email", "").strip()

    conn = connection()
    try:
        with conn.cursor() as cursor:
            row = get_otp_for_email(conn, cursor, email)
            
            if row and str(row.get("otp_code")) == str(otp_input) and row.get("expires_at") > datetime.now():
                
                # FIXED: Insert into temp_registrations to get an ID
                # Clean up old attempts first
                cursor.execute("DELETE FROM temp_registrations WHERE email=%s", (email,))
                cursor.execute("INSERT INTO temp_registrations (email) VALUES (%s)", (email,))
                
                # Get the ID
                new_temp_id = cursor.lastrowid
                session['temp_id'] = new_temp_id # Store ID, not email
                
                flash("Email verified successfully.", "success")
                return redirect(url_for("registration"))
            else:
                flash("Invalid or Expired OTP!", "error")
                return render_template("otp_verification.html", email=email)
                
    except Exception as e:
        print("Error in /otp_verification:", e)
        flash("Error verifying OTP.", "error")
        return render_template("otp_verification.html", email=email)
    finally:
        conn.close()

# 4. FINAL REGISTRATION (Step 3 - Create User)
from threading import Thread # Ensure this is imported

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    # 1. Security Check
    temp_id = session.get('temp_id')
    if not temp_id:
        flash("Session expired. Verify email again.", "error")
        return redirect(url_for('email_verification'))

    # 2. Fetch Email
    verified_email = None
    conn = connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT email FROM temp_registrations WHERE id=%s", (temp_id,))
            res = cursor.fetchone()
            if res: verified_email = res['email']
    finally:
        conn.close()

    if not verified_email:
        flash("Registration session invalid.", "error")
        return redirect(url_for('email_verification'))

    # 3. Handle Form Submission
    if request.method == 'POST':
        conn = connection()
        try:
            with conn.cursor() as cursor:
                firstname = request.form.get('firstname')
                lastname = request.form.get('lastname')
                password = request.form.get('password_hash')
                role = request.form.get('role')
                hashed_pw = generate_password_hash(password)
                
                phone_no = request.form.get("phone_no")
                state = request.form.get("state")
                city = request.form.get("city")
                address = request.form.get("address")

                email_subject = ""
                email_body = ""

                # --- VENDOR LOGIC ---
                if role == 'vendor':
                    business_name = request.form.get('business_name')
                    category = request.form.get('category')
                    
                    sql = """INSERT INTO vendor_data 
                             (firstname, lastname, email, password_hash, business_name, category, verification_status, phone_no, state, city, address) 
                             VALUES (%s, %s, %s, %s, %s, %s, 'pending', %s, %s, %s, %s)"""
                    cursor.execute(sql, (firstname, lastname, verified_email, hashed_pw, business_name, category, phone_no, state, city, address))
                    
                    # Professional Vendor Email
                    email_subject = "EventPilot Partner Application Received 🌟"
                    email_body = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; color: #333;">
                        <h2 style="color: #FF6B00;">Welcome to EventPilot, {firstname}!</h2>
                        <p>Thank you for registering <strong>{business_name}</strong> with us.</p>
                        <p>Your account is currently <strong>PENDING APPROVAL</strong>.</p>
                        <p>Our team verifies all vendors to ensure quality. This process usually takes 24-48 hours.</p>
                        <hr>
                        <h3>What happens next?</h3>
                        <ol>
                            <li>Admin reviews your business details.</li>
                            <li>Once approved, you will receive a confirmation email.</li>
                            <li>You can then login and start accepting bookings!</li>
                        </ol>
                        <p>If you have questions, reply to this email.</p>
                        <br>
                        <p>Best Regards,<br><strong>The EventPilot Team</strong></p>
                    </body>
                    </html>
                    """

                # --- USER (ORGANIZER) LOGIC ---
                else:
                    sql = """INSERT INTO user_data 
                             (firstname, lastname, email, password_hash, phone_no, state, city, address) 
                             VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                    cursor.execute(sql, (firstname, lastname, verified_email, hashed_pw, phone_no, state, city, address))
                    
                    # Exciting User Email
                    email_subject = "Welcome to EventPilot - Let's Plan Your Event! 🚀"
                    email_body = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; color: #333;">
                        <h2 style="color: #FF6B00;">Welcome Aboard, {firstname}!</h2>
                        <p>You have successfully created your account. You are now one step closer to planning the perfect event.</p>
                        <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #FF6B00; margin: 20px 0;">
                            <p><strong>Your Account is Ready!</strong></p>
                            <p>Log in now to browse top-rated photographers, caterers, and decorators in <strong>{city}</strong>.</p>
                        </div>
                        <p>
                            <a href="http://127.0.0.1:5000/login" style="background-color: #FF6B00; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">Login to EventPilot</a>
                        </p>
                        <br>
                        <p>Happy Planning,<br><strong>The EventPilot Team</strong></p>
                    </body>
                    </html>
                    """

                # 4. Cleanup & Commit
                cursor.execute("DELETE FROM temp_registrations WHERE id=%s", (temp_id,))
                session.pop('temp_id', None)

                # 5. Send Email
                Thread(target=send_email_smtp, args=(verified_email, email_subject, email_body)).start()

            flash("Registration Successful! Please Login.", "success")
            return redirect(url_for('login'))
            
        except Exception as e:
            print("Reg Error:", e)
            flash("Error creating account. Please try again.", "error")
            return redirect(url_for('registration'))
        finally:
            conn.close()

    return render_template("registration.html", email=verified_email)

# 5. RESEND OTP
@app.route("/resend_otp", methods=["POST"])
def resend_otp():
    email = request.form.get("email")
    if not email:
        flash("Email missing.", "error")
        return redirect(url_for("email_verification"))

    conn = connection()
    try:
        with conn.cursor() as cursor:
            otp = str(random.randint(100000, 999999))
            save_otp_for_email(conn, cursor, email, otp, 'resend_verification')
            Thread(target=send_email_smtp, args=(email, "Resend OTP", f"Your new OTP is: {otp}")).start()
            
            flash("New OTP sent.", "success")
            return render_template("otp_verification.html", email=email)
    except Exception as e:
        print("Resend Error:", e)
        return redirect(url_for("email_verification"))
    finally:
        conn.close()


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('homepage'))

# ---------------- ADMIN DASHBOARD ----------------
# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin/dashboard')
def admin_dashboard():
    # 1. Security Check
    if 'admin_id' not in session:
        return redirect(url_for('login'))

    conn = connection()
    try:
        with conn.cursor() as cursor:
            # --- 1. Get Counts ---
            cursor.execute("SELECT COUNT(*) as count FROM user_data")
            user_count = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM vendor_data WHERE verification_status='verified'")
            vendor_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM bookings")
            booking_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM admin_data")
            admin_count = cursor.fetchone()['count']

            # --- 2. Get Lists (All Users, Vendors, Bookings) ---
            
            # Pending Vendors
            cursor.execute("SELECT * FROM vendor_data WHERE verification_status='pending'")
            pending_vendors = cursor.fetchall()

            # All Users
            cursor.execute("SELECT * FROM user_data")
            all_users = cursor.fetchall()

            # All Vendors
            cursor.execute("SELECT * FROM vendor_data")
            all_vendors = cursor.fetchall()

            # All Bookings (FIXED SQL COLUMN NAME HERE)
            # Changed 'b.total_price' to 'b.user_request_price'
            sql_bookings = """
                SELECT 
                    b.id, b.event_date, b.status, 
                    b.user_request_price, b.final_price, 
                    u.firstname as user_name, u.email as user_email, 
                    v.business_name as vendor_name, v.category
                FROM bookings b
                JOIN user_data u ON b.user_id = u.id
                JOIN vendor_data v ON b.vendor_id = v.id
                ORDER BY b.created_at DESC
            """
            cursor.execute(sql_bookings)
            all_bookings = cursor.fetchall()

            # Admin List
            cursor.execute("SELECT * FROM admin_data")
            admin_info = cursor.fetchall()

            # Calculate Total Users
            total_platform_users = user_count + vendor_count

            return render_template('admin.html', 
                                   total_users=total_platform_users,
                                   vendors=vendor_count, 
                                   bookings=booking_count,
                                   admins=admin_count,
                                   pending_vendors=pending_vendors,
                                   all_users=all_users,
                                   all_vendors=all_vendors,
                                   all_bookings=all_bookings,
                                   admin_info=admin_info)

    except Exception as e:
        print(f"Admin Dashboard Error: {e}")
        # Return a simple error string so the page doesn't crash completely with TypeError
        return f"An error occurred loading the dashboard: {e}"
        
    finally:
        if conn:
            conn.close()


# --- 2. VENDOR APPROVAL / REJECTION ---
@app.route('/admin/vendor/<action>/<int:id>')
def vendor_action(action, id):
    if 'admin_id' not in session: return redirect(url_for('login'))
    
    status = 'verified' if action == 'approve' else 'rejected'
    
    conn = connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE vendor_data SET verification_status=%s WHERE id=%s", (status, id))
            flash(f"Vendor {status} successfully.", "success")
    finally:
        conn.close()
    return redirect(url_for('admin_dashboard'))


# --- 3. VIEW DETAILS ROUTES ---

# View User Detail
@app.route('/admin/view/user/<int:id>')
def view_user_detail(id):
    if 'admin_id' not in session: return redirect(url_for('login'))
    
    conn = connection()
    try:
        with conn.cursor() as cursor:
            # User Info
            cursor.execute("SELECT * FROM user_data WHERE id=%s", (id,))
            user = cursor.fetchone()
            
            # Booking History for this user
            cursor.execute("""
                SELECT b.*, v.business_name 
                FROM bookings b 
                JOIN vendor_data v ON b.vendor_id = v.id 
                WHERE b.user_id=%s ORDER BY b.event_date DESC
            """, (id,))
            bookings = cursor.fetchall()
            
            return render_template('admin_view_user.html', user=user, bookings=bookings)
    finally:
        conn.close()

# View Vendor Detail
@app.route('/admin/view/vendor/<int:id>')
def view_vendor_detail(id):
    if 'admin_id' not in session: return redirect(url_for('login'))
    
    conn = connection()
    try:
        with conn.cursor() as cursor:
            # Vendor Info
            cursor.execute("SELECT * FROM vendor_data WHERE id=%s", (id,))
            vendor = cursor.fetchone()
            
            # Completed Job Count
            cursor.execute("SELECT COUNT(*) as count FROM bookings WHERE vendor_id=%s AND status='completed'", (id,))
            completed_count = cursor.fetchone()['count']

            # Job History
            cursor.execute("""
                SELECT b.*, u.firstname, u.lastname 
                FROM bookings b 
                JOIN user_data u ON b.user_id = u.id 
                WHERE b.vendor_id=%s ORDER BY b.event_date DESC
            """, (id,))
            history = cursor.fetchall()
            
            return render_template('admin_view_vendor.html', vendor=vendor, completed_count=completed_count, history=history)
    finally:
        conn.close()

# View Booking Invoice
@app.route('/admin/view/booking/<int:id>')
def view_booking_detail(id):
    if 'admin_id' not in session: return redirect(url_for('login'))
    
    conn = connection()
    try:
        with conn.cursor() as cursor:
            # Get Full Invoice Details
            sql = """
            SELECT 
                b.*, 
                u.firstname as u_fname, u.lastname as u_lname, u.email as u_email, u.phone_no as u_phone, u.city as u_city,
                v.business_name, v.firstname as v_fname, v.lastname as v_lname, v.email as v_email, v.phone_no as v_phone, v.address as v_address
            FROM bookings b
            JOIN user_data u ON b.user_id = u.id
            JOIN vendor_data v ON b.vendor_id = v.id
            WHERE b.id = %s
            """
            cursor.execute(sql, (id,))
            booking = cursor.fetchone()
            
            return render_template('admin_view_booking.html', booking=booking)
    finally:
        conn.close()

# --- 2. Delete Admin Route ---
@app.route('/admin/delete/<int:id>')
def delete_admin(id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    # Prevent deleting yourself
    if session['admin_id'] == id:
        flash("You cannot delete your own account.", "error")
        return redirect(url_for('admin_dashboard'))

    conn = connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM admin_data WHERE id=%s", (id,))
            flash("Admin removed successfully.", "success")
    except Exception as e:
        print(f"Error: {e}")
        flash("Could not delete admin.", "error")
    finally:
        conn.close()
        
    return redirect(url_for('admin_dashboard'))

# ---------------- ADD NEW ADMIN ----------------
@app.route('/admin/add_new', methods=['GET', 'POST'])
def add_new_admin():
    # 1. SECURITY: Only logged-in Admins can access this
    if 'admin_id' not in session:
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        conn = connection()
        try:
            with conn.cursor() as cursor:
                # Check if email exists
                cursor.execute("SELECT id FROM admin_data WHERE email=%s", (email,))
                if cursor.fetchone():
                    flash("Admin email already exists.", "error")
                    return redirect(url_for('add_new_admin'))

                # Hash Password
                hashed_pw = generate_password_hash(password)

                # Insert
                sql = "INSERT INTO admin_data (username, email, password_hash, role) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (username, email, hashed_pw, role))
                
                flash(f"New Admin '{username}' created successfully!", "success")
                return redirect(url_for('admin_dashboard'))

        except Exception as e:
            print("Add Admin Error:", e)
            flash("Error creating admin.", "error")
        finally:
            conn.close()

    return render_template("add_admin.html")

# -----------------------------------------------------vendor list -----------------------------------------------------------------------

@app.route('/vendors', methods=['GET'])
def vendor_list():
    # 1. Capture filters from URL parameters
    # request.args.get() handles ?city=...&category=...
    category = request.args.get('category', '').strip()
    city = request.args.get('city', '').strip()
    
    conn = connection()
    try:
        with conn.cursor() as cursor:
            # 2. Base Query: Always show verified vendors only
            sql = "SELECT * FROM vendor_data WHERE verification_status = 'verified'"
            params = []

            # 3. Dynamic Filtering
            if category:
                sql += " AND category = %s"
                params.append(category)
            
            if city:
                # Use LIKE for partial matches (e.g., "Mum" finds "Mumbai")
                sql += " AND (city LIKE %s OR address LIKE %s)"
                search_term = f"%{city}%"
                params.extend([search_term, search_term])

            # 4. Execute
            cursor.execute(sql, tuple(params))
            vendors = cursor.fetchall()

            # 5. Render template with results AND the current filters (to keep inputs filled)
            return render_template('vendors.html', 
                                   vendors=vendors, 
                                   current_category=category, 
                                   current_city=city)
    except Exception as e:
        print(f"Search Error: {e}")
        return render_template('vendors.html', vendors=[], error="Could not load vendors.")
    finally:
        conn.close()

# ----------------------------------------------------------vendor  dashboard -----------------------------------------------------------------------
@app.route('/vendor/dashboard', methods=['GET', 'POST'])
def vendor_dashboard():
    # Security Check
    if 'id' not in session or session.get('role') != 'vendor':
        return redirect(url_for('login'))
    
    vendor_id = session['id']
    conn = connection()
    
    try:
        with conn.cursor() as cursor:
            # --- POST: UPDATE PROFILE ---
            if request.method == 'POST':
                try:
                    price = request.form.get('starting_price')
                    description = request.form.get('description')
                    
                    # Update Text Data
                    if price:
                        cursor.execute("UPDATE vendor_data SET starting_price=%s WHERE id=%s", (price, vendor_id))
                    if description:
                        cursor.execute("UPDATE vendor_data SET description=%s WHERE id=%s", (description, vendor_id))

                    # Update Image
                    if 'portfolio_image' in request.files:
                        file = request.files['portfolio_image']
                        if file and file.filename != '' and allowed_file(file.filename):
                            file_ext = os.path.splitext(file.filename)[1]
                            unique_filename = str(uuid.uuid4()) + file_ext
                            
                            # Save to disk
                            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                            
                            # Save to DB
                            cursor.execute("UPDATE vendor_data SET profile_pic=%s WHERE id=%s", (unique_filename, vendor_id))
                    
                    flash("Profile updated successfully!", "success")
                    return redirect(url_for('vendor_dashboard'))

                except Exception as e:
                    # Catch Upload/Update specific errors
                    print(f"Update Error: {e}")
                    flash("Error updating profile. Please try again.", "error")
                    # We don't return here, we fall through to GET to reload the page

            # --- GET: FETCH DATA ---
            # 1. Vendor Details
            cursor.execute("SELECT * FROM vendor_data WHERE id=%s", (vendor_id,))
            vendor = cursor.fetchone()

            # 2. Statistics
            cursor.execute("SELECT SUM(final_price) as revenue FROM bookings WHERE vendor_id=%s AND status='completed'", (vendor_id,))
            res = cursor.fetchone()
            revenue = res['revenue'] if res and res['revenue'] else 0
            
            cursor.execute("SELECT COUNT(*) as count FROM bookings WHERE vendor_id=%s AND status='pending'", (vendor_id,))
            pending_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM bookings WHERE vendor_id=%s AND status='completed'", (vendor_id,))
            completed_count = cursor.fetchone()['count']

            # 3. Bookings List
            sql = """
                SELECT b.*, u.firstname, u.lastname, u.phone_no 
                FROM bookings b
                JOIN user_data u ON b.user_id = u.id
                WHERE b.vendor_id = %s
                ORDER BY b.created_at DESC
            """
            cursor.execute(sql, (vendor_id,))
            bookings = cursor.fetchall()

            return render_template('vendor_dashboard.html', 
                                   vendor=vendor, 
                                   revenue=revenue,
                                   pending_count=pending_count,
                                   completed_count=completed_count,
                                   bookings=bookings)

    except Exception as e:
        # Catch Database Connection/Query errors
        print(f"Dashboard System Error: {e}")
        flash("System error loading dashboard.", "error")
        return redirect(url_for('homepage'))
        
    finally:
        if conn:
            conn.close()

# ----------------------------------------------------------------------vendor details -----------------------------------------------------------------------
# ---------------- SINGLE VENDOR DETAILS PAGE (PROTECTED) ----------------
@app.route('/vendor/<int:id>')
def vendor_details(id):
    # 1. SECURITY CHECK: Is the user logged in?
    if 'id' not in session:
        flash("Please Login to view vendor details.", "error")
        # Redirect them to login page
        return redirect(url_for('login'))

    # 2. If logged in, proceed to fetch data
    conn = connection()
    try:
        with conn.cursor() as cursor:
            # Fetch Vendor Data
            cursor.execute("SELECT * FROM vendor_data WHERE id=%s", (id,))
            vendor = cursor.fetchone()
            
            # If ID doesn't exist, go back to list
            if not vendor:
                flash("Vendor not found.", "error")
                return redirect(url_for('vendor_list'))
            
            return render_template('vendor_details.html', vendor=vendor)
    finally:
        conn.close()

# --------------------------------------------------------book vendor -----------------------------------------------------------------------
from datetime import date # Make sure this is imported at the top

# ---------------- REQUEST BOOKING ROUTE ----------------
# In app.py

@app.route('/book/<int:vendor_id>', methods=['GET', 'POST'])
def request_booking(vendor_id):
    # 1. Security Check
    if 'id' not in session:
        flash("Please login to request a quote.", "error")
        return redirect(url_for('login'))

    conn = connection()
    
    # --- GET: Show Form (No changes here) ---
    if request.method == 'GET':
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, business_name FROM vendor_data WHERE id=%s", (vendor_id,))
                vendor = cursor.fetchone()
                if not vendor:
                    flash("Vendor not found.", "error")
                    return redirect(url_for('homepage'))
                return render_template("book_vendor.html", vendor=vendor, today_date=date.today())
        finally:
            conn.close()

    # --- POST: Save & Email ---
    if request.method == 'POST':
        try:
            # 1. Collect Form Data
            user_id = session['id']
            event_date = request.form.get('event_date')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            event_type = request.form.get('event_type')
            user_request_price = request.form.get('user_request_price') 
            onsite_contact = request.form.get('onsite_contact')
            specific_requirements = request.form.get('specific_requirements') or "No specific notes provided."

            with conn.cursor() as cursor:
                # 2. Insert Booking
                sql = """
                    INSERT INTO bookings 
                    (user_id, vendor_id, event_date, start_time, end_time, 
                     event_type, user_request_price, onsite_contact, specific_requirements, status) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
                """
                cursor.execute(sql, (
                    user_id, vendor_id, event_date, start_time, end_time, 
                    event_type, user_request_price, onsite_contact, specific_requirements
                ))

                # 3. Fetch Data for Email
                # Get Vendor Details
                cursor.execute("SELECT email, business_name FROM vendor_data WHERE id=%s", (vendor_id,))
                vendor_info = cursor.fetchone()
                v_email = vendor_info['email']
                v_name = vendor_info['business_name']

                # Get User Details
                cursor.execute("SELECT email, firstname, lastname FROM user_data WHERE id=%s", (user_id,))
                user_info = cursor.fetchone()
                u_email = user_info['email']
                u_name = f"{user_info['firstname']} {user_info['lastname']}"

            # ---------------- EMAIL 1: TO VENDOR (New Lead) ----------------
            vendor_subject = f"New Booking Inquiry: {event_type} 📅"
            vendor_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2 style="color: #FF6B00;">New Lead for {v_name}! 🚀</h2>
                <p>Hello,</p>
                <p>You have received a new booking request on EventPilot.</p>
                
                <div style="background-color: #f9f9f9; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Client:</strong> {u_name}</p>
                    <p style="margin: 5px 0;"><strong>Event:</strong> {event_type} on {event_date}</p>
                    <p style="margin: 5px 0;"><strong>Time:</strong> {start_time} - {end_time}</p>
                    <p style="margin: 5px 0;"><strong>Budget Proposed:</strong> <span style="color: #FF6B00; font-weight: bold;">₹{user_request_price}</span></p>
                    <p style="margin: 5px 0;"><strong>Onsite Contact:</strong> {onsite_contact}</p>
                </div>

                <div style="border-left: 4px solid #FF6B00; padding-left: 15px; margin-bottom: 20px;">
                    <strong>Specific Requirements:</strong><br>
                    <em>"{specific_requirements}"</em>
                </div>

                <p>
                    <a href="http://127.0.0.1:5000/vendor/dashboard" style="background-color: #FF6B00; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                        View Request in Dashboard
                    </a>
                </p>
                <br>
                <p>Best Regards,<br><strong>The EventPilot Team</strong></p>
            </body>
            </html>
            """

            # ---------------- EMAIL 2: TO USER (Confirmation) ----------------
            user_subject = f"Quote Request Sent to {v_name} ✅"
            user_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2 style="color: #FF6B00;">Request Sent Successfully!</h2>
                <p>Hello <strong>{u_name}</strong>,</p>
                <p>We have forwarded your quote request to <strong>{v_name}</strong>.</p>
                
                <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #FF6B00; margin: 20px 0;">
                    <p><strong>Event:</strong> {event_type} on {event_date}</p>
                    <p><strong>Proposed Budget:</strong> ₹{user_request_price}</p>
                </div>

                <h3>What happens next?</h3>
                <ol>
                    <li>The vendor will review your requirements.</li>
                    <li>They usually respond within 24 hours.</li>
                    <li>You will receive an email notification when they <strong>Accept</strong> or <strong>Reject</strong> your request.</li>
                </ol>
                <br>
                <p>Happy Planning,<br><strong>The EventPilot Team</strong></p>
            </body>
            </html>
            """

            # 5. Send Emails (Using Threads)
            # Send to Vendor
            Thread(target=send_email_smtp, args=(v_email, vendor_subject, vendor_body, True)).start()
            # Send to User
            Thread(target=send_email_smtp, args=(u_email, user_subject, user_body, True)).start()

            flash("Quote request sent successfully! Check your email for confirmation.", "success")
            return redirect(url_for('homepage')) 

        except Exception as e:
            print("Booking Error:", e)
            flash("Error sending request.", "error")
            return redirect(url_for('request_booking', vendor_id=vendor_id))
        finally:
            if conn:
                conn.close()



# --- ROUTE 1: View Booking Details Page ---
@app.route('/vendor/booking/<int:booking_id>')
def view_booking(booking_id):
    if 'id' not in session or session.get('role') != 'vendor':
        return redirect(url_for('login'))

    conn = connection()
    try:
        with conn.cursor() as cursor:
            # Join with user_data to get client info
            sql = """
                SELECT 
                    b.*, 
                    u.firstname, u.lastname, u.email, u.phone_no 
                FROM bookings b
                JOIN user_data u ON b.user_id = u.id
                WHERE b.id = %s
            """
            cursor.execute(sql, (booking_id,))
            booking = cursor.fetchone()

            # Security: Ensure this booking belongs to the logged-in vendor
            # (We need to fetch the vendor_id associated with the session user_id)
            cursor.execute("SELECT id FROM vendor_data WHERE id=%s", (session['id'],))
            vendor_check = cursor.fetchone()
            
            if not booking or booking['vendor_id'] != vendor_check['id']:
                flash("Unauthorized access or booking not found.", "error")
                return redirect(url_for('vendor_dashboard'))

            return render_template('view_booking.html', booking=booking)
    finally:
        conn.close()


# --- ROUTE 2: Handle Accept/Reject & Send Email ---
@app.route('/vendor/booking/action/<int:booking_id>', methods=['POST'])
def process_booking_action(booking_id):
    if 'id' not in session or session.get('role') != 'vendor':
        return redirect(url_for('login'))

    action = request.form.get('action') # 'accept' or 'reject'
    final_price = request.form.get('final_price')
    
    conn = connection()
    try:
        with conn.cursor() as cursor:
            # 1. Fetch Booking & User Details for Email
            sql = """
                SELECT b.*, u.email as user_email, u.firstname, v.business_name 
                FROM bookings b
                JOIN user_data u ON b.user_id = u.id
                JOIN vendor_data v ON b.vendor_id = v.id
                WHERE b.id = %s
            """
            cursor.execute(sql, (booking_id,))
            details = cursor.fetchone()
            
            if not details:
                return redirect(url_for('vendor_dashboard'))

            user_email = details['user_email']
            user_name = details['firstname']
            vendor_name = details['business_name']
            event_type = details['event_type']

            # 2. Update Database based on Action
            if action == 'accept':
                cursor.execute("UPDATE bookings SET status='accepted', final_price=%s WHERE id=%s", 
                               (final_price, booking_id))
                flash_msg = "Booking accepted! Client has been notified."
                
                # --- EMAIL: ACCEPTANCE ---
                subject = f"Booking Confirmed: {vendor_name} ✅"
                body = f"""
                <html>
                <body style="font-family: Arial; color: #333;">
                    <h2 style="color: #10b981;">Good News, {user_name}!</h2>
                    <p><strong>{vendor_name}</strong> has ACCEPTED your booking request.</p>
                    <div style="background: #ecfdf5; padding: 15px; border-left: 4px solid #10b981; margin: 20px 0;">
                        <p><strong>Event:</strong> {event_type}</p>
                        <p><strong>Final Agreed Price:</strong> <span style="font-size: 1.2rem; font-weight: bold;">₹{final_price}</span></p>
                        <p><strong>Status:</strong> CONFIRMED</p>
                    </div>
                    <p>The vendor will contact you shortly to discuss further arrangements.</p>
                </body>
                </html>
                """

            elif action == 'reject':
                cursor.execute("UPDATE bookings SET status='rejected' WHERE id=%s", (booking_id,))
                flash_msg = "Booking rejected."
                
                # --- EMAIL: REJECTION ---
                subject = f"Booking Update: {vendor_name}"
                body = f"""
                <html>
                <body style="font-family: Arial; color: #333;">
                    <h2>Booking Update</h2>
                    <p>Hello {user_name},</p>
                    <p>Unfortunately, <strong>{vendor_name}</strong> is unable to accept your booking request for {event_type} at this time.</p>
                    <p>Please visit EventPilot to browse other available vendors.</p>
                    <p><a href="http://127.0.0.1:5000">Find other vendors</a></p>
                </body>
                </html>
                """

            # 3. Send Email
            Thread(target=send_email_smtp, args=(user_email, subject, body, True)).start()
            
            flash(flash_msg, "success" if action == 'accept' else "info")

    except Exception as e:
        print("Action Error:", e)
        flash("Error processing request.", "error")
    finally:
        conn.close()

    return redirect(url_for('vendor_dashboard'))




if __name__=="__main__":
    app.run(debug=True)