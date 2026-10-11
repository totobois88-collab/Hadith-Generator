import streamlit as st
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont
import io
import os
import glob
import re

# ================= إعدادات الصفحة =================
st.set_page_config(page_title="صانع صور الأحاديث", page_icon="📜", layout="wide")

st.title("صانع صور الأحاديث النبوية 📜")
st.write("أدخل النص، وسيقوم النظام بتوزيعه وضبط مقاساته ليلائم حجم الصورة.")

# ================= البحث عن الخطوط =================
available_fonts = glob.glob("*.ttf") + glob.glob("*.otf")
if not available_fonts:
    st.warning("لم يتم العثور على خطوط. يرجى رفع ملفات .ttf إلى المستودع.")

# ================= القائمة الجانبية (إعدادات التصميم) =================
st.sidebar.header("🎨 إعدادات التصميم")

st.sidebar.subheader("1. أبعاد الصورة")
image_width = st.sidebar.slider("عرض الصورة:", 600, 2000, 1200, 100)
image_height = st.sidebar.slider("طول الصورة:", 600, 2500, 1200, 100)

st.sidebar.subheader("2. صورة الخلفية")
bg_image_file = st.sidebar.file_uploader("رفع صورة خلفية (اختياري):", type=["png", "jpg", "jpeg"])
bg_scale_mode = "ملء الشاشة (Cover)"
custom_scale = 100
if bg_image_file:
    bg_scale_mode = st.sidebar.selectbox("طريقة عرض الخلفية:", ["ملء الشاشة (Cover)", "تمديد (Stretch)", "تخصيص الحجم (Custom)"])
    if bg_scale_mode == "تخصيص الحجم (Custom)":
        custom_scale = st.sidebar.slider("نسبة التكبير/التصغير:", 10, 200, 100)

st.sidebar.subheader("3. محاذاة وأحجام النصوص")
auto_scale = st.sidebar.checkbox("🤖 تفعيل التحجيم الآلي للخطوط", value=True)

align_opts = ["وسط (Center)", "يمين (Right)", "يسار (Left)"]

col_in1, col_in2 = st.sidebar.columns(2)
align_intro = col_in1.selectbox("محاذاة السند:", align_opts, index=0)
intro_size = col_in2.number_input("حجم السند:", min_value=10, max_value=150, value=40, disabled=auto_scale)

col_hd1, col_hd2 = st.sidebar.columns(2)
align_hadith = col_hd1.selectbox("محاذاة الحديث:", align_opts, index=0)
hadith_size = col_hd2.number_input("حجم الحديث:", min_value=10, max_value=250, value=75, disabled=auto_scale)

col_gr1, col_gr2 = st.sidebar.columns(2)
align_grade = col_gr1.selectbox("محاذاة التخريج:", align_opts, index=0)
grade_size = col_gr2.number_input("حجم التخريج:", min_value=10, max_value=150, value=40, disabled=auto_scale)

st.sidebar.subheader("4. ألوان الخطوط")
intro_text_color = st.sidebar.color_picker("لون نص السند:", "#4A4A4A")
hadith_text_color = st.sidebar.color_picker("لون نص الحديث:", "#1A1A1A")
grade_text_color = st.sidebar.color_picker("لون التخريج:", "#785028")

st.sidebar.subheader("5. أشرطة (تظليل) خلف النصوص")
show_text_bg = st.sidebar.checkbox("تفعيل تظليل ملون خلف النصوص", value=False)
intro_bg_color = "#F0E6D2"
hadith_bg_color = "#E8E8E8"
grade_bg_color = "#F0E6D2"

if show_text_bg:
    intro_bg_color = st.sidebar.color_picker("لون تظليل السند:", "#F0E6D2")
    hadith_bg_color = st.sidebar.color_picker("لون تظليل الحديث:", "#E8E8E8")
    grade_bg_color = st.sidebar.color_picker("لون تظليل التخريج:", "#F0E6D2")

st.sidebar.subheader("6. إعدادات أخرى")
bg_color = st.sidebar.color_picker("لون خلفية الصورة العام:", "#FDFBF7")
show_frame = st.sidebar.checkbox("إضافة إطار عام للصورة", value=True)
frame_color = st.sidebar.color_picker("لون الإطار العام:", "#D3C5A3")
gap = st.sidebar.slider("المسافة بين الأقسام:", 20, 200, 60)

st.sidebar.subheader("7. الخط والمعالجة المتقدمة")
selected_font_file = st.sidebar.selectbox("اختر نوع الخط:", available_fonts) if available_fonts else None
shift_harakat = st.sidebar.checkbox("تصحيح موضع التشكيل (فعّله إذا كان التشكيل غير متطابق)", value=False)

# ================= واجهة الإدخال =================
col1, col2 = st.columns([2, 1]) 
with col1:
    enable_smart_parse = st.checkbox("🤖 تفعيل التقسيم الذكي (بالكلمات المفتاحية)", value=True)
    full_text_input = st.text_area(
        "أدخل النص هنا:",
        value="", 
        height=200,
        placeholder="الصق نص الحديث هنا...\nإذا ألغيت الذكاء الاصطناعي، اترك سطراً فارغاً بين السند والحديث والتخريج."
    )

