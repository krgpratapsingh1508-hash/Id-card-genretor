import streamlit as st
import csv
import io
import sqlite3
import base64
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageOps

# Page Configuration
st.set_page_config(
    page_title="Dynamic Student ID Card System",
    page_icon="🪪",
    layout="centered"
)

# ==========================================
# 🗄️ DATABASE ENGINE & AUTO SCHEMA MIGRATION
# ==========================================
EXPECTED_COLUMNS = [
    "app_no", "name", "samagra_id", "father_name", "mother_name",
    "dob", "gender", "admission_year", "trade_name", "trade_type",
    "mobile", "email", "category", "ews", "minority", "passing_year",
    "board_name", "domicile", "date_of_admission", "trade_duration",
    "round", "disability", "pwd_category", "e_district"
]

def init_db():
    conn = sqlite3.connect('dynamic_students_db.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='students'"
    )
    table_exists = cursor.fetchone()
    
    recreate = False
    if table_exists:
        cursor.execute("PRAGMA table_info(students)")
        current_cols = [row[1] for row in cursor.fetchall()]
        if len(current_cols) != len(EXPECTED_COLUMNS) or (current_cols and current_cols[0] != "app_no"):
            cursor.execute("DROP TABLE students")
            recreate = True
    else:
        recreate = True

    if recreate:
        cols_sql = []
        for col in EXPECTED_COLUMNS:
            if col == "app_no":
                cols_sql.append(f"{col} TEXT PRIMARY KEY")
            else:
                cols_sql.append(f"{col} TEXT")
        create_query = f"CREATE TABLE students ({', '.join(cols_sql)})"
        cursor.execute(create_query)
    
    conn.commit()
    conn.close()

def get_setting(key, default):
    conn = sqlite3.connect('dynamic_students_db.db')
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

def save_setting(key, value):
    conn = sqlite3.connect('dynamic_students_db.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
        (key, str(value))
    )
    conn.commit()
    conn.close()

