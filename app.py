,            mobile TEXT,
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
    conn.close()

def get_setting(key, default):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        val = row[0]
        if val.startswith("('") and (val.endswith("',)") or val.endswith(",)")):
            val = val.replace("('", "").replace("',)", "").replace(",)", "").strip("'")
        return val
    return default

def save_setting(key, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, str(value)))
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 🎨 PREMIUM CIRCULAR ID CARD ENGINE
# ==========================================
def generate_dynamic_card(student_dict, photo_file, bg_color, text_color, header_title, logo_base64=None):
    card_height = 580 
    card = Image.new("RGB", (420, card_height), "#F8FAFC") 
    draw = ImageDraw.Draw(card)
    
    draw.rectangle([(0, 0), (420, 140)], fill=bg_color)
    
    try:
        font_header = ImageFont.truetype("arial.ttf", 22)
        font_sub = ImageFont.truetype("arial.ttf", 13)
        font_name = ImageFont.truetype("arial.ttf", 26)
        font_text = ImageFont.truetype("arial.ttf", 16)
        font_label = ImageFont.truetype("arial.ttf", 15)
    except IOError:
        font_header = font_sub = font_name = font_text = font_label = ImageFont.load_default()

    header_text_x = 210
    if logo_base64 and logo_base64 != "None" and logo_base64 != "":
        try:
            logo_data = base64.b64decode(logo_base64)
            logo_img = Image.open(io.BytesIO(logo_data)).convert("RGBA")
            logo_img = logo_img.resize((55, 55), Image.Resampling.LANCZOS)
            card.paste(logo_img, (30, 42), logo_img)
            header_text_x = 245
        except Exception:
            pass

    draw.text((header_text_x, 55), str(header_title).upper(), fill="#FFFFFF", font=font_header, anchor="mm" if header_text_x==210 else "lm")
    draw.text((header_text_x, 90), "STUDENT IDENTITY CARD", fill="#E2E8F0", font=font_sub, anchor="mm" if header_text_x==210 else "lm")
    
    cx, cy, r = 210, 215, 65
    draw.ellipse([(cx - r - 4, cy - r - 4), (cx + r + 4, cy + r + 4)], fill="#FFFFFF", outline=bg_color, width=4)
    
    if photo_file is not None:
        try:
            student_img = Image.open(photo_file)
            student_img = ImageOps.fit(student_img, (r*2, r*2), Image.Resampling.LANCZOS)
            mask = Image.new("L", (r*2, r*2), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse([(0, 0), (r*2, r*2)], fill=255)
            card.paste(student_img, (cx - r, cy - r), mask=mask)
        except Exception:
            draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill="#E2E8F0")
    else:
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill="#E2E8F0")
        draw.text((cx, cy), "PHOTO", fill="#64748B", font=font_label, anchor="mm")
    
    draw.text((210, 310), str(student_dict['name']).upper(), fill=text_color, font=font_name, anchor="mm")
    draw.line([(50, 335), (370, 335)], fill="#CBD5E1", width=2)
    
    display_fields = [
        ("Application No :", student_dict['app_no']),
        ("Father Name :", student_dict['father_name']),
        ("Date of Birth :", student_dict['dob']),
        ("Trade Name :", student_dict['trade_name']),
        ("Mobile No :", student_dict['mobile']),
    ]
    
    current_y = 355
    for label, val in display_fields:
        draw.text((50, current_y), label, fill="#64748B", font=font_label)
        draw.text((185, current_y), f"{val}", fill="#0F172A", font=font_text)
        current_y += 36
        
    draw.rectangle([(0, card_height - 60), (420, card_height)], fill="#1E293B")
    draw.text((210, card_height - 30), "AUTHORIZED SIGNATORY", fill="#FFFFFF", font=font_text, anchor="mm")
    
    img_byte_arr = io.BytesIO()
    card.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

# ==========================================
# 🌐 MAIN ROUTER LAYOUT CONTROLLER
# ==========================================
db_title = get_setting('header_title', 'LOVE INSTITUTE')
db_bg = get_setting('bg_color', '#0052cc')
db_text = get_setting('text_color', '#1E293B')
db_logo = get_setting('saved_logo_b64', 'None')

app_mode = st.selectbox("Apna Portal Chunein:", ["🎓 Student Portal", "🛡️ Admin Panel"])