# ================= خوارزميات تحليل النص =================
def parse_text_smart(text):
    if not text.strip(): return "", "", ""
    lines = text.split('\n')
    intro, hadith, grade = [], [], []
    state = 0 
    grade_keywords = ["رواه", "أخرجه", "صححه", "صحيح", "متفق عليه", "حسن", "رقم", "الألباني", "ابن باز", "الراوي:"]
    intro_end_keywords = ["قال:", "يقول:", "ﷺ", "صلى الله عليه وسلم:", "عنه:", "فيما يروي عن ربه"]

    for line in lines:
        if not line.strip(): continue
        if state == 1 and any(k in line for k in grade_keywords): state = 2
        
        if state == 0:
            intro.append(line)
            if any(k in line for k in intro_end_keywords): state = 1
        elif state == 1: hadith.append(line)
        elif state == 2: grade.append(line)
            
    if not hadith and intro: return "", "\n".join(intro), ""
    return "\n".join(intro), "\n".join(hadith), "\n".join(grade)

def parse_text_manual(text):
    if not text.strip(): return "", "", ""
    parts = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    intro, hadith, grade = "", "", ""
    if len(parts) >= 3:
        intro, hadith = parts[0], parts[1]
        grade = "\n".join(parts[2:]) 
    elif len(parts) == 2:
        intro, hadith = parts[0], parts[1]
    elif len(parts) == 1:
        hadith = parts[0]
    return intro, hadith, grade

if enable_smart_parse:
    intro_part, hadith_part, grade_part = parse_text_smart(full_text_input)
else:
    intro_part, hadith_part, grade_part = parse_text_manual(full_text_input)

# ================= معالجة اللغة العربية المتقدمة =================
reshaper_config = {
    'delete_harakat': False,
    'support_ligatures': True, 
    'shift_harakat_position': shift_harakat # ربط الخيار بالزر
}
reshaper = arabic_reshaper.ArabicReshaper(configuration=reshaper_config)

def prepare_arabic(text):
    if not text.strip(): return ""
    text = text.replace("ﷺ", "صلى الله عليه وسلم").replace("ﷻ", "جل جلاله")
    
    # حل مشكلة الأقواس المعكوسة والمربعات باستخدام base_dir='R'
    reshaped_text = reshaper.reshape(text)
    return get_display(reshaped_text, base_dir='R')

def wrap_text(text, font, max_width):
    if not text.strip(): return ""
    lines = []
    for paragraph in text.split('\n'):
        words = paragraph.split(' ')
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word]) if current_line else word
            test_bbox = font.getbbox(prepare_arabic(test_line))
            test_width = test_bbox[2] - test_bbox[0] if test_bbox else 0
            
            if test_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        if current_line:
            lines.append(' '.join(current_line))
    return '\n'.join(lines)

