import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import glob
import re

# ================= إعدادات الصفحة =================
st.set_page_config(page_title="صانع صور الأحاديث", page_icon="📜", layout="wide")

st.title("صانع صور الأحاديث النبوية 📜")
st.write("أدخل النص، وسيقوم النظام بتوزيعه وضبط مقاساته ليلائم حجم الصورة.")

# ================= التحقق من دعم Raqm =================
try:
    HAS_RAQM = ImageFont.core.HAVE_RAQM
except AttributeError:
    HAS_RAQM = False

if not HAS_RAQM:
    st.warning(
        "⚠️ مكتبة Pillow الحالية لا تدعم محرك Raqm، لذلك قد يظهر التشكيل بشكل غير دقيق "
        "وقد تظهر بعض الرموز كمربعات. أضف `libraqm-dev` إلى ملف packages.txt عند النشر على Streamlit Cloud."
    )

# ================= البحث عن الخطوط وإعداد الخط الافتراضي =================
available_fonts = glob.glob("*.ttf") + glob.glob("*.otf")
default_font_index = 0

if not available_fonts:
    st.warning("لم يتم العثور على خطوط. يرجى رفع ملفات .ttf إلى المستودع.")
else:
    target_font = "kfgqpc-uthman-taha-naskh-bold.ttf"
    if target_font in available_fonts:
        default_font_index = available_fonts.index(target_font)

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

st.sidebar.subheader("6. المسافات بين الأقسام (التباعد)")
gap_intro_hadith = st.sidebar.slider("المسافة بين السند والحديث:", 0, 200, 60)
gap_hadith_grade = st.sidebar.slider("المسافة بين الحديث والتخريج:", 0, 200, 60)

st.sidebar.subheader("7. إعدادات أخرى")
bg_color = st.sidebar.color_picker("لون خلفية الصورة العام:", "#FDFBF7")
show_frame = st.sidebar.checkbox("إضافة إطار عام للصورة", value=True)
frame_color = st.sidebar.color_picker("لون الإطار العام:", "#D3C5A3")
selected_font_file = st.sidebar.selectbox("اختر نوع الخط:", available_fonts, index=default_font_index) if available_fonts else None

# ================= اللوغو (الشعار) والخريطة المصغرة =================
st.sidebar.subheader("8. الشعار (اللوغو)")
logo_file = st.sidebar.file_uploader("رفع الشعار (PNG شفاف أو JPG):", type=["png", "jpg", "jpeg"])

if logo_file:
    logo_size_pct = st.sidebar.slider("حجم الشعار (%)", min_value=5, max_value=100, value=20)
    logo_opacity = st.sidebar.slider("شفافية الشعار (%)", min_value=10, max_value=100, value=100)
    
    st.sidebar.write("**موضع الشعار:**")
    logo_x_pct = st.sidebar.slider("المحور الأفقي (يمين - يسار)", 0, 100, 50, label_visibility="collapsed")
    logo_y_pct = st.sidebar.slider("المحور العمودي (أعلى - أسفل)", 0, 100, 90, label_visibility="collapsed")
    
    # خريطة مصغرة لمعاينة موقع اللوغو
    try:
        preview_logo = Image.open(logo_file)
        aspect = preview_logo.height / preview_logo.width
        
        map_w = 200
        map_h = int(map_w * (image_height / image_width))
        minimap = Image.new('RGB', (map_w, map_h), color="#ECECEC")
        draw_map = ImageDraw.Draw(minimap)
        
        # رسم إطار الخريطة
        draw_map.rectangle([(0,0), (map_w-1, map_h-1)], outline="#B0B0B0", width=2)
        
        # حجم الشعار في الخريطة المصغرة
        logo_map_w = max(5, int(map_w * (logo_size_pct / 100.0)))
        logo_map_h = max(5, int(logo_map_w * aspect))
        
        # حساب الإحداثيات
        map_x = int((map_w - logo_map_w) * (logo_x_pct / 100.0))
        map_y = int((map_h - logo_map_h) * (logo_y_pct / 100.0))
        
        # رسم المربع الممثل للشعار
        draw_map.rectangle([(map_x, map_y), (map_x + logo_map_w, map_y + logo_map_h)], fill="#FF4B4B", outline="#990000")
        
        st.sidebar.image(minimap, caption="الخريطة المصغرة (المربع الأحمر يمثل موقع اللوغو)")
    except Exception:
        pass


