import streamlit as st
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont
import io
import os
import glob
import re

# ================= إعدادات الصفحة =================
st.set_page_config(page_title="صانع صور الأحاديث الاحترافي", page_icon="📜", layout="wide")

st.title("صانع صور الأحاديث النبوية 📜")
st.write("أدخل النص كاملاً في المربع أدناه. سيقوم النظام آلياً باستخراج الحديث من بين الأقواس « » أو ( ) وتوزيع النص.")

# ================= البحث عن الخطوط المرفوعة =================
available_fonts = glob.glob("*.ttf") + glob.glob("*.otf")
if not available_fonts:
    st.warning("لم يتم العثور على خطوط. يرجى رفع ملفات .ttf (مثل NotoNaskhArabic-Regular.ttf) إلى المستودع.")

# ================= القائمة الجانبية (إعدادات التصميم) =================
st.sidebar.header("🎨 إعدادات التصميم")

st.sidebar.subheader("1. أبعاد الصورة")
image_width = st.sidebar.slider("عرض الصورة:", 600, 2000, 1200, 100)
image_height = st.sidebar.slider("طول الصورة:", 600, 2500, 1200, 100)

st.sidebar.subheader("2. محاذاة النصوص المستقلة")
align_opts = ["وسط (Center)", "يمين (Right)", "يسار (Left)"]
align_intro = st.sidebar.selectbox("محاذاة السند (الأعلى):", align_opts, index=0)
align_hadith = st.sidebar.selectbox("محاذاة الحديث (الوسط):", align_opts, index=0)
align_grade = st.sidebar.selectbox("محاذاة التخريج (الأسفل):", align_opts, index=0)

st.sidebar.subheader("3. الألوان والشكل")
bg_color = st.sidebar.color_picker("لون الخلفية:", "#FDFBF7")
text_color = st.sidebar.color_picker("لون نص الحديث والمقدمة:", "#282828")
grade_color = st.sidebar.color_picker("لون التخريج:", "#785028")
show_frame = st.sidebar.checkbox("إضافة إطار (برواز)", value=True)
frame_color = st.sidebar.color_picker("لون الإطار:", "#D3C5A3")
gap = st.sidebar.slider("المسافة بين الأقسام:", 20, 200, 80)

st.sidebar.subheader("4. نوع وأحجام الخطوط")
selected_font_file = st.sidebar.selectbox("اختر نوع الخط:", available_fonts) if available_fonts else None
intro_font_size = st.sidebar.slider("حجم خط المقدمة:", 20, 150, 40)
hadith_font_size = st.sidebar.slider("حجم خط الحديث:", 30, 200, 75)
grade_font_size = st.sidebar.slider("حجم خط التخريج:", 20, 150, 40)

# ================= واجهة الإدخال الذكية =================
col1, col2 = st.columns([2, 1]) 
with col1:
    full_text_input = st.text_area(
        "أدخل النص كاملاً هنا:", 
        "عن أمير المؤمنين أبي حفص عمر بن الخطاب رضي الله عنه قال: سمعت رسول الله ﷺ يقول:\n« إنما الأعمال بالنيات، وإنما لكل امرئ ما نوى »\nرواه البخاري ومسلم", 
        height=200
    )

# ================= تحليل النص آلياً (Regex) =================
def parse_text_auto(text):
    # يبحث عن أول قوس ويأخذ كل ما بداخله كحديث، وما قبله مقدمة، وما بعده تخريج
    pattern = r'(?s)^(.*?)([«\(\["\{].*?[»\)\]"\}])(.*)$'
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip(), match.group(2).strip(), match.group(3).strip()
    return "", text.strip(), "" # في حال عدم وجود أقواس، يضع النص كله في الوسط

intro_part, hadith_part, grade_part = parse_text_auto(full_text_input)

# عرض نتيجة الفحص للمستخدم ليتأكد من التقسيم
with st.expander("🔍 اضغط هنا لرؤية كيف قام الذكاء الاصطناعي بتقسيم نصك:"):
    st.info(f"**السند:** {intro_part}")
    st.success(f"**الحديث:** {hadith_part}")
    st.warning(f"**التخريج:** {grade_part}")

