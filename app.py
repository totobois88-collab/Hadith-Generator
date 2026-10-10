import streamlit as st
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont
import io
import os
import urllib.request

st.set_page_config(page_title="صانع صور الأحاديث", page_icon="📜", layout="centered")

st.title("صانع صور الأحاديث النبوية 📜")
st.write("أدخل بيانات الحديث لتوليد صورة احترافية بتنسيق جميل.")

# واجهة إدخال النصوص
intro_input = st.text_area("السند والمقدمة:", "عن أمير المؤمنين أبي حفص عمر بن الخطاب رضي الله عنه قال:\nسمعت رسول الله ﷺ يقول:")
hadith_input = st.text_area("نص الحديث:", "« إنما الأعمال بالنيات، وإنما لكل امرئ ما نوى »")
grade_input = st.text_input("التخريج والصحة:", "رواه البخاري ومسلم")

# تحميل الخط الكامل تلقائياً لتفادي مشاكل المربعات
font_path = "Amiri-Regular.ttf"
if not os.path.exists(font_path):
    with st.spinner("جاري تحميل الخطوط العربية الأصلية... (يحدث مرة واحدة فقط)"):
        font_url = "https://github.com/googlefonts/amiri/raw/main/fonts/ttf/Amiri-Regular.ttf"
        urllib.request.urlretrieve(font_url, font_path)

def prepare_arabic(text):
    # إعدادات مخصصة لدعم خط أميري بشكل كامل
    reshaper = arabic_reshaper.ArabicReshaper(configuration={
        'delete_harakat': False,
        'support_ligatures': True,
    })
    reshaped_text = reshaper.reshape(text)
    return get_display(reshaped_text)

if st.button("توليد الصورة", type="primary"):
    fixed_intro = "\n".join([prepare_arabic(line) for line in intro_input.split('\n')])
    fixed_hadith = "\n".join([prepare_arabic(line) for line in hadith_input.split('\n')])
    fixed_grade = prepare_arabic(grade_input)

    image_width, image_height = 900, 600
    img = Image.new('RGB', (image_width, image_height), color=(253, 251, 247))
    draw = ImageDraw.Draw(img)

    try:
        font_small = ImageFont.truetype(font_path, 32)
        font_large = ImageFont.truetype(font_path, 55)
    except OSError:
        st.error("حدث خطأ أثناء قراءة ملف الخط.")
        st.stop()

    text_color = (40, 40, 40)
    grade_color = (120, 80, 40)

    # رسم النصوص
    draw.multiline_text((image_width / 2, 130), fixed_intro, font=font_small, fill=text_color, anchor="mm", align="center", spacing=15)
    draw.multiline_text((image_width / 2, 300), fixed_hadith, font=font_large, fill=text_color, anchor="mm", align="center", spacing=20)
    draw.multiline_text((image_width / 2, 490), fixed_grade, font=font_small, fill=grade_color, anchor="mm", align="center", spacing=15)

    st.image(img, caption="معاينة الصورة", use_column_width=True)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    byte_im = buf.getvalue()

    st.download_button(
        label="📥 تحميل الصورة",
        data=byte_im,
        file_name="hadith_image.png",
        mime="image/png"
    )
