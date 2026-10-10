import streamlit as st
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont
import io
import os

# إعدادات الصفحة
st.set_page_config(page_title="صانع صور الأحاديث", page_icon="📜", layout="centered")

st.title("صانع صور الأحاديث النبوية 📜")
st.write("أدخل نص الحديث والتخريج لتوليد صورة جميلة جاهزة للتحميل.")

# واجهة إدخال النصوص
hadith_input = st.text_area("نص الحديث:", "قال رسول الله ﷺ:\n« إنما الأعمال بالنيات، وإنما لكل امرئ ما نوى »")
grade_input = st.text_input("التخريج:", "رواه البخاري ومسلم")

# إعدادات معالجة اللغة العربية
reshaper = arabic_reshaper.ArabicReshaper(configuration={
    'delete_harakat': False,
    'support_ligatures': True,
})

def prepare_arabic(text):
    return get_display(reshaper.reshape(text))

# زر التوليد
if st.button("توليد الصورة", type="primary"):
    # معالجة النصوص
    fixed_hadith = "\n".join([prepare_arabic(line) for line in hadith_input.split('\n')])
    fixed_grade = prepare_arabic(grade_input)

    # إعداد الصورة
    image_width, image_height = 900, 500
    img = Image.new('RGB', (image_width, image_height), color=(253, 251, 247))
    draw = ImageDraw.Draw(img)

    # تحميل الخط (يجب أن يكون مرفوعاً مع ملفات الموقع)
    font_path = "Tajawal-Bold.ttf"
    try:
        font_hadith = ImageFont.truetype(font_path, 40)
        font_grade = ImageFont.truetype(font_path, 28)
    except OSError:
        st.error("لم يتم العثور على ملف الخط 'Tajawal-Bold.ttf'. يرجى التأكد من رفعه.")
        st.stop()

    # رسم النصوص
    draw.multiline_text((image_width / 2, image_height / 2 - 40), fixed_hadith, font=font_hadith, fill=(40, 40, 40), anchor="mm", align="center", spacing=20)
    draw.text((image_width / 2, image_height / 2 + 120), fixed_grade, font=font_grade, fill=(120, 80, 40), anchor="mm")

    # عرض الصورة في الموقع
    st.image(img, caption="معاينة الصورة", use_column_width=True)

    # تحويل الصورة إلى بايتات لتفعيل زر التحميل
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    byte_im = buf.getvalue()

    # زر التحميل
    st.download_button(
        label="📥 تحميل الصورة",
        data=byte_im,
        file_name="hadith_image.png",
        mime="image/png"
    )