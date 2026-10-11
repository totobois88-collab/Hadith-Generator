import streamlit as st
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont
import io
import os
import glob
import re

# ================= إعدادات الصفحة =================
st.set_page_config(page_title="صانع صور الأحاديث الذكي", page_icon="📜", layout="wide")

st.title("صانع صور الأحاديث النبوية الذكي 📜")
st.write("أدخل النص، وسيقوم النظام بتوزيعه وضبط مقاساته ليلائم حجم الصورة والخلفية آلياً.")

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

st.sidebar.subheader("3. محاذاة النصوص المستقلة")
align_opts = ["وسط (Center)", "يمين (Right)", "يسار (Left)"]
align_intro = st.sidebar.selectbox("محاذاة السند (الأعلى):", align_opts, index=0)
align_hadith = st.sidebar.selectbox("محاذاة الحديث (الوسط):", align_opts, index=0)
align_grade = st.sidebar.selectbox("محاذاة التخريج (الأسفل):", align_opts, index=0)

st.sidebar.subheader("4. الألوان والشكل")
bg_color = st.sidebar.color_picker("لون الخلفية (في حال عدم رفع صورة):", "#FDFBF7")
text_color = st.sidebar.color_picker("لون نص الحديث والمقدمة:", "#282828")
grade_color = st.sidebar.color_picker("لون التخريج:", "#785028")
show_frame = st.sidebar.checkbox("إضافة إطار (برواز)", value=True)
frame_color = st.sidebar.color_picker("لون الإطار:", "#D3C5A3")
gap = st.sidebar.slider("المسافة بين الأقسام:", 20, 200, 60)

st.sidebar.subheader("5. نوع الخط")
selected_font_file = st.sidebar.selectbox("اختر نوع الخط:", available_fonts) if available_fonts else None

# ================= واجهة الإدخال واختيار نوع التقسيم =================
col1, col2 = st.columns([2, 1]) 
with col1:
    # خيار تفعيل/إلغاء الذكاء الاصطناعي
    enable_smart_parse = st.checkbox("🤖 تفعيل التقسيم الذكي للنص (التعرف الآلي)", value=True)
    
    if enable_smart_parse:
        help_text = "أدخل النص كاملاً (وسيقوم الذكاء الاصطناعي بفصل السند والحديث والتخريج):"
        default_text = "عن أبي هريرة رضي الله عنه قال: قال رسول الله ﷺ\nمن حسن إسلام المرء تركه ما لا يعنيه\nرواه الترمذي وحسنه"
    else:
        help_text = "أدخل النص كاملاً (يجب ترك سطر فارغ بين السند، والحديث، والتخريج للفصل بينهم):"
        default_text = "عن أبي هريرة رضي الله عنه قال: قال رسول الله ﷺ\n\nمن حسن إسلام المرء تركه ما لا يعنيه\n\nرواه الترمذي وحسنه"

    full_text_input = st.text_area(help_text, default_text, height=200)

# ================= خوارزميات تحليل النص =================
def parse_text_smart(text):
    """خوارزمية الذكاء الاصطناعي للتقسيم الآلي"""
    pattern = r'(?s)^(.*?)([«\(\["\{].*?[»\)\]"\}])(.*)$'
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip(), match.group(2).strip(), match.group(3).strip()
    
    lines = text.split('\n')
    intro, hadith, grade = [], [], []
    state = 0 
    
    grade_keywords = ["رواه", "أخرجه", "صححه", "صحيح", "متفق عليه", "حسن", "رقم", "الألباني", "ابن باز", "المحدث:", "الراوي:"]
    intro_end_keywords = ["قال:", "يقول:", "ﷺ", "صلى الله عليه وسلم:", "عنه:", "فيما يروي عن ربه"]

    for line in lines:
        if not line.strip(): continue
        
        if state == 1 and any(k in line for k in grade_keywords):
            state = 2
            
        if state == 0:
            intro.append(line)
            if any(k in line for k in intro_end_keywords):
                state = 1
        elif state == 1:
            hadith.append(line)
        elif state == 2:
            grade.append(line)
            
    if not hadith and intro:
        return "", "\n".join(intro), ""
        
    return "\n".join(intro), "\n".join(hadith), "\n".join(grade)

def parse_text_manual(text):
    """خوارزمية التقسيم اليدوي بناءً على السطر الفارغ"""
    # يقسم النص عندما يجد سطرين متتاليين (سطر فارغ بينهما)
    parts = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    intro, hadith, grade = "", "", ""
    
    if len(parts) >= 3:
        intro = parts[0]
        hadith = parts[1]
        grade = "\n".join(parts[2:]) # جمع ما تبقى في التخريج
    elif len(parts) == 2:
        intro = parts[0]
        hadith = parts[1]
    elif len(parts) == 1:
        hadith = parts[0]
        
    return intro, hadith, grade

