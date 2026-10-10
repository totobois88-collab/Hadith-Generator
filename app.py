import streamlit as st
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont
import io

st.set_page_config(page_title="صانع صور الأحاديث", page_icon="📜", layout="centered")

st.title("صانع صور الأحاديث النبوية 📜")
st.write("أدخل بيانات الحديث لتوليد صورة احترافية بتنسيق جميل.")

intro_input = st.text_area("السند والمقدمة:", "عن أمير المؤمنين أبي حفص عمر بن الخطاب رضي الله عنه قال:\nسمعت رسول الله ﷺ يقول:")
hadith_input = st.text_area("نص الحديث:", "« إنما الأعمال بالنيات، وإنما لكل امرئ ما نوى »")
grade_input = st.text_input("التخريج والصحة:", "رواه البخاري ومسلم")

def prepare_arabic(text):
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

    # استخدام الملف المرفوع مباشرة من المستودع
    font_path = "Amiri-Regular.ttf"
    
    try:
        font_small = ImageFont.truetype(font_path, 32)
        font_large = ImageFont.truetype(font_path, 55)
    except OSError:
        st.error(f"لم يتم العثور على ملف الخط '{font_path}'. يرجى التأكد من رفعه إلى المستودع.")
        st.stop()

    text_color = (40, 40, 40)
    grade_color = (120, 80, 40)

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
