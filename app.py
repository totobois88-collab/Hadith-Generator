import streamlit as st
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont
import io
import os

st.set_page_config(page_title="صانع صور الأحاديث", page_icon="📜", layout="wide")

st.title("صانع صور الأحاديث النبوية 📜")
st.write("أدخل بيانات الحديث وتحكم في الشكل والتصميم من القائمة الجانبية.")

# ================= القائمة الجانبية (للتحكم في التصميم) =================
st.sidebar.header("🎨 إعدادات التصميم")

st.sidebar.subheader("1. أبعاد الصورة")
image_width = st.sidebar.slider("عرض الصورة:", min_value=600, max_value=2000, value=1200, step=100)
image_height = st.sidebar.slider("طول الصورة:", min_value=400, max_value=2000, value=800, step=100)

st.sidebar.subheader("2. الألوان والشكل")
bg_color = st.sidebar.color_picker("لون الخلفية:", "#FDFBF7")
text_color = st.sidebar.color_picker("لون نص الحديث والمقدمة:", "#282828")
grade_color = st.sidebar.color_picker("لون التخريج:", "#785028")
show_frame = st.sidebar.checkbox("إضافة إطار (برواز) للصورة", value=True)
frame_color = st.sidebar.color_picker("لون الإطار:", "#D3C5A3")

st.sidebar.subheader("3. أحجام الخطوط")
intro_font_size = st.sidebar.slider("حجم خط المقدمة:", 20, 100, 35)
hadith_font_size = st.sidebar.slider("حجم خط الحديث:", 30, 150, 70)
grade_font_size = st.sidebar.slider("حجم خط التخريج:", 20, 100, 35)


# ================= واجهة إدخال النصوص (في المنتصف) =================
col1, col2 = st.columns([2, 1]) # تقسيم الشاشة لترتيب أفضل

with col1:
    intro_input = st.text_area("السند والمقدمة:", "عن أمير المؤمنين أبي حفص عمر بن الخطاب رضي الله عنه قال:\nسمعت رسول الله ﷺ يقول:")
    hadith_input = st.text_area("نص الحديث:", "« إنما الأعمال بالنيات، وإنما لكل امرئ ما نوى »", height=150)
    grade_input = st.text_input("التخريج والصحة:", "رواه البخاري ومسلم")


# ================= دالة معالجة اللغة العربية =================
def prepare_arabic(text):
    reshaper = arabic_reshaper.ArabicReshaper(configuration={
        'delete_harakat': False,
        'support_ligatures': True,
    })
    reshaped_text = reshaper.reshape(text)
    return get_display(reshaped_text)


# ================= توليد الصورة =================
if st.button("✨ توليد الصورة", type="primary"):
    # معالجة النصوص
    fixed_intro = "\n".join([prepare_arabic(line) for line in intro_input.split('\n')])
    fixed_hadith = "\n".join([prepare_arabic(line) for line in hadith_input.split('\n')])
    fixed_grade = prepare_arabic(grade_input)

    # إنشاء الصورة باللون المختار
    img = Image.new('RGB', (image_width, image_height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # رسم الإطار إذا تم تفعيله
    if show_frame:
        # رسم مستطيل فارغ كإطار (نترك مسافة 30 بكسل من كل الحواف)
        draw.rectangle(
            [(30, 30), (image_width - 30, image_height - 30)],
            outline=frame_color,
            width=5
        )
        # إطار داخلي رفيع لمسة جمالية
        draw.rectangle(
            [(40, 40), (image_width - 40, image_height - 40)],
            outline=frame_color,
            width=1
        )

    # تحميل الخط (من المستودع)
    font_path = "Amiri-Regular.ttf"
    try:
        font_intro = ImageFont.truetype(font_path, intro_font_size)
        font_hadith = ImageFont.truetype(font_path, hadith_font_size)
        font_grade = ImageFont.truetype(font_path, grade_font_size)
    except OSError:
        st.error(f"لم يتم العثور على ملف الخط '{font_path}'. يرجى التأكد من رفعه إلى المستودع.")
        st.stop()

    # حساب أماكن النصوص بناءً على ارتفاع الصورة الديناميكي
    pos_intro = image_height * 0.20  # 20% من الأعلى
    pos_hadith = image_height * 0.50 # في المنتصف تماماً
    pos_grade = image_height * 0.82  # 82% من الأعلى (قريب للأسفل)

    # رسم النصوص
    draw.multiline_text((image_width / 2, pos_intro), fixed_intro, font=font_intro, fill=text_color, anchor="mm", align="center", spacing=15)
    draw.multiline_text((image_width / 2, pos_hadith), fixed_hadith, font=font_hadith, fill=text_color, anchor="mm", align="center", spacing=25)
    draw.multiline_text((image_width / 2, pos_grade), fixed_grade, font=font_grade, fill=grade_color, anchor="mm", align="center", spacing=15)

    # عرض الصورة في الموقع
    st.image(img, caption="معاينة الصورة النهائية", use_column_width=True)

    # تحويل الصورة إلى بايتات للتحميل
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    byte_im = buf.getvalue()

    # زر التحميل
    st.download_button(
        label="📥 تحميل الصورة العالية الدقة",
        data=byte_im,
        file_name="hadith_hd.png",
        mime="image/png"
    )