def delete_setting(key):
    conn = sqlite3.connect('dynamic_students_db.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM settings WHERE key = ?', (key,))
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 🎨 ID CARD GENERATOR ENGINE
# ==========================================
def get_font(size, bold=False):
    font_names = [
        "arialbd.ttf" if bold else "arial.ttf",
        "LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    ]
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None

def generate_dynamic_card(
    student_dict,
    photo_file=None,
    bg_color="#0052cc",
    text_color="#1E293B",
    header_title="GLOBAL TECHNOLOGIES",
    title_font_size=20,
    title_bold=True,
    subtitle_text="STUDENT IDENTITY CARD",
    subtitle_font_size=12,
    subtitle_bold=False,
    logo_base64=None,
    logo_size=55,
    sign_base64=None
):
    card_width = 420
    card_height = 580
    card = Image.new("RGB", (card_width, card_height), "#F8FAFC")
    draw = ImageDraw.Draw(card)

    # 1. Top Header Banner
    draw.rectangle([(0, 0), (card_width, 140)], fill=bg_color)

    font_header = get_font(int(title_font_size), bold=title_bold)
    font_sub = get_font(int(subtitle_font_size), bold=subtitle_bold)
    font_name = get_font(24, bold=True)
    font_text = get_font(15, bold=False)
    font_label = get_font(14, bold=True)

    header_text_x = 210
    logo_w = int(logo_size)
    if logo_base64 and logo_base64 != "None":
        try:
            logo_data = base64.b64decode(logo_base64)
            logo_img = Image.open(io.BytesIO(logo_data)).convert("RGBA")
            logo_img = logo_img.resize((logo_w, logo_w), Image.Resampling.LANCZOS)
            logo_y = max(10, 70 - (logo_w // 2))
            card.paste(logo_img, (20, logo_y), logo_img)
            header_text_x = 20 + logo_w + 15 + ((card_width - (20 + logo_w + 15)) // 2)
        except Exception:
            pass

    # Header Titles Text
    draw.text(
        (header_text_x, 52),
        str(header_title).upper(),
        fill="#FFFFFF",
        font=font_header,
        anchor="mm"
    )
    draw.text(
        (header_text_x, 92),
        str(subtitle_text).upper(),
        fill="#E2E8F0",
        font=font_sub,
        anchor="mm"
    )

    # 2. Circular Profile Photo Frame
    cx, cy, r = 210, 215, 62
    draw.ellipse(
        [(cx - r - 4, cy - r - 4), (cx + r + 4, cy + r + 4)],
        fill="#FFFFFF",
        outline=bg_color,
        width=4
    )

    photo_rendered = False
    if photo_file is not None:
        try:
            student_img = Image.open(photo_file)
            student_img = ImageOps.exif_transpose(student_img)
            student_img = ImageOps.fit(
                student_img,
                (r * 2, r * 2),
                Image.Resampling.LANCZOS
            )
            mask = Image.new("L", (r * 2, r * 2), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse([(0, 0), (r * 2, r * 2)], fill=255)
            card.paste(student_img, (cx - r, cy - r), mask=mask)
            photo_rendered = True
        except Exception:
            photo_rendered = False

    if not photo_rendered:
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill="#E2E8F0")
        draw.text((cx, cy), "PHOTO", fill="#64748B", font=font_label, anchor="mm")

    # 3. Student Full Name
    student_name = str(student_dict.get('name', 'Unknown')).upper()
    draw.text((210, 305), student_name, fill=text_color, font=font_name, anchor="mm")
    draw.line([(50, 328), (370, 328)], fill="#CBD5E1", width=2)

    # 4. Details Fields
    display_fields = [
        ("Application No :", student_dict.get('app_no', '-')),
        ("Father Name :", student_dict.get('father_name', '-')),
        ("Date of Birth :", student_dict.get('dob', '-')),
        ("Trade Name :", student_dict.get('trade_name', '-')),
        ("Mobile No :", student_dict.get('mobile', '-')),
    ]

    current_y = 345
    for label, val in display_fields:
        draw.text((50, current_y), label, fill="#64748B", font=font_label)
        draw.text((185, current_y), str(val), fill="#0F172A", font=font_text)
        current_y += 32

    # 5. Signatory Strip Footer Bar
    footer_height = 55
    footer_top = card_height - footer_height
    draw.rectangle([(0, footer_top), (card_width, card_height)], fill="#1E293B")

    # Authorized Signature (Paste if available)
    if sign_base64 and sign_base64 != "None":
        try:
            sign_data = base64.b64decode(sign_base64)
            sign_img = Image.open(io.BytesIO(sign_data)).convert("RGBA")
            sign_img.thumbnail((130, 36), Image.Resampling.LANCZOS)
            sign_x = 210 - (sign_img.width // 2)
            sign_y = footer_top - sign_img.height - 4
            card.paste(sign_img, (sign_x, sign_y), sign_img)
        except Exception:
            pass

    draw.text(
        (210, footer_top + 27),
        "AUTHORIZED SIGNATORY",
        fill="#FFFFFF",
        font=font_text,
        anchor="mm"
    )

    img_byte_arr = io.BytesIO()
    card.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


# ==========================================
# 🌐 ROUTER & SETTINGS LOADING
# ==========================================
db_title = get_setting('header_title', 'GLOBAL TECHNOLOGIES')
db_title_size = int(get_setting('title_font_size', '20'))
db_title_bold = get_setting('title_bold', 'True') == 'True'

db_sub = get_setting('subtitle_text', 'STUDENT IDENTITY CARD')
db_sub_size = int(get_setting('subtitle_font_size', '12'))
db_sub_bold = get_setting('subtitle_bold', 'False') == 'True'

db_bg = get_setting('bg_color', '#0052cc')
db_text = get_setting('text_color', '#1E293B')

db_logo = get_setting('saved_logo_b64', 'None')
db_logo_size = int(get_setting('logo_size', '55'))
db_sign = get_setting('saved_sign_b64', 'None')

app_mode = st.selectbox(
    "Apna Portal Chunein:",
    ["🎓 Student Portal", "🛡️ Admin Panel"]
)

# ------------------------------------------
# 🛡️ MODE 1: ADMIN CONTROL PANEL
# ------------------------------------------
if app_mode == "🛡️ Admin Panel":
    st.header("🛡️ Admin Secure Access Control")
    admin_pass = st.text_input("Admin Password Likhein:", type="password")

    if admin_pass == "daminimylove":
        st.success("🔓 Access Approved! Welcome Admin.")

        # --- DESIGN & BRANDING ---
        st.markdown("---")
        st.subheader("🎨 Custom Design & Brand Settings")
        
        with st.form("design_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_title = st.text_input("Institute / School Name:", value=db_title)
                new_title_size = st.slider(
                    "Institute Name Font Size (px):",
                    min_value=14, max_value=34, value=db_title_size
                )
                new_title_bold = st.checkbox("Institute Name Bold Karein", value=db_title_bold)
                new_bg = st.color_picker("Header Top Theme Color:", value=db_bg)

            with col2:
                new_sub = st.text_input("Subtitle Text:", value=db_sub)
                new_sub_size = st.slider(
                    "Subtitle Font Size (px):",
                    min_value=10, max_value=24, value=db_sub_size
                )
                new_sub_bold = st.checkbox("Subtitle Bold Karein", value=db_sub_bold)
                new_text = st.color_picker("Student Name Text Color:", value=db_text)

            new_logo_size = st.slider(
                "Logo Size (px):",
                min_value=30, max_value=90, value=db_logo_size
            )
            
            save_btn = st.form_submit_button("💾 Design Settings Save Karein")
            if save_btn:
                save_setting('header_title', new_title)
                save_setting('title_font_size', str(new_title_size))
                save_setting('title_bold', str(new_title_bold))
                save_setting('subtitle_text', new_sub)
                save_setting('subtitle_font_size', str(new_sub_size))
                save_setting('subtitle_bold', str(new_sub_bold))
                save_setting('bg_color', new_bg)
                save_setting('text_color', new_text)
                save_setting('logo_size', str(new_logo_size))
                st.success("✅ Design Settings permanently save ho gayi!")
                st.rerun()

        # Logo Upload / Remove Section
        st.markdown("---")
        st.markdown("##### 🏢 Institute Logo Management")
        c_logo_disp, c_logo_up = st.columns([1, 2])
        with c_logo_disp:
            if db_logo != "None":
                try:
                    st.image(
                        io.BytesIO(base64.b64decode(db_logo)),
                        width=80,
                        caption="Current Saved Logo"
                    )
                    if st.button("❌ Logo Remove Karein", key="del_logo_btn"):
                        delete_setting('saved_logo_b64')
                        st.success("Logo hata diya gaya!")
                        st.rerun()
                except Exception:
                    st.info("Logo load error.")
            else:
                st.info("Koi logo uploaded nahi hai.")
        with c_logo_up:
            logo_file = st.file_uploader(
                "Naya Logo Upload Karein (PNG/JPG):",
                type=["png", "jpg", "jpeg"],
                key="up_logo"
            )
            if logo_file is not None:
                logo_b64 = base64.b64encode(logo_file.getvalue()).decode('utf-8')
                save_setting('saved_logo_b64', logo_b64)
                st.success("🎉 Logo database me save ho gaya!")
                st.rerun()

        # Authorized Signature Section
        st.markdown("---")
        st.markdown("##### ✍️ Authorized Signature Management")
        c_sign_disp, c_sign_up = st.columns([1, 2])
        with c_sign_disp:
            if db_sign != "None":
                try:
                    st.image(
                        io.BytesIO(base64.b64decode(db_sign)),
                        width=120,
                        caption="Current Saved Signature"
                    )
                    if st.button("❌ Signature Remove Karein", key="del_sign_btn"):
                        delete_setting('saved_sign_b64')
                        st.success("Signature hata diya gaya!")
                        st.rerun()
                except Exception:
                    st.info("Signature load error.")
            else:
                st.info("Koi signature uploaded nahi hai.")
        with c_sign_up:
            sign_file = st.file_uploader(
                "Authorized Signature Upload Karein (PNG/JPG):",
                type=["png", "jpg", "jpeg"],
                key="up_sign"
            )
            if sign_file is not None:
                sign_b64 = base64.b64encode(sign_file.getvalue()).decode('utf-8')
                save_setting('saved_sign_b64', sign_b64)
                st.success("✍️ Signature permanently save ho gaya!")
                st.rerun()

        # --- BATCH CSV IMPORTER ---
        st.markdown("---")
        st.subheader("📦 Bulk CSV Data Importer")
        st.caption("💡 Apni 24 columns wali standard sheet upload karein.")
        
        uploaded_csv = st.file_uploader(
            "Select Database Spreadsheet (.CSV File Only):",
            type=["csv"],
            key="csv_file_uploader"
        )
        if uploaded_csv is not None:
            raw_bytes = uploaded_csv.getvalue()
            decoded_text = None
            for enc in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
                try:
                    decoded_text = raw_bytes.decode(enc)
                    break
                except Exception:
                    continue

            if decoded_text:
                file_lines = decoded_text.splitlines()
                reader = csv.DictReader(file_lines)
                reader.fieldnames = [f.strip() for f in reader.fieldnames] if reader.fieldnames else []
                
                conn = sqlite3.connect('dynamic_students_db.db')
                cursor = conn.cursor()
                
                count = 0
                for row in reader:
                    r_app = row.get('Application Number', row.get('ApplicationNo', row.get('app_no', ''))).strip()
                    r_name = row.get('Name', row.get('Student Name', row.get('name', 'Unknown'))).strip()
                    
                    if not r_app:
                        continue
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO students VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ''', (
                        r_app,
                        r_name,
                        row.get('Samagra ID', row.get('samagra_id', 'N/A')).strip(),
                        row.get('Father Name', row.get('father_name', 'N/A')).strip(),
                        row.get('Mother Name', row.get('mother_name', 'N/A')).strip(),
                        row.get('Dob', row.get('dob', 'N/A')).strip(),
                        row.get('Gender', row.get('gender', 'N/A')).strip(),
                        row.get('Admission Year', row.get('admission_year', 'N/A')).strip(),
                        row.get('Trade Name', row.get('trade_name', 'N/A')).strip(),
                        row.get('Trade Type NCVT/SCVT', row.get('trade_type', 'N/A')).strip(),
                        row.get('Trainee Mobile', row.get('mobile', 'N/A')).strip(),
                        row.get('Trainee Email', row.get('email', 'N/A')).strip(),
                        row.get('Category', row.get('category', 'N/A')).strip(),
                        row.get('EWS', row.get('ews', 'N/A')).strip(),
                        row.get('Minority Category', row.get('minority', 'N/A')).strip(),
                        row.get('Passing Year', row.get('passing_year', 'N/A')).strip(),
                        row.get('Board Name', row.get('board_name', 'N/A')).strip(),
                        row.get('Domicile', row.get('domicile', 'N/A')).strip(),
                        row.get('Date of Admission', row.get('date_of_admission', 'N/A')).strip(),
                        row.get('Trade Duration', row.get('trade_duration', 'N/A')).strip(),
                        row.get('Round', row.get('round', 'N/A')).strip(),
                        row.get('Disability', row.get('disability', 'N/A')).strip(),
                        row.get('PWD category', row.get('pwd_category', 'N/A')).strip(),
                        row.get('Trainee E-District', row.get('e_district', 'N/A')).strip()
                    ))
                    count += 1
                    
                conn.commit()
                conn.close()
                st.success(f"✅ Data Synchronized! Total {count} records saved cleanly.")
                st.rerun()
            else:
                st.error("CSV file decode nahi ho saki. Kripya standard CSV upload karein.")

        # --- DATA LIST & RESET ---
        st.markdown("---")
        st.subheader("📋 Live Database Uploaded List")
        
        conn = sqlite3.connect('dynamic_students_db.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM students')
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            columns_list = [
                "Application Number", "Student Name", "Samagra ID", "Father Name", "Mother Name",
                "DOB", "Gender", "Admission Year", "Trade Name", "Trade Type", "Mobile No",
                "Email", "Category", "EWS", "Minority", "Passing Year", "Board Name", "Domicile",
                "Date of Admission", "Trade Duration", "Round", "Disability", "PWD Category", "E-District"
            ]
            df_full = pd.DataFrame(rows, columns=columns_list)
            st.dataframe(df_full, use_container_width=True)
            st.write(f"Total Permanent Strength: **{len(rows)}** Students found in database.")
            
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                if st.button("🗑️ Clear All Permanent Records", key="clear_db_btn"):
                    conn = sqlite3.connect('dynamic_students_db.db')
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM students')
                    conn.commit()
                    conn.close()
                    st.warning("🚨 Complete student dataset deleted!")
                    st.rerun()
            with c_btn2:
                if st.button("🔄 Reset & Re-create Table Schema", key="reset_schema_btn"):
                    conn = sqlite3.connect('dynamic_students_db.db')
                    cursor = conn.cursor()
                    cursor.execute('DROP TABLE IF EXISTS students')
                    conn.commit()
                    conn.close()
                    init_db()
                    st.success("✅ Database Schema reset successfully!")
                    st.rerun()
        else:
            st.info("📂 Database is currently empty. Upload a CSV file above.")

    elif admin_pass != "":
        st.error("❌ Galat Password! Access Denied.")

# ------------------------------------------
# 🎓 MODE 2: STUDENT PORTAL SECTION
# ------------------------------------------
else:
    st.header("🎓 Student Self-Service Hub")
    
    conn = sqlite3.connect('dynamic_students_db.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM students')
    db_count = cursor.fetchone()
    conn.close()
    
    if db_count[0] == 0:
        st.warning("⚠️ Database me abhi records upload nahi hain. Admin panel se CSV upload karein.")
    else:
        search_app = st.text_input(
            "Apna Application Number Type Karein:",
            placeholder="Eg. APP202601, 54321..."
        ).strip()
        
        if search_app:
            conn = sqlite3.connect('dynamic_students_db.db')
            cursor = conn.cursor()
            
            # Single line query (koi syntax error nahi aayega)
            search_query = "SELECT * FROM students WHERE UPPER(TRIM(app_no)) = ?"
            cursor.execute(search_query, (search_app.upper(),))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                student_data_map = {
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
                
                st.success(f"🎯 Record Found! Hello, **{student_data_map['name']}**")
                
                st.write("### 📋 Aapki Verified Details:")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"🔹 **Father Name:** {student_data_map['father_name']}")
                    st.write(f"🔹 **DOB (Birth Date):** {student_data_map['dob']}")
                with col_b:
                    st.write(f"🔹 **Trade/Course:** {student_data_map['trade_name']}")
                    st.write(f"🔹 **Mobile No:** {student_data_map['mobile']}")
                    
                student_photo = st.file_uploader(
                    "Apni Passport Photo Upload Karein (Optional):",
                    type=["jpg", "png", "jpeg"],
                    key="student_photo_input"
                )
                
                # Card hamesha generate hoga (photo ho ya na ho)
                card_bytes = generate_dynamic_card(
                    student_dict=student_data_map,
                    photo_file=student_photo if student_photo is not None else None,
                    bg_color=db_bg,
                    text_color=db_text,
                    header_title=db_title,
                    title_font_size=db_title_size,
                    title_bold=db_title_bold,
                    subtitle_text=db_sub,
                    subtitle_font_size=db_sub_size,
                    subtitle_bold=db_sub_bold,
                    logo_base64=db_logo,
                    logo_size=db_logo_size,
                    sign_base64=db_sign
                )
                
                st.write("### 🪪 Aapka Live ID Card Preview:")
                st.image(card_bytes, width=280)
                
                st.download_button(
                    label="📥 Download My ID Card",
                    data=card_bytes,
                    file_name=f"ID_{student_data_map['app_no']}.png",
                    mime="image/png"
                )
                if student_photo is not None:
                    st.balloons()
            else:
                st.error("🔍 Yeh Application Number records me nahi mila. Kripya apna sahi Number enter karein.")
