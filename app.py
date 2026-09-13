import streamlit as st
import csv
import io
import sqlite3
import base64
from PIL import Image, ImageDraw, ImageFont, ImageOps
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Student ID Card Portal", page_icon="🪪", layout="centered")

DB_NAME = "dynamic_students_db.db"

# ==========================================
# 🗄️ DATABASE ENGINE (AUTO-MIGRATION FIXED)
# ==========================================
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Check current table schema
        cursor.execute("PRAGMA table_info(students)")
        existing_cols = cursor.fetchall()
        
        # Agar table purana hai (jaise 3 columns wala), drop karke naya banayein
        if existing_cols and len(existing_cols) != 24:
            cursor.execute("DROP TABLE students")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                app_no TEXT PRIMARY KEY,
                name TEXT,
                samagra_id TEXT,
                father_name TEXT,
                mother_name TEXT,
                dob TEXT,
                gender TEXT,
                admission_year TEXT,
                trade_name TEXT,
                trade_type TEXT,
                mobile TEXT,
                email TEXT,
                category TEXT,
                ews TEXT,
                minority TEXT,
                passing_year TEXT,
                board_name TEXT,
                domicile TEXT,
                date_of_admission TEXT,
                trade_duration TEXT,
                round TEXT,
                disability TEXT,
                pwd_category TEXT,
                e_district TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        conn.commit()

def reset_database():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS students")
        conn.commit()
    init_db()

def get_setting(key, default):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            return row[0] if row else default
    except Exception:
        return default

def save_setting(key, value):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, str(value)))
        conn.commit()

# Ensure table schema on startup
init_db()

# ==========================================
# 🔤 CROSS-PLATFORM FONT HELPER
# ==========================================
def get_font(size, bold=False):
    font_names = [
        "arialbd.ttf" if bold else "arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "DejaVuSans.ttf"
    ]
    for font_path in font_names:
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()