def get_alignment_props(choice, width, pad):
    if "يمين" in choice: return width - pad, "ra", "right"
    elif "يسار" in choice: return pad, "la", "left"
    else: return width / 2, "ma", "center"

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# ================= توليد الصورة =================
if st.button("✨ توليد الصورة", type="primary"):
    if not selected_font_file:
        st.error("الرجاء رفع خط أولاً لتوليد الصورة.")
    elif not full_text_input.strip():
        st.error("الرجاء إدخال نص الحديث لتوليد الصورة.")
    else:
        try:
            img = Image.new('RGB', (image_width, image_height), color=bg_color)
            
            if bg_image_file:
                bg_pil = Image.open(bg_image_file).convert("RGBA")
                if bg_scale_mode == "تمديد (Stretch)":
                    bg_pil = bg_pil.resize((image_width, image_height))
                    img.paste(bg_pil, (0,0), bg_pil)
                elif bg_scale_mode == "ملء الشاشة (Cover)":
                    bg_ratio = bg_pil.width / bg_pil.height
                    img_ratio = image_width / image_height
                    if bg_ratio > img_ratio:
                        new_w = int(image_height * bg_ratio)
                        bg_pil = bg_pil.resize((new_w, image_height))
                        img.paste(bg_pil, (-(new_w - image_width) // 2, 0), bg_pil)
                    else:
                        new_h = int(image_width / bg_ratio)
                        bg_pil = bg_pil.resize((image_width, new_h))
                        img.paste(bg_pil, (0, -(new_h - image_height) // 2), bg_pil)
                elif bg_scale_mode == "تخصيص الحجم (Custom)":
                    new_w = int(bg_pil.width * custom_scale / 100)
                    new_h = int(bg_pil.height * custom_scale / 100)
                    bg_pil = bg_pil.resize((new_w, new_h))
                    img.paste(bg_pil, ((image_width - new_w) // 2, (image_height - new_h) // 2), bg_pil)
                    
            draw = ImageDraw.Draw(img)
            padding = 80 

            if show_frame:
                draw.rectangle([(30, 30), (image_width - 30, image_height - 30)], outline=frame_color, width=5)
                draw.rectangle([(40, 40), (image_width - 40, image_height - 40)], outline=frame_color, width=1)

            max_width = image_width - (padding * 2)
            max_height = image_height - (padding * 2)

            if auto_scale:
                best_x = 10 
                for x in range(60, 9, -1):
                    f_in = ImageFont.truetype(selected_font_file, 2 * x) 
                    f_hd = ImageFont.truetype(selected_font_file, 3 * x) 
                    f_gr = ImageFont.truetype(selected_font_file, x)     

                    w_in = wrap_text(intro_part, f_in, max_width)
                    w_hd = wrap_text(hadith_part, f_hd, max_width)
                    w_gr = wrap_text(grade_part, f_gr, max_width)

                    h_in = draw.multiline_textbbox((0,0), prepare_arabic(w_in), font=f_in, spacing=15)[3] if w_in else 0
                    h_hd = draw.multiline_textbbox((0,0), prepare_arabic(w_hd), font=f_hd, spacing=25)[3] if w_hd else 0
                    h_gr = draw.multiline_textbbox((0,0), prepare_arabic(w_gr), font=f_gr, spacing=15)[3] if w_gr else 0

                    total_h = h_in + h_hd + h_gr
                    if h_in and (h_hd or h_gr): total_h += gap
                    if h_hd and h_gr: total_h += gap

                    if total_h <= max_height:
                        best_x = x
                        break

                font_intro = ImageFont.truetype(selected_font_file, 2 * best_x)
                font_hadith = ImageFont.truetype(selected_font_file, 3 * best_x)
                font_grade = ImageFont.truetype(selected_font_file, best_x)
            else:
                font_intro = ImageFont.truetype(selected_font_file, intro_size)
                font_hadith = ImageFont.truetype(selected_font_file, hadith_size)
                font_grade = ImageFont.truetype(selected_font_file, grade_size)

            wrapped_intro = prepare_arabic(wrap_text(intro_part, font_intro, max_width))
            wrapped_hadith = prepare_arabic(wrap_text(hadith_part, font_hadith, max_width))
            wrapped_grade = prepare_arabic(wrap_text(grade_part, font_grade, max_width))

            x_intro, anchor_intro, align_in = get_alignment_props(align_intro, image_width, padding)
            x_hadith, anchor_hadith, align_hd = get_alignment_props(align_hadith, image_width, padding)
            x_grade, anchor_grade, align_gr = get_alignment_props(align_grade, image_width, padding)

            h_in = draw.multiline_textbbox((0,0), wrapped_intro, font=font_intro, spacing=15)[3] if wrapped_intro else 0
            h_hd = draw.multiline_textbbox((0,0), wrapped_hadith, font=font_hadith, spacing=25)[3] if wrapped_hadith else 0
            h_gr = draw.multiline_textbbox((0,0), wrapped_grade, font=font_grade, spacing=15)[3] if wrapped_grade else 0

            total_final_h = h_in + h_hd + h_gr
            if h_in and (h_hd or h_gr): total_final_h += gap
            if h_hd and h_gr: total_final_h += gap

            start_y = max(padding, (image_height - total_final_h) / 2)

            def draw_highlighted_text(x, y, text, font, text_color, bg_color, anchor, align, spacing):
                if not text: return 0
                bbox = draw.multiline_textbbox((x, y), text, font=font, anchor=anchor, align=align, spacing=spacing)
                
                if show_text_bg:
                    rgb = hex_to_rgb(bg_color)
                    rect_coords = [(bbox[0] - 15, bbox[1] - 10), (bbox[2] + 15, bbox[3] + 10)]
                    draw.rectangle(rect_coords, fill=rgb)
                    
                draw.multiline_text((x, y), text, font=font, fill=text_color, anchor=anchor, align=align, spacing=spacing)
                return bbox[3] - bbox[1] 

            if wrapped_intro:
                h = draw_highlighted_text(x_intro, start_y, wrapped_intro, font_intro, intro_text_color, intro_bg_color, anchor_intro, align_in, 15)
                start_y += h + gap
                
            if wrapped_hadith:
                h = draw_highlighted_text(x_hadith, start_y, wrapped_hadith, font_hadith, hadith_text_color, hadith_bg_color, anchor_hadith, align_hd, 25)
                start_y += h + gap
                
            if wrapped_grade:
                draw_highlighted_text(x_grade, start_y, wrapped_grade, font_grade, grade_text_color, grade_bg_color, anchor_grade, align_gr, 15)

            st.session_state['final_image'] = img

        except Exception as e:
            st.error(f"حدث خطأ أثناء المعالجة: {e}")

if 'final_image' in st.session_state:
    st.image(st.session_state['final_image'], caption="معاينة الصورة النهائية", use_column_width=True)
    
    buf = io.BytesIO()
    st.session_state['final_image'].save(buf, format="PNG")
    byte_im = buf.getvalue()
    
    st.download_button("📥 تحميل الصورة", data=byte_im, file_name="hadith_pro_bg.png", mime="image/png")