# ------------------------------------------
# 🛡️ MODE 1: ADMIN CONTROL CENTER (OPERATIONAL FIXED)
# ------------------------------------------
if app_mode == "🛡️ Admin Panel":
    st.header("🛡️ Admin Secure Access Control")
    admin_pass = st.text_input("Admin Password Likhein:", type="password")
    
    if admin_pass == "daminimylove":
        st.success("🔓 Access Approved! Welcome Admin.")
        
        # --- SUBSECTION 1: LAYOUT & LOGO DESIGNER ---
        st.subheader("🎨 Custom Design & Brand Assets")
        new_title = st.text_input("Institute / School Name:", db_title)
        new_bg = st.color_picker("Header Top Theme Color:", db_bg)
        new_text = st.color_picker("Student Name Text Color:", db_text)
        
        st.write("")
        st.markdown("##### 🏢 Permanent Institute Logo Status")
        if db_logo != "None" and db_logo != "":
            try:
                st.image(io.BytesIO(base64.b64decode(db_logo)), width=80, caption="Saved Current Logo")
            except Exception:
                pass
            
        logo_file = st.file_uploader("Naya Logo Upload/Change Karein (PNG/JPG):", type=["png", "jpg", "jpeg"])
        if logo_file is not None:
            logo_b64_str = base64.b64encode(logo_file.getvalue()).decode('utf-8')
            save_setting('saved_logo_b64', logo_b64_str)
            st.success("🎉 Logo permanently locked in SQLite!")
            st.rerun()

        if new_title != db_title or new_bg != db_bg or new_text != db_text:
            save_setting('header_title', new_title)
            save_setting('bg_color', new_bg)
            save_setting('text_color', new_text)
            st.rerun()

        # --- SUBSECTION 2: BATCH CSV IMPORTER ---
        st.markdown("---")
        st.subheader("📦 Bulk CSV Data Importer Dashboard")
        st.caption("💡 Apni 25 columns wali standard sheet upload karein. Sabhi details auto-fetch ho jayengi.")
        
        uploaded_csv = st.file_uploader("Select Database Spreadsheet (.CSV)", type=["csv"])
        if uploaded_csv is not None:
            file_contents = uploaded_csv.getvalue().decode("utf-8-sig").splitlines()
            reader = csv.DictReader(file_contents)
            reader.fieldnames = [f.strip() for f in reader.fieldnames] if reader.fieldnames else []
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            count = 0
            for row in reader:
                r_app = row.get('Application Number', row.get('ApplicationNo', '')).strip()
                r_name = row.get('Name', 'Unknown').strip()
                
                if not r_app or r_app == "":
                    continue
                
                cursor.execute('''
                    INSERT OR REPLACE INTO students VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', (
                    r_app, r_name,
                    row.get('Samagra ID', 'N/A').strip(),
                    row.get('Father Name', 'N/A').strip(),
                    row.get('Mother Name', 'N/A').strip(),
                    row.get('Dob', 'N/A').strip(),
                    row.get('Gender', 'N/A').strip(),
                    row.get('Admission Year', 'N/A').strip(),
                    row.get('Trade Name', 'N/A').strip(),
                    row.get('Trade Type NCVT/SCVT', 'N/A').strip(),
                    row.get('Trainee Mobile', 'N/A').strip(),
                    row.get('Trainee Email', 'N/A').strip(),
                    row.get('Category', 'N/A').strip(),
                    row.get('EWS', 'N/A').strip(),
                    row.get('Minority Category', 'N/A').strip(),
                    row.get('Passing Year', 'N/A').strip(),
                    row.get('Board Name', 'N/A').strip(),
                    row.get('Domicile', 'N/A').strip(),
                    row.get('Date of Admission', 'N/A').strip(),
                    row.get('Trade Duration', 'N/A').strip(),
                    row.get('Round', 'N/A').strip(),
                    row.get('Disability', 'N/A').strip(),
                    row.get('PWD category', 'N/A').strip(),
                    row.get('Trainee E-District', 'N/A').strip()
                ))
                count += 1
                
            conn.commit()
            conn.close()
            st.success(f"✅ Data Synchronized! Total {count} records saved cleanly.")
            st.rerun()

        # --- SUBSECTION 3: DATA GRID LIST VIEWER WITH AUTO-COLUMN PARSING ---
        st.markdown("---")
        st.subheader("📋 Live Database Uploaded List")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM students')
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            columns_list = [
                "Application Number", "Student Name", "Samagra ID", "Father Name", "Mother Name",
                "DOB", "Gender", "Admission Year", "Trade Name", "Trade Type", "Mobile No",
                "Email", "Category", "EWS", "Minority", "Passing Year", "Board Name", "Domicile",
                "Date of Admission", "Trade Duration", "Round", "Disability", "PWD Category", "Trainee E-District"
            ]
            
            df_full = pd.DataFrame(rows, columns=columns_list)
            df_full.insert(0, "Select Row to Delete", False)
            
            edited_df = st.data_editor(
                df_full,
                hide_index=True,
                disabled=[c for c in columns_list],
                use_container_width=False
            )
            
            selected_rows = edited_df[edited_df["Select Row to Delete"] == True]
            st.write(f"Total Permanent Strength: **{len(rows)}** Students found in database.")
            
            col_del1, col_del2 = st.columns(2)
            with col_del1:
                if st.button("🗑️ Delete Selected Student(s)", key="del_selected"):
                    if not selected_rows.empty:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        for app_no in selected_rows["Application Number"]:
                            cursor.execute('DELETE FROM students WHERE app_no = ?', (str(app_no),))
                        conn.commit()
                        conn.close()
                        st.success(f"🚨 Selected ({len(selected_rows)}) records removed successfully!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Kripya delete karne ke liye pehle kisi checkbox par click karein.")
                        
            with col_del2:
                if st.button("🚨 Clear Entire Database Records", key="clear_db_btn"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM students')
                    conn.commit()
                    conn.close()
                    st.warning("🚨 Complete student database deleted!")
                    st.rerun()
        else:
            st.info("📂 Database is currently empty. Upload a clean CSV file above.")

    elif admin_pass != "":
        st.error("❌ Galat Password! Access Denied.")

# ------------------------------------------
# 🎓 MODE 2: STUDENT PORTAL SECTION (FINAL CORE FIXED)
# ------------------------------------------
else:
    st.header("🎓 Student Self-Service Hub")
    
    # 1. Check karein ki database me data maujood hai ya nahi
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM students')
    db_count = cursor.fetchone()
    conn.close()
    
    # Tuple format validation layout filter logic block
    actual_count = db_count[0] if isinstance(db_count, tuple) else db_count
    
    if actual_count == 0:
        st.warning("⚠️ Admin ne abhi tak koi records database me upload nahi kiye hain.")
    else:
        # 2. Student se Application Number input lena
        search_app = st.text_input("Apna Application Number Type Karein:", placeholder="Eg. APP202601, 54321...").strip()
        
        if search_app:
            # 3. Database se Student ki details extract karna
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM students WHERE app_no = ?', (search_app,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                # 4. Database ke saare columns ko fixed array index se tuple unpacking dwara map karna
                student_data_map = {
                    'app_no': str(result[0]),
                    'name': str(result[1]),
                    'samagra_id': str(result[2]),
                    'father_name': str(result[3]),
                    'mother_name': str(result[4]),
                    'dob': str(result[5]),
                    'gender': str(result[6]),
                    'admission_year': str(result[7]),
                    'trade_name': str(result[8]),
                    'trade_type': str(result[9]),
                    'mobile': str(result[10]),
                    'email': str(result[11])
                }
                
                st.success(f"🎯 Record Found! Hello, {student_data_map['name']}")
                
                # Screen par verified profile values show karna
                st.write("### 📋 Aapki Verified Details:")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"🔹 **Father Name:** {student_data_map['father_name']}")
                    st.write(f"🔹 **DOB (Birth Date):** {student_data_map['dob']}")
                with col_b:
                    st.write(f"🔹 **Trade/Course:** {student_data_map['trade_name']}")
                    st.write(f"🔹 **Mobile No:** {student_data_map['mobile']}")
                    
                # 5. Student ki Photo upload karne ka slot trigger
                student_photo = st.file_uploader("Apni Passport Photo Upload Karein (JPG/PNG):", type=["jpg","png","jpeg"])
                
                if student_photo is not None:
                    # Database parameters unpacked cleanly to protect PIL imaging rendering thread crashes
                    actual_bg = db_bg if not isinstance(db_bg, tuple) else db_bg[0]
                    actual_text = db_text if not isinstance(db_text, tuple) else db_text[0]
                    actual_title = db_title if not isinstance(db_title, tuple) else db_title[0]
                    actual_logo = db_logo if not isinstance(db_logo, tuple) else db_logo[0]

                    # ID card image bytes generate karna
                    card_bytes = generate_dynamic_card(
                        student_dict=student_data_map,
                        photo_file=student_photo,
                        bg_color=actual_bg,
                        text_color=actual_text,
                        header_title=actual_title,
                        logo_base64=actual_logo
                    )
                    
                    st.write("### 🪪 Aapka Live ID Card Preview:")
                    # Screen par premium card output render karna
                    st.image(card_bytes, width=270)
                    
                    # Instant Action Download Button
                    st.download_button(
                        label="📥 Download My ID Card", 
                        data=card_bytes, 
                        file_name=f"ID_{search_app}.png", 
                        mime="image/png"
                    )
                    st.balloons() # Success graphics animation template sequence
            else:
                st.error("🔍 Yeh Application Number records me nahi mila. Kripya apna sahi Number enter karein.")
                