# ==========================================
# 🎨 PREMIUM ID CARD ENGINE (CUSTOM BACKGROUND SUPPORT)
# ==========================================
def generate_dynamic_card(student_dict, photo_file, bg_color, text_color, header_title, logo_base64=None, bg_image_base64=None):
    card_width = 420
    card_height = 590
    
    # 1. Base Card Background (Custom Image agar uploaded ho, varna Solid Clean Background)
    has_custom_bg = False
    if bg_image_base64 and str(bg_image_base64).strip() not in ["None", ""]:
        try:
            bg_data = base64.b64decode(bg_image_base64)
            card = Image.open(io.BytesIO(bg_data)).convert("RGB")
            card = ImageOps.fit(card, (card_width, card_height), Image.Resampling.LANCZOS)
            has_custom_bg = True
        except Exception:
            card = Image.new("RGB", (card_width, card_height), "#F8FAFC")
    else:
        card = Image.new("RGB", (card_width, card_height), "#F8FAFC")

    draw = ImageDraw.Draw(card)

    font_header = get_font(20, bold=True)
    font_sub = get_font(12, bold=True)
    font_name = get_font(22, bold=True)
    font_label = get_font(14, bold=True)
    font_text = get_font(14, bold=False)
    font_footer = get_font(13, bold=True)

    # Agar custom background nahi hai, tabhi top banner & footer rectangle banayein
    if not has_custom_bg:
        draw.rectangle([(0, 0), (card_width, 135)], fill=bg_color)
        draw.rectangle([(0, card_height - 50), (card_width, card_height)], fill="#0F172A")
        draw.text((210, card_height - 25), "AUTHORIZED SIGNATORY", fill="#F8FAFC", font=font_footer, anchor="mm")

    # Logo Placement
    header_text_x = 210
    align_anchor = "mm"
    if logo_base64 and str(logo_base64).strip() not in ["None", ""]:
        try:
            logo_data = base64.b64decode(logo_base64)
            logo_img = Image.open(io.BytesIO(logo_data)).convert("RGBA")
            logo_img = logo_img.resize((58, 58), Image.Resampling.LANCZOS)
            card.paste(logo_img, (24, 38), mask=logo_img)
            header_text_x = 235
            align_anchor = "lm"
        except Exception:
            header_text_x = 210
            align_anchor = "mm"

    # Institute Title & Subheader
    safe_title = (header_title or "INSTITUTE OF TECHNOLOGY").upper()
    if len(safe_title) > 26 and align_anchor == "lm":
        safe_title = safe_title[:24] + "..."
        
    title_fill = "#FFFFFF" if not has_custom_bg else text_color
    sub_fill = "#E2E8F0" if not has_custom_bg else "#475569"

    draw.text((header_text_x, 52), safe_title, fill=title_fill, font=font_header, anchor=align_anchor)
    draw.text((header_text_x, 86), "STUDENT IDENTITY CARD", fill=sub_fill, font=font_sub, anchor=align_anchor)

    # Circular Profile Photo
    cx, cy, r = 210, 215, 62
    draw.ellipse([(cx - r - 4, cy - r - 4), (cx + r + 4, cy + r + 4)], fill="#FFFFFF", outline=bg_color, width=4)

    if photo_file is not None:
        try:
            student_img = Image.open(photo_file)
            student_img = ImageOps.exif_transpose(student_img).convert("RGBA")
            student_img = ImageOps.fit(student_img, (r * 2, r * 2), Image.Resampling.LANCZOS)
            
            mask = Image.new("L", (r * 2, r * 2), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse([(0, 0), (r * 2, r * 2)], fill=255)
            card.paste(student_img, (cx - r, cy - r), mask=mask)
        except Exception:
            draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill="#E2E8F0")
            draw.text((cx, cy), "NO PHOTO", fill="#64748B", font=font_label, anchor="mm")
    else:
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill="#E2E8F0")
        draw.text((cx, cy), "PHOTO", fill="#64748B", font=font_label, anchor="mm")

    # Student Full Name
    student_name = str(student_dict.get('name', 'N/A')).upper()
    if len(student_name) > 24:
        student_name = student_name[:22] + ".."
    draw.text((210, 305), student_name, fill=text_color, font=font_name, anchor="mm")
    draw.line([(45, 330), (375, 330)], fill="#CBD5E1", width=2)

    # Information Details
    display_fields = [
        ("Roll / App No :", student_dict.get('app_no', 'N/A')),
        ("Father's Name :", student_dict.get('father_name', 'N/A')),
        ("Date of Birth  :", student_dict.get('dob', 'N/A')),
        ("Trade/Course   :", student_dict.get('trade_name', 'N/A')),
        ("Mobile No      :", student_dict.get('mobile', 'N/A')),
    ]

    current_y = 350
    for label, val in display_fields:
        val_str = str(val).strip()
        if len(val_str) > 22:
            val_str = val_str[:20] + "..."
        draw.text((45, current_y), label, fill="#64748B", font=font_label)
        draw.text((185, current_y), val_str, fill="#0F172A", font=font_text)
        current_y += 35

    out_bytes = io.BytesIO()
    card.save(out_bytes, format='PNG', quality=95)
    return out_bytes.getvalue()

# ==========================================
# 🌐 MAIN SETTINGS LOAD
# ==========================================
db_title = get_setting('header_title', 'LOVE INSTITUTE')
db_bg = get_setting('bg_color', '#8B00FF')
db_text = get_setting('text_color', '#1E293B')
db_logo = get_setting('saved_logo_b64', 'None')
db_bg_image = get_setting('saved_bg_image_b64', 'None')

st.sidebar.title("📌 Menu")
app_mode = st.sidebar.radio("Go to:", ["🎓 Student Portal", "🛡️ Admin Panel"])

