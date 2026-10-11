import streamlit as st
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont
import io
import os
import glob

st.set_page_config(page_title="صانع صور الأحاديث", page_icon="📜", layout="wide")

st.title("صانع صور الأحاديث النبوية 📜")
st.write("أدخل بيانات الحديث وتحكم في الشكل والتصميم. يمكنك رفع خطوط بصيغة `.ttf` أو `.otf` إلى المستودع وستظهر هنا.")

# ================= البحث عن الخطوط المرفوعة (ttf و otf) =================
# تم تعديل الكود للبحث عن الصيغتين
available_fonts = glob.glob("*.ttf") + glob.glob("*.otf")
if not available_fonts:
    st.error("لم يتم العثور على أي ملف خط (.ttf أو .otf). يرجى رفع ملفات الخطوط إلى المستودع.")
    st.stop()

# ================= القائمة الجانبية (للتحكم في التصميم) =================
st.sidebar.header("🎨 إعدادات التصميم")

st.sidebar.subheader("1. أبعاد الصورة والمحاذاة")
image_width = st.sidebar.slider("عرض الصورة:", min_value=600, max_value=2000, value=1200, step=100)
image_height = st.sidebar.slider("طول الصورة:", min_value=600, max_value=2500, value=1200, step=100)
alignment_choice = st.sidebar.selectbox("محاذاة النص:", ["وسط (Center)", "يمين (Right)", "يسار (Left)"])

st.sidebar.subheader("2. الألوان والشكل")
bg_color = st.sidebar.color_picker("لون الخلفية:", "#FDFBF7")
text_color = st.sidebar.color_picker("لون نص الحديث والمقدمة:", "#282828")
grade_color = st.sidebar.color_picker("لون التخريج:", "#785028")
show_frame = st.sidebar.checkbox("إضافة إطار (برواز)", value=True)
frame_color = st.sidebar.color_picker("لون الإطار:", "#D3C5A3")
gap_between_sections = st.sidebar.slider("المسافة بين الأقسام:", 20, 200, 80)

st.sidebar.subheader("3. نوع وأحجام الخطوط")
selected_font_file = st.sidebar.selectbox("اختر نوع الخط:", available_fonts)

intro_font_size = st.sidebar.slider("حجم خط المقدمة:", 20, 150, 40)
hadith_font_size = st.sidebar.slider("حجم خط الحديث:", 30, 200, 75)
grade_font_size = st.sidebar.slider("حجم خط التخريج:", 20, 150, 40)

# ================= واجهة إدخال النصوص =================
col1, col2 = st.columns([2, 1]) 
with col1:
    intro_input = st.text_area("السند والمقدمة:", "عن أمير المؤمنين أبي حفص عمر بن الخطاب رضي الله عنه قال:\nسمعت رسول الله ﷺ يقول:")
    hadith_input = st.text_area("نص الحديث:", "« إنما الأعمال بالنيات، وإنما لكل امرئ ما نوى »", height=150)
    grade_input = st.text_input("التخريج والصحة:", "رواه البخاري ومسلم")

# ================= معالجة اللغة العربية والالتفاف (Wrapping) =================
reshaper = arabic_reshaper.ArabicReshaper(configuration={'delete_harakat': False, 'support_ligatures': True})

def prepare_arabic(text):
    return get_display(reshaper.reshape(text))

def wrap_text(text, font, max_width):
    lines = []
    for paragraph in text.split('\n'):
        words = paragraph.split(' ')
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
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


# ================= توليد الصورة =================
if st.button("✨ توليد الصورة", type="primary"):
    
    img = Image.new('RGB', (image_width, image_height), color=bg_color)
    draw = ImageDraw.Draw(img)

    padding = 80 
    if show_frame:
        draw.rectangle([(30, 30), (image_width - 30, image_height - 30)], outline=frame_color, width=5)
        draw.rectangle([(40, 40), (image_width - 40, image_height - 40)], outline=frame_color, width=1)

    # تحميل الخط (ttf أو otf)
    try:
        font_intro = ImageFont.truetype(selected_font_file, intro_font_size)
        font_hadith = ImageFont.truetype(selected_font_file, hadith_font_size)
        font_grade = ImageFont.truetype(selected_font_file, grade_font_size)
    except OSError:
        st.error(f"تعذر قراءة ملف الخط {selected_font_file}.")
        st.stop()

    max_text_width = image_width - (padding * 2)

    wrapped_intro = prepare_arabic(wrap_text(intro_input, font_intro, max_text_width))
    wrapped_hadith = prepare_arabic(wrap_text(hadith_input, font_hadith, max_text_width))
    wrapped_grade = prepare_arabic(wrap_text(grade_input, font_grade, max_text_width))

    if alignment_choice == "يمين (Right)":
        x_pos = image_width - padding
        anchor = "ra" 
        align = "right"
    elif alignment_choice == "يسار (Left)":
        x_pos = padding
        anchor = "la"
        align = "left"
    else: 
        x_pos = image_width / 2
        anchor = "ma"
        align = "center"

    intro_bbox = draw.multiline_textbbox((0,0), wrapped_intro, font=font_intro, spacing=15)
    intro_h = intro_bbox[3] - intro_bbox[1]

    hadith_bbox = draw.multiline_textbbox((0,0), wrapped_hadith, font=font_hadith, spacing=25)
    hadith_h = hadith_bbox[3] - hadith_bbox[1]

    grade_bbox = draw.multiline_textbbox((0,0), wrapped_grade, font=font_grade, spacing=15)
    grade_h = grade_bbox[3] - grade_bbox[1]

    total_height = intro_h + hadith_h + grade_h + (gap_between_sections * 2)
    start_y = (image_height - total_height) / 2

    if start_y < padding:
        start_y = padding

    draw.multiline_text((x_pos, start_y), wrapped_intro, font=font_intro, fill=text_color, anchor=anchor, align=align, spacing=15)
    
    start_y += intro_h + gap_between_sections 
    draw.multiline_text((x_pos, start_y), wrapped_hadith, font=font_hadith, fill=text_color, anchor=anchor, align=align, spacing=25)
    
    start_y += hadith_h + gap_between_sections 
    draw.multiline_text((x_pos, start_y), wrapped_grade, font=font_grade, fill=grade_color, anchor=anchor, align=align, spacing=15)

    st.image(img, caption="معاينة الصورة النهائية", use_column_width=True)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    byte_im = buf.getvalue()

    st.download_button(
        label="📥 تحميل الصورة",
        data=byte_im,
        file_name="hadith_hd.png",
        mime="image/png"
    )
