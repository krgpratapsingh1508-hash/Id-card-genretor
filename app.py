import streamlit as st
import csv
import io
import sqlite3
import base64
from PIL import Image, ImageDraw, ImageFont, ImageOps
import pandas as pd

st.set_page_config(page_title="Student ID Card Portal", page_icon="🪪", layout="centered")

DB_NAME = "dynamic_students_db.db"

# ==========================================
# 🗄️ DATABASE ENGINE (AUTO-MIGRATION FIXED)
# ==========================================
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(students)")
        existing_cols = cursor.fetchall()
        if existing_cols and len(existing_cols) != 24:
            cursor.execute("DROP TABLE students")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                app_no TEXT PRIMARY KEY, name TEXT, samagra_id TEXT,
                father_name TEXT, mother_name TEXT, dob TEXT, gender TEXT,
                admission_year TEXT, trade_name TEXT, trade_type TEXT,
                mobile TEXT, email TEXT, category TEXT, ews TEXT, minority TEXT,
                passing_year TEXT, board_name TEXT, domicile TEXT,
                date_of_admission TEXT, trade_duration TEXT, round TEXT,
                disability TEXT, pwd_category TEXT, e_district TEXT
            )
        ''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
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

init_db()

# ==========================================
# 🔤 CROSS-PLATFORM FONT HELPER
# ==========================================
def get_font(size, bold=False):
    font_names = [
        "arialbd.ttf" if bold else "arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
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
# 🎨 ID CARD ENGINE (FULL DESIGN CONTROL)
# ==========================================
def generate_dynamic_card(student_dict, photo_file, bg_color, text_color, 
                         header_title, title_size, title_bold,
                         sub_title, sub_size, sub_bold,
                         logo_base64=None, logo_size=55, sign_base64=None):
    
    card_width, card_height = 420, 600
    card = Image.new("RGB", (card_width, card_height), "#F8FAFC")
    draw = ImageDraw.Draw(card)

    font_header = get_font(title_size, bold=title_bold)
    font_sub = get_font(sub_size, bold=sub_bold)
    font_name = get_font(22, bold=True)
    font_label = get_font(14, bold=True)
    font_text = get_font(14, bold=False)
    font_footer = get_font(11, bold=True)

    # 1. Top Header Banner
    draw.rectangle([(0, 0), (card_width, 135)], fill=bg_color)

    # 2. Dynamic Logo Placement & Sizing
    header_text_x = 210
    align_anchor = "mm"
    has_logo = False
    
    if logo_base64 and str(logo_base64).strip() not in ["None", ""]:
        try:
            logo_data = base64.b64decode(logo_base64)
            logo_img = Image.open(io.BytesIO(logo_data)).convert("RGBA")
            logo_img = logo_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Vertically center logo inside 135px header
            logo_y = max(10, (135 - logo_size) // 2)
            card.paste(logo_img, (20, logo_y), mask=logo_img)
            
            header_text_x = 20 + logo_size + 14
            align_anchor = "lm"
            has_logo = True
        except Exception:
            header_text_x = 210
            align_anchor = "mm"

    # 3. Main Title & Subtitle Render
    safe_title = (header_title or "").upper()
    safe_sub = (sub_title or "").upper()
    
    draw.text((header_text_x, 52), safe_title, fill="#FFFFFF", font=font_header, anchor=align_anchor)
    if safe_sub:
        draw.text((header_text_x, 88), safe_sub, fill="#E2E8F0", font=font_sub, anchor=align_anchor)

    # 4. Circular Profile Photo
    cx, cy, r = 210, 215, 62
    draw.ellipse([(cx - r - 4, cy - r - 4), (cx + r + 4, cy + r + 4)], fill="#FFFFFF", outline=bg_color, width=4)

    if photo_file is not None:
        try:
            student_img = Image.open(photo_file)
            student_img = ImageOps.exif_transpose(student_img).convert("RGBA")
            student_img = ImageOps.fit(student_img, (r * 2, r * 2), Image.Resampling.LANCZOS)
            mask = Image.new("L", (r * 2, r * 2), 0)
            ImageDraw.Draw(mask).ellipse([(0, 0), (r * 2, r * 2)], fill=255)
            card.paste(student_img, (cx - r, cy - r), mask=mask)
        except Exception:
            draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill="#E2E8F0")
            draw.text((cx, cy), "NO PHOTO", fill="#64748B", font=font_label, anchor="mm")
    else:
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill="#E2E8F0")
        draw.text((cx, cy), "PHOTO", fill="#64748B", font=font_label, anchor="mm")

    # 5. Student Full Name
    student_name = str(student_dict.get('name', 'N/A')).upper()[:24]
    draw.text((210, 305), student_name, fill=text_color, font=font_name, anchor="mm")
    draw.line([(45, 328), (375, 328)], fill="#CBD5E1", width=2)

    # 6. Student Information Rows
    display_fields = [
        ("Roll / App No :", student_dict.get('app_no', 'N/A')),
        ("Father's Name :", student_dict.get('father_name', 'N/A')),
        ("Date of Birth :", student_dict.get('dob', 'N/A')),
        ("Trade/Course  :", student_dict.get('trade_name', 'N/A')),
        ("Mobile No     :", student_dict.get('mobile', 'N/A')),
    ]

    current_y = 345
    for label, val in display_fields:
        val_str = str(val).strip()[:22]
        draw.text((45, current_y), label, fill="#64748B", font=font_label)
        draw.text((185, current_y), val_str, fill="#0F172A", font=font_text)
        current_y += 33

    # 7. Authorized Signature & Signatory Underline
    if sign_base64 and str(sign_base64).strip() not in ["None", ""]:
        try:
            sign_data = base64.b64decode(sign_base64)
            sign_img = Image.open(io.BytesIO(sign_data))
            sign_img.thumbnail((140, 45), Image.Resampling.LANCZOS)
            sw, sh = sign_img.size
            sx = 210 - (sw // 2)
            sy = 548 - sh
            if sign_img.mode == 'RGBA':
                card.paste(sign_img, (sx, sy), mask=sign_img)
            else:
                card.paste(sign_img, (sx, sy))
        except Exception:
            pass

    draw.line([(130, 555), (290, 555)], fill="#94A3B8", width=1)
    draw.text((210, 572), "AUTHORIZED SIGNATORY", fill="#334155", font=font_footer, anchor="mm")

    # Bottom Accent Border
    draw.rectangle([(0, card_height - 6), (card_width, card_height)], fill=bg_color)

    out_bytes = io.BytesIO()
    card.save(out_bytes, format='PNG', quality=95)
    return out_bytes.getvalue()

# ==========================================
# 🌐 MAIN SETTINGS LOAD
# ==========================================
db_title = get_setting('header_title', 'LOVE INSTITUTE')
db_title_size = int(get_setting('title_font_size', 20))
db_title_bold = get_setting('title_bold', 'True') == 'True'

db_sub = get_setting('sub_title', 'STUDENT IDENTITY CARD')
db_sub_size = int(get_setting('sub_font_size', 12))
db_sub_bold = get_setting('sub_bold', 'True') == 'True'

db_bg = get_setting('bg_color', '#8B00FF')
db_text = get_setting('text_color', '#1E293B')
db_logo = get_setting('saved_logo_b64', 'None')
db_logo_size = int(get_setting('logo_size', 55))
db_sign = get_setting('saved_sign_b64', 'None')

st.sidebar.title("📌 Menu")
app_mode = st.sidebar.radio("Go to:", ["🎓 Student Portal", "🛡️ Admin Panel"])

# ------------------------------------------
# 🛡️ ADMIN PANEL
# ------------------------------------------
if app_mode == "🛡️ Admin Panel":
    st.header("🛡️ Admin Secure Access Control")
    admin_pass = st.text_input("Admin Password Likhein:", type="password")

    if admin_pass == "daminimylove":
        st.success("🔓 Access Approved! Welcome Admin.")

        # --- SUBSECTION 1: ADVANCED DESIGN & TYPOGRAPHY SETTINGS ---
        st.subheader("🎨 Custom Typography & Header Designer")
        with st.form("branding_form"):
            st.markdown("#### 🏛️ 1. Main Institute Name Settings")
            new_title = st.text_input("Institute / School Name:", value=db_title)
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                new_title_size = st.slider("Name Font Size (px):", min_value=14, max_value=34, value=db_title_size)
            with col_t2:
                new_title_bold = st.checkbox("Bold Institute Name", value=db_title_bold)

            st.markdown("#### 📝 2. Subtitle / Card Heading Settings")
            new_sub = st.text_input("Card Sub-Title (e.g. STUDENT IDENTITY CARD):", value=db_sub)
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                new_sub_size = st.slider("Subtitle Font Size (px):", min_value=10, max_value=24, value=db_sub_size)
            with col_s2:
                new_sub_bold = st.checkbox("Bold Subtitle", value=db_sub_bold)

            st.markdown("#### 🎨 3. Theme Colors")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                new_bg = st.color_picker("Header Top Background Color:", value=db_bg)
            with col_c2:
                new_text = st.color_picker("Student Name / Text Color:", value=db_text)

            st.markdown("#### 📐 4. Logo Dimensions")
            new_logo_size = st.slider("Logo Size (Width & Height in px):", min_value=30, max_value=90, value=db_logo_size)

            submitted = st.form_submit_button("💾 Save All Designer Settings")
            if submitted:
                save_setting('header_title', new_title.strip())
                save_setting('title_font_size', new_title_size)
                save_setting('title_bold', str(new_title_bold))
                
                save_setting('sub_title', new_sub.strip())
                save_setting('sub_font_size', new_sub_size)
                save_setting('sub_bold', str(new_sub_bold))
                
                save_setting('bg_color', new_bg)
                save_setting('text_color', new_text)
                save_setting('logo_size', new_logo_size)
                
                st.success("✅ All typography & layout settings saved successfully!")
                st.rerun()

        st.markdown("---")
        col_img1, col_img2 = st.columns(2)

        # 🏢 LOGO SECTION
        with col_img1:
            st.markdown("##### 🏢 Institute Logo")
            if db_logo and db_logo != "None":
                try:
                    st.image(io.BytesIO(base64.b64decode(db_logo)), width=db_logo_size, caption=f"Current Logo ({db_logo_size}px)")
                except Exception:
                    pass
            logo_file = st.file_uploader("Upload New Logo (PNG / JPG):", type=["png", "jpg", "jpeg"], key="logo_uploader")
            if logo_file is not None and st.button("Save Logo", key="btn_save_logo"):
                save_setting('saved_logo_b64', base64.b64encode(logo_file.getvalue()).decode('utf-8'))
                st.success("Logo saved!")
                st.rerun()
            if db_logo and db_logo != "None" and st.button("❌ Remove Logo", key="btn_del_logo"):
                save_setting('saved_logo_b64', 'None')
                st.rerun()

        # ✍️ AUTHORIZED SIGNATURE SECTION
        with col_img2:
            st.markdown("##### ✍️ Authorized Signature")
            if db_sign and db_sign != "None":
                try:
                    st.image(io.BytesIO(base64.b64decode(db_sign)), width=130, caption="Current Saved Sign")
                except Exception:
                    pass
            else:
                st.caption("No signature uploaded yet.")

            sign_file = st.file_uploader("Upload Signature (PNG / JPG):", type=["png", "jpg", "jpeg"], key="sign_uploader")
            if sign_file is not None and st.button("Save Signature", key="btn_save_sign"):
                save_setting('saved_sign_b64', base64.b64encode(sign_file.getvalue()).decode('utf-8'))
                st.success("Signature saved successfully!")
                st.rerun()
            if db_sign and db_sign != "None" and st.button("❌ Remove Signature", key="btn_del_sign"):
                save_setting('saved_sign_b64', 'None')
                st.success("Signature removed!")
                st.rerun()

        # CSV IMPORTER
        st.markdown("---")
        st.subheader("📦 Bulk CSV Data Importer")
        uploaded_csv = st.file_uploader("Select Spreadsheet (.CSV File)", type=["csv"], key="csv_uploader")

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
                        if alias.lower() in clean_fieldnames:
                            val = row.get(clean_fieldnames[alias.lower()])
                            if val is not None and str(val).strip():
                                return str(val).strip()
                    return 'N/A'

                with sqlite3.connect(DB_NAME) as conn:
                    cursor = conn.cursor()
                    count = 0
                    for row in reader:
                        r_app = get_val(row, 'Application Number', 'ApplicationNo', 'App No', 'Roll No', 'app_no')
                        if r_app == 'N/A' or not r_app:
                            continue
                        cursor.execute('''
                            INSERT OR REPLACE INTO students VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        ''', (
                            r_app,
                            get_val(row, 'Name', 'Student Name', 'Trainee Name'),
                            get_val(row, 'Samagra ID', 'SamagraId'),
                            get_val(row, 'Father Name', 'FatherName'),
                            get_val(row, 'Mother Name', 'MotherName'),
                            get_val(row, 'Dob', 'DOB', 'Date of Birth'),
                            get_val(row, 'Gender'),
                            get_val(row, 'Admission Year', 'AdmissionYear'),
                            get_val(row, 'Trade Name', 'Trade', 'Course'),
                            get_val(row, 'Trade Type NCVT/SCVT', 'Trade Type'),
                            get_val(row, 'Trainee Mobile', 'Mobile', 'Mobile No', 'Phone'),
                            get_val(row, 'Trainee Email', 'Email'),
                            get_val(row, 'Category'),
                            get_val(row, 'EWS'),
                            get_val(row, 'Minority Category', 'Minority'),
                            get_val(row, 'Passing Year', 'PassingYear'),
                            get_val(row, 'Board Name', 'Board'),
                            get_val(row, 'Domicile'),
                            get_val(row, 'Date of Admission', 'Admission Date'),
                            get_val(row, 'Trade Duration', 'Duration'),
                            get_val(row, 'Round'),
                            get_val(row, 'Disability'),
                            get_val(row, 'PWD category', 'PWD Category'),
                            get_val(row, 'Trainee E-District', 'E-District', 'District')
                        ))
                        count += 1
                    conn.commit()

                st.success(f"✅ Total {count} records saved successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"CSV Error: {e}")

        # DATA VIEWER
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
                if st.button("🗑️ Clear All Records"):
                    with sqlite3.connect(DB_NAME) as conn:
                        conn.execute('DELETE FROM students')
                        conn.commit()
                    st.rerun()
            with col_btn2:
                if st.button("🔄 Reset & Fix Table Schema"):
                    reset_database()
                    st.rerun()
        else:
            st.info("📂 Database is currently empty.")

    elif admin_pass != "":
        st.error("❌ Galat Password! Access Denied.")

# ------------------------------------------
# 🎓 STUDENT PORTAL
# ------------------------------------------
else:
    st.header("🎓 Student Self-Service Hub")

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM students')
        row = cursor.fetchone()
        db_count = row[0] if row else 0

    if db_count == 0:
        st.warning("⚠️ Database me abhi koi records nahi hain. Admin panel se CSV upload karein.")
    else:
        search_app = st.text_input("Apna Application Number Type Karein:", placeholder="Eg. APP202601...").strip()

        if search_app:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM students WHERE UPPER(TRIM(app_no)) = UPPER(TRIM(?))', (search_app,))
                result = cursor.fetchone()

            if result:
                student_data = {
                    'app_no': result[0], 'name': result[1], 'samagra_id': result[2],
                    'father_name': result[3], 'mother_name': result[4], 'dob': result[5],
                    'gender': result[6], 'admission_year': result[7], 'trade_name': result[8],
                    'trade_type': result[9], 'mobile': result[10], 'email': result[11]
                }

                st.success(f"🎯 Record Mil Gaya! Hello, **{student_data['name']}**")

                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**Father's Name:** {student_data['father_name']}")
                    st.markdown(f"**DOB:** {student_data['dob']}")
                with col_b:
                 