# تنفيذ الخوارزمية بناءً على اختيار المستخدم
if enable_smart_parse:
    intro_part, hadith_part, grade_part = parse_text_smart(full_text_input)
else:
    intro_part, hadith_part, grade_part = parse_text_manual(full_text_input)

# عرض نتيجة الفحص
with st.expander("🔍 اضغط لرؤية كيف تم تقسيم النص:"):
    st.info(f"**السند (المقدمة):** {intro_part}")
    st.success(f"**الحديث:** {hadith_part}")
    st.warning(f"**التخريج:** {grade_part}")

# ================= معالجة اللغة العربية (منع المربعات) =================
reshaper_config = {
    'delete_harakat': False,
    'support_ligatures': False, 
    'shift_harakat_position': False
}
reshaper = arabic_reshaper.ArabicReshaper(configuration=reshaper_config)

def prepare_arabic(text):
    if not text.strip(): return ""
    text = text.replace("ﷺ", "صلى الله عليه وسلم").replace("ﷻ", "جل جلاله").replace("رضي الله عنه", "رضي الله عنه")
    return get_display(reshaper.reshape(text))

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

# ================= توليد الصورة =================
if st.button("✨ توليد الصورة", type="primary"):
    if not selected_font_file:
        st.error("الرجاء رفع خط أولاً لتوليد الصورة.")
        st.stop()

    img = Image.new('RGB', (image_width, image_height), color=bg_color)
    
    # رسم الخلفية المرفوعة إن وجدت
    if bg_image_file:
        try:
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
                    x_offset = (new_w - image_width) // 2
                    img.paste(bg_pil, (-x_offset, 0), bg_pil)
                else:
                    new_h = int(image_width / bg_ratio)
                    bg_pil = bg_pil.resize((image_width, new_h))
                    y_offset = (new_h - image_height) // 2
                    img.paste(bg_pil, (0, -y_offset), bg_pil)
            elif bg_scale_mode == "تخصيص الحجم (Custom)":
                new_w = int(bg_pil.width * custom_scale / 100)
                new_h = int(bg_pil.height * custom_scale / 100)
                bg_pil = bg_pil.resize((new_w, new_h))
                x_offset = (image_width - new_w) // 2
                y_offset = (image_height - new_h) // 2
                img.paste(bg_pil, (x_offset, y_offset), bg_pil)
        except Exception as e:
            st.error("حدث خطأ أثناء قراءة صورة الخلفية.")
            
    draw = ImageDraw.Draw(img)
    padding = 80 

    if show_frame:
        draw.rectangle([(30, 30), (image_width - 30, image_height - 30)], outline=frame_color, width=5)
        draw.rectangle([(40, 40), (image_width - 40, image_height - 40)], outline=frame_color, width=1)

    max_width = image_width - (padding * 2)
    max_height = image_height - (padding * 2)

    # حساب حجم الخطوط آلياً (1 للتخريج، 2 للسند، 3 للحديث)
    best_x = 10 
    for x in range(60, 9, -1):
        try:
            f_in = ImageFont.truetype(selected_font_file, 2 * x) 
            f_hd = ImageFont.truetype(selected_font_file, 3 * x) 
            f_gr = ImageFont.truetype(selected_font_file, x)     
        except OSError:
            st.error("الملف المرفوع للخط تالف.")
            st.stop()

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

    # رسم النصوص 
    if wrapped_intro:
        draw.multiline_text((x_intro, start_y), wrapped_intro, font=font_intro, fill=text_color, anchor=anchor_intro, align=align_in, spacing=15)
        start_y += h_in + gap
        
    if wrapped_hadith:
        draw.multiline_text((x_hadith, start_y), wrapped_hadith, font=font_hadith, fill=text_color, anchor=anchor_hadith, align=align_hd, spacing=25)
        start_y += h_hd + gap
        
    if wrapped_grade:
        draw.multiline_text((x_grade, start_y), wrapped_grade, font=font_grade, fill=grade_color, anchor=anchor_grade, align=align_gr, spacing=15)

    st.image(img, caption=f"معاينة الصورة النهائية (التقسيم المستخدم: {'الذكي' if enable_smart_parse else 'اليدوي'})", use_column_width=True)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    byte_im = buf.getvalue()

    st.download_button("📥 تحميل الصورة", data=byte_im, file_name="hadith_smart_bg.png", mime="image/png")