# ================= واجهة الإدخال =================
col1, col2 = st.columns([2, 1])
with col1:
    full_text_input = st.text_area(
        "أدخل النص هنا:",
        value="",
        height=200,
        placeholder="الصق نص الحديث هنا...\nيجب ترك سطر فارغ (اضغط Enter مرتين) للفصل بين السند، والحديث، والتخريج."
    )

# ================= خوارزمية تحليل النص (اليدوي) =================
def parse_text_manual(text):
    if not text.strip():
        return "", "", ""
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

intro_part, hadith_part, grade_part = parse_text_manual(full_text_input)

with col1:
    if full_text_input.strip():
        with st.expander("🔍 اضغط هنا لمعاينة كيف تم تقسيم النص (بناءً على الأسطر الفارغة):"):
            st.info(f"**السند:**\n{intro_part}")
            st.success(f"**الحديث:**\n{hadith_part}")
            st.warning(f"**التخريج:**\n{grade_part}")

# ================= أدوات مساعدة =================
def load_font(path, size):
    try:
        return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)
    except Exception:
        return ImageFont.truetype(path, size)


def wrap_text(text, font, max_width):
    if not text.strip():
        return ""
    lines = []
    for paragraph in text.split('\n'):
        words = paragraph.split(' ')
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word]) if current_line else word
            bbox = font.getbbox(test_line, direction="rtl", language="ar")
            test_width = bbox[2] - bbox[0] if bbox else 0

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
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def text_height(draw, text, font, spacing):
    if not text:
        return 0
    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing, direction="rtl", language="ar")
    return bbox[3]