# ------------------------------------------
# 🛡️ MODE 1: ADMIN CONTROL CENTER
# ------------------------------------------
if app_mode == "🛡️ Admin Panel":
    st.header("🛡️ Admin Secure Access Control")
    admin_pass = st.text_input("Admin Password Likhein:", type="password")

    if admin_pass == "daminimylove":
        st.success("🔓 Access Approved! Welcome Admin.")

        # --- SUBSECTION 1: DESIGNER & BRANDING ---
        st.subheader("🎨 Custom Design & Brand Assets")
        with st.form("branding_form"):
            new_title = st.text_input("Institute / School Name:", value=db_title)
            col1, col2 = st.columns(2)
            with col1:
                new_bg = st.color_picker("Header Top Theme Color:", value=db_bg)
            with col2:
                new_text = st.color_picker("Student Name / Text Color:", value=db_text)

            submitted = st.form_submit_button("💾 Save Branding Settings")
            if submitted:
                save_setting('header_title', new_title.strip())
                save_setting('bg_color', new_bg)
                save_setting('text_color', new_text)
                st.success("Settings saved successfully!")
                st.rerun()

        st.markdown("---")
        
        # --- SUBSECTION 1.1: LOGO & BACKGROUND IMAGE MANAGEMENT ---
        col_img1, col_img2 = st.columns(2)

        # 🏢 LOGO UPLOAD
        with col_img1:
            st.markdown("##### 🏢 Institute Logo")
            if db_logo and db_logo != "None":
                try:
                    st.image(io.BytesIO(base64.b64decode(db_logo)), width=90, caption="Current Logo")
                except Exception:
                    pass
            else:
                st.caption("No custom logo uploaded.")

            logo_file = st.file_uploader("Upload New Logo (PNG / JPG):", type=["png", "jpg", "jpeg"], key="logo_uploader")
            if logo_file is not None:
                if st.button("Save Logo", key="btn_save_logo"):
                    logo_b64_str = base64.b64encode(logo_file.getvalue()).decode('utf-8')
                    save_setting('saved_logo_b64', logo_b64_str)
                    st.success("Logo saved!")
                    st.rerun()
            if db_logo and db_logo != "None":
                if st.button("❌ Remove Logo", key="btn_del_logo"):
                    save_setting('saved_logo_b64', 'None')
                    st.rerun()

        # 🖼️ CUSTOM CARD BACKGROUND IMAGE UPLOAD
        with col_img2:
            st.markdown("##### 🖼️ Card Background Image")
            if db_bg_image and db_bg_image != "None":
                try:
                    st.image(io.BytesIO(base64.b64decode(db_bg_image)), width=130, caption="Current Background Image")
                except Exception:
                    pass
            else:
                st.caption("Default clean background active.")

            bg_file = st.file_uploader("Upload Card Background (JPG / PNG):", type=["png", "jpg", "jpeg"], key="bg_uploader")
            if bg_file is not None:
                if st.button("Save Background Image", key="btn_save_bg"):
                    bg_b64_str = base64.b64encode(bg_file.getvalue()).decode('utf-8')
                    save_setting('saved_bg_image_b64', bg_b64_str)
                    st.success("Background Image saved permanently!")
                    st.rerun()
            if db_bg_image and db_bg_image != "None":
                if st.button("❌ Remove Background Image", key="btn_del_bg"):
                    save_setting('saved_bg_image_b64', 'None')
                    st.success("Default background restored!")
                    st.rerun()

        # --- SUBSECTION 2: BATCH CSV IMPORTER ---
        st.markdown("---")
        st.subheader("📦 Bulk CSV Data Importer")
        uploaded_csv = st.file_uploader("Select Database Spreadsheet (.CSV File)", type=["csv"], key="csv_uploader")

        if uploaded_csv is not None:
            try:
                raw_bytes = uploaded_csv.getvalue()
                try:
                    file_contents = raw_bytes.decode("utf-8-sig").splitlines()
                except UnicodeDecodeError:
                    file_contents = raw_bytes.decode("latin-1").splitlines()

                reader = csv.DictReader(file_contents)
                clean_fieldnames = {f.strip().lower(): f.strip() for f in (reader.fieldnames or [])}

                def get_val(row, *aliases):
                    for alias in aliases:
                        al = alias.lower()
                        if al in clean_fieldnames:
                            val = row.get(clean_fieldnames[al])
                            if val is not None and str(val).strip() != "":
                                return str(val).strip()
                    return 'N/A'

                with sqlite3.connect(DB_NAME) as conn:
                    cursor = conn.cursor()
                    count = 0
                    for row in reader:
                        r_app = get_val(row, 'Application Number', 'ApplicationNo', 'App No', 'Roll No', 'app_no')
                        if r_app == 'N/A' or not r_app:
                            continue

                        r_name = get_val(row, 'Name', 'Student Name', 'Candidate Name', 'Trainee Name')

                        cursor.execute('''
                            INSERT OR REPLACE INTO students (
                                app_no, name, samagra_id, father_name, mother_name,
                                dob, gender, admission_year, trade_name, trade_type,
                                mobile, email, category, ews, minority,
                                passing_year, board_name, domicile, date_of_admission,
                                trade_duration, round, disability, pwd_category, e_district
                            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        ''', (
                            r_app, r_name,
                            get_val(row, 'Samagra ID', 'SamagraId', 'Samagra'),
                            get_val(row, 'Father Name', 'FatherName', "Father's Name"),
                            get_val(row, 'Mother Name', 'MotherName', "Mother's Name"),
                            get_val(row, 'Dob', 'DOB', 'Date of Birth'),
                            get_val(row, 'Gender'),
                            get_val(row, 'Admission Year', 'AdmissionYear'),
                            get_val(row, 'Trade Name', 'Trade', 'Course'),
                            get_val(row, 'Trade Type NCVT/SCVT', 'Trade Type', 'TradeType'),
                            get_val(row, 'Trainee Mobile', 'Mobile', 'Mobile No', 'Phone'),
                            get_val(row, 'Trainee Email', 'Email', 'Email ID'),
                            get_val(row, 'Category'),
                            get_val(row, 'EWS'),
                            get_val(row, 'Minority Category', 'Minority'),
                            get_val(row, 'Passing Year', 'PassingYear'),
                            get_val(row, 'Board Name', 'Board'),
                            get_val(row, 'Domicile'),
                            get_val(row, 'Date of Admission', 'Admission Date', 'AdmissionDate'),
                            get_val(row, 'Trade Duration', 'Duration'),
                            get_val(row, 'Round'),
                            get_val(row, 'Disability'),
                            get_val(row, 'PWD category', 'PWD Category'),
                            get_val(row, 'Trainee E-District', 'E-District', 'District')
                        ))
                        count += 1
                    conn.commit()

                st.success(f"✅ Data Synchronized! Total {count} student records saved.")
                st.rerun()
            except Exception as e:
                st.error(f"Error processing CSV file: {e}")

        # --- SUBSECTION 3: DATA VIEWER ---
        st.markdown("---")
        st.subheader("📋 Live Database Student List")
        
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM students')
            rows = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description] if cursor.description else []

        if rows:
            df_full = pd.DataFrame(rows, columns=col_names)
            st.dataframe(df_full, use_container_width=True)
            st.write(f"Total Students: **{len(rows)}**")

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("🗑️ Clear All Student Records"):
                    with sqlite3.connect(DB_NAME) as conn:
                        cursor = conn.cursor()
                        cursor.execute('DELETE FROM students')
                        conn.commit()
                    st.warning("All student records deleted.")
                    st.rerun()
            with col_btn2:
                if st.button("🔄 Reset & Re-create Table Schema"):
                    reset_database()
                    st.success("Database table reset to 24 columns cleanly!")
                    st.rerun()
        else:
            st.info("📂 Database is currently empty.")
            if st.button("🔄 Re-sync / Fix Table Schema"):
                reset_database()
                st.success("Schema synchronized!")
                st.rerun()

    elif admin_pass != "":
        st.error("❌ Galat Password! Access Denied.")

# ------------------------------------------
# 🎓 MODE 2: STUDENT PORTAL
# ------------------------------------------
else:
    st.header("🎓 Student Self-Service Hub")

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM students')
        row = cursor.fetchone()
        db_count = row[0] if row else 0

    if db_count == 0:
        st.warning("⚠️ Database me abhi koi student records nahi hain. Admin panel se pehle CSV upload karein.")
    else:
        search_app = st.text_input("Apna Application Number Type Karein:", placeholder="Eg. APP202601, 1024...").strip()

        if search_app:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM students WHERE UPPER(TRIM(app_no)) = UPPER(TRIM(?))', (search_app,))
                result = cursor.fetchone()

            if result:
                student_data = {
                    'app_no': result[0],
                    'name': result[1],
                    'samagra_id': result[2],
                    'father_name': result[3],
                    'mother_name': result[4],
                    'dob': result[5],
                    'gender': result[6],
                    'admission_year': result[7],
                    'trade_name': result[8],
                    'trade_type': result[9],
                    'mobile': result[10],
                    'email': result[11]
                }

        