# ================= معالجة اللغة العربية والتشكيل =================
reshaper_config = {
    'delete_harakat': False,
    'support_ligatures': True, # ضرورية لتشابك الحروف والتشكيل
    'shift_harakat_position': True # يمنع تشوه الحركات في بعض الخطوط
}
reshaper = arabic_reshaper.ArabicReshaper(configuration=reshaper_config)

def prepare_arabic(text):
    if not text.strip(): return ""
    text = text.replace("ﷺ", "صلى الله عليه وسلم").replace("ﷻ", "جل جلاله")
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

# ================= عملية توليد الصورة =================
if st.button("✨ توليد الصورة", type="primary"):
    if not selected_font_file:
        st.error("الرجاء رفع خط أولاً لتوليد الصورة.")
        st.stop()

    img = Image.new('RGB', (image_width, image_height), color=bg_color)
    draw = ImageDraw.Draw(img)
    padding = 80 

    if show_frame:
        draw.rectangle([(30, 30), (image_width - 30, image_height - 30)], outline=frame_color, width=5)
        draw.rectangle([(40, 40), (image_width - 40, image_height - 40)], outline=frame_color, width=1)

    try:
        font_intro = ImageFont.truetype(selected_font_file, intro_font_size)
        font_hadith = ImageFont.truetype(selected_font_file, hadith_font_size)
        font_grade = ImageFont.truetype(selected_font_file, grade_font_size)
    except OSError:
        st.error("الملف المرفوع للخط تالف، حاول رفع خط آخر.")
        st.stop()

    max_width = image_width - (padding * 2)

    wrapped_intro = prepare_arabic(wrap_text(intro_part, font_intro, max_width))
    wrapped_hadith = prepare_arabic(wrap_text(hadith_part, font_hadith, max_width))
    wrapped_grade = prepare_arabic(wrap_text(grade_part, font_grade, max_width))

    x_intro, anchor_intro, align_in = get_alignment_props(align_intro, image_width, padding)
    x_hadith, anchor_hadith, align_hd = get_alignment_props(align_hadith, image_width, padding)
    x_grade, anchor_grade, align_gr = get_alignment_props(align_grade, image_width, padding)

    # حساب الارتفاعات
    intro_h = draw.multiline_textbbox((0,0), wrapped_intro, font=font_intro, spacing=15)[3] if wrapped_intro else 0
    hadith_h = draw.multiline_textbbox((0,0), wrapped_hadith, font=font_hadith, spacing=25)[3] if wrapped_hadith else 0
    grade_h = draw.multiline_textbbox((0,0), wrapped_grade, font=font_grade, spacing=15)[3] if wrapped_grade else 0

    total_h = intro_h + hadith_h + grade_h
    # إضافة المسافات فقط إذا كانت الأجزاء موجودة
    if intro_h and (hadith_h or grade_h): total_h += gap
    if hadith_h and grade_h: total_h += gap

    start_y = max(padding, (image_height - total_h) / 2)

    # رسم النصوص
    if wrapped_intro:
        draw.multiline_text((x_intro, start_y), wrapped_intro, font=font_intro, fill=text_color, anchor=anchor_intro, align=align_in, spacing=15)
        start_y += intro_h + gap
        
    if wrapped_hadith:
        draw.multiline_text((x_hadith, start_y), wrapped_hadith, font=font_hadith, fill=text_color, anchor=anchor_hadith, align=align_hd, spacing=25)
        start_y += hadith_h + gap
        
    if wrapped_grade:
        draw.multiline_text((x_grade, start_y), wrapped_grade, font=font_grade, fill=grade_color, anchor=anchor_grade, align=align_gr, spacing=15)

    st.image(img, caption="معاينة الصورة", use_column_width=True)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    byte_im = buf.getvalue()

    st.download_button("📥 تحميل الصورة", data=byte_im, file_name="hadith_pro.png", mime="image/png")