# ================= توليد الصورة =================
if st.button("✨ توليد الصورة", type="primary"):
    if not selected_font_file:
        st.error("الرجاء رفع خط أولاً لتوليد الصورة.")
    elif not full_text_input.strip():
        st.error("الرجاء إدخال نص الحديث لتوليد الصورة.")
    else:
        try:
            img = Image.new('RGB', (image_width, image_height), color=bg_color)

            # --- رسم الخلفية ---
            if bg_image_file:
                bg_pil = Image.open(bg_image_file).convert("RGBA")
                if bg_scale_mode == "تمديد (Stretch)":
                    bg_pil = bg_pil.resize((image_width, image_height))
                    img.paste(bg_pil, (0, 0), bg_pil)
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

            # --- حساب الخطوط ---
            if auto_scale:
                best_x = 10
                for x in range(60, 9, -1):
                    f_in = load_font(selected_font_file, 2 * x)
                    f_hd = load_font(selected_font_file, 3 * x)
                    f_gr = load_font(selected_font_file, x)

                    w_in = wrap_text(intro_part, f_in, max_width)
                    w_hd = wrap_text(hadith_part, f_hd, max_width)
                    w_gr = wrap_text(grade_part, f_gr, max_width)

                    h_in = text_height(draw, w_in, f_in, 15)
                    h_hd = text_height(draw, w_hd, f_hd, 25)
                    h_gr = text_height(draw, w_gr, f_gr, 15)

                    total_h = h_in + h_hd + h_gr
                    if h_in and (h_hd or h_gr): total_h += gap_intro_hadith
                    if h_hd and h_gr: total_h += gap_hadith_grade

                    if total_h <= max_height:
                        best_x = x
                        break

                font_intro = load_font(selected_font_file, 2 * best_x)
                font_hadith = load_font(selected_font_file, 3 * best_x)
                font_grade = load_font(selected_font_file, best_x)
            else:
                font_intro = load_font(selected_font_file, intro_size)
                font_hadith = load_font(selected_font_file, hadith_size)
                font_grade = load_font(selected_font_file, grade_size)

            wrapped_intro = wrap_text(intro_part, font_intro, max_width)
            wrapped_hadith = wrap_text(hadith_part, font_hadith, max_width)
            wrapped_grade = wrap_text(grade_part, font_grade, max_width)

            x_intro, anchor_intro, align_in = get_alignment_props(align_intro, image_width, padding)
            x_hadith, anchor_hadith, align_hd = get_alignment_props(align_hadith, image_width, padding)
            x_grade, anchor_grade, align_gr = get_alignment_props(align_grade, image_width, padding)

            h_in = text_height(draw, wrapped_intro, font_intro, 15)
            h_hd = text_height(draw, wrapped_hadith, font_hadith, 25)
            h_gr = text_height(draw, wrapped_grade, font_grade, 15)

            total_final_h = h_in + h_hd + h_gr
            if h_in and (h_hd or h_gr): total_final_h += gap_intro_hadith
            if h_hd and h_gr: total_final_h += gap_hadith_grade

            start_y = max(padding, (image_height - total_final_h) / 2)

            def draw_highlighted_text(x, y, text, font, text_color, bg_color_hex, anchor, align, spacing):
                if not text: return 0
                bbox = draw.multiline_textbbox((x, y), text, font=font, anchor=anchor, align=align, spacing=spacing, direction="rtl", language="ar")
                if show_text_bg:
                    rgb = hex_to_rgb(bg_color_hex)
                    rect_coords = [(bbox[0] - 15, bbox[1] - 10), (bbox[2] + 15, bbox[3] + 10)]
                    draw.rectangle(rect_coords, fill=rgb)
                draw.multiline_text((x, y), text, font=font, fill=text_color, anchor=anchor, align=align, spacing=spacing, direction="rtl", language="ar")
                return bbox[3] - bbox[1]

            if wrapped_intro:
                h = draw_highlighted_text(x_intro, start_y, wrapped_intro, font_intro, intro_text_color, intro_bg_color, anchor_intro, align_in, 15)
                start_y += h + gap_intro_hadith

            if wrapped_hadith:
                h = draw_highlighted_text(x_hadith, start_y, wrapped_hadith, font_hadith, hadith_text_color, hadith_bg_color, anchor_hadith, align_hd, 25)
                start_y += h + gap_hadith_grade

            if wrapped_grade:
                draw_highlighted_text(x_grade, start_y, wrapped_grade, font_grade, grade_text_color, grade_bg_color, anchor_grade, align_gr, 15)

            # --- رسم اللوغو فوق كل شيء ---
            if logo_file:
                logo_img = Image.open(logo_file).convert("RGBA")
                
                # تغيير الحجم
                resample_method = getattr(Image, 'Resampling', Image).LANCZOS
                logo_aspect = logo_img.height / logo_img.width
                target_w = max(10, int(image_width * (logo_size_pct / 100.0)))
                target_h = int(target_w * logo_aspect)
                logo_img = logo_img.resize((target_w, target_h), resample_method)
                
                # تطبيق الشفافية
                if logo_opacity < 100:
                    r, g, b, a = logo_img.split()
                    a = a.point(lambda p: int(p * (logo_opacity / 100.0)))
                    logo_img = Image.merge("RGBA", (r, g, b, a))
                
                # تطبيق الإحداثيات
                paste_x = int((image_width - target_w) * (logo_x_pct / 100.0))
                paste_y = int((image_height - target_h) * (logo_y_pct / 100.0))
                
                img.paste(logo_img, (paste_x, paste_y), logo_img)

            st.session_state['final_image'] = img

        except Exception as e:
            st.error(f"حدث خطأ أثناء المعالجة: {e}")

if 'final_image' in st.session_state:
    st.image(st.session_state['final_image'], caption="معاينة الصورة النهائية", use_column_width=True)

    buf = io.BytesIO()
    st.session_state['final_image'].save(buf, format="PNG")
    byte_im = buf.getvalue()

    st.download_button("📥 تحميل الصورة", data=byte_im, file_name="hadith_pro_bg.png", mime="image/png")
