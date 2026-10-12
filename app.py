import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import glob
import re

# ================= إعدادات الصفحة =================
st.set_page_config(page_title="صانع صور الأحاديث", page_icon="📜", layout="wide")

st.title("صانع صور الأحاديث النبوية 📜")
st.write("أدخل النص واضغط توليد. يمكنك بعد ذلك تعديل الإعدادات وستُطبق مباشرة دون التأثر بتغييرك للنص حتى تضغط توليد مجدداً.")

# ================= تهيئة الجلسة والحالة =================
def init_session_state():
    defaults = {
        "text_input": "",
        "confirmed_text": "",
        "bg_color": "#E4D2B1",
        "frame_color": "#54391F",
        "intro_text_color": "#821107",
        "hadith_text_color": "#151515",
        "grade_text_color": "#54391F",
        "intro_bg_color": "#F0E6D2",
        "hadith_bg_color": "#E8E8E8",
        "grade_bg_color": "#F0E6D2",
        "image_generated": False,
        "uploader_key": 0 # مُعرف لتفريغ الملفات المرفوعة
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session_state()

# دوال الأزرار
def generate_action():
    if st.session_state.text_input.strip():
        st.session_state.confirmed_text = st.session_state.text_input
        st.session_state.image_generated = True

def clear_text():
    st.session_state.text_input = ""

def reset_app():
    st.session_state.text_input = ""
    st.session_state.confirmed_text = ""
    st.session_state.bg_color = "#E4D2B1"
    st.session_state.frame_color = "#54391F"
    st.session_state.intro_text_color = "#821107"
    st.session_state.hadith_text_color = "#151515"
    st.session_state.grade_text_color = "#54391F"
    st.session_state.intro_bg_color = "#F0E6D2"
    st.session_state.hadith_bg_color = "#E8E8E8"
    st.session_state.grade_bg_color = "#F0E6D2"
    st.session_state.image_generated = False
    st.session_state.uploader_key += 1

# ================= التحقق من دعم Raqm =================
try:
    HAS_RAQM = ImageFont.core.HAVE_RAQM
except AttributeError:
    HAS_RAQM = False

if not HAS_RAQM:
    st.warning("⚠️ مكتبة Pillow الحالية لا تدعم محرك Raqm. للحصول على تشكيل مثالي أضف `libraqm-dev` إلى packages.txt.")

# ================= البحث عن الخطوط =================
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

st.sidebar.subheader("2. صورة الخلفية (المرفوعة)")
bg_image_file = st.sidebar.file_uploader("رفع صورة خلفية:", type=["png", "jpg", "jpeg"], key=f"bg_{st.session_state.uploader_key}")
bg_scale_mode = "ملء الشاشة (Cover)"
custom_scale = 100
bg_opacity = 100
if bg_image_file:
    bg_opacity = st.sidebar.slider("شفافية صورة الخلفية (%):", 10, 100, 100)
    bg_scale_mode = st.sidebar.selectbox("طريقة عرض الخلفية:", ["ملء الشاشة (Cover)", "تمديد (Stretch)", "تخصيص الحجم (Custom)"])
    if bg_scale_mode == "تخصيص الحجم (Custom)":
        custom_scale = st.sidebar.slider("نسبة التكبير/التصغير:", 10, 200, 100)

st.sidebar.subheader("3. الإطار العام (جديد)")
st.sidebar.color_picker("لون خلفية الصورة العام:", key="bg_color")
show_frame = st.sidebar.checkbox("إضافة إطار عام للصورة", value=True)
frame_style = "بسيط"
frame_thickness = 5
if show_frame:
    frame_style = st.sidebar.selectbox("شكل الإطار:", ["بسيط", "مزدوج", "زوايا هندسية", "إسلامي كلاسيكي"])
    frame_thickness = st.sidebar.slider("سمك الإطار:", 1, 30, 5)
    st.sidebar.color_picker("لون الإطار:", key="frame_color")

st.sidebar.subheader("4. محاذاة وأحجام النصوص")
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

st.sidebar.subheader("5. ألوان الخطوط")
st.sidebar.color_picker("لون نص السند:", key="intro_text_color")
st.sidebar.color_picker("لون نص الحديث:", key="hadith_text_color")
st.sidebar.color_picker("لون التخريج:", key="grade_text_color")

st.sidebar.subheader("6. أشرطة (تظليل) خلف النصوص")
show_text_bg = st.sidebar.checkbox("تفعيل تظليل ملون خلف النصوص", value=False)
if show_text_bg:
    st.sidebar.color_picker("لون تظليل السند:", key="intro_bg_color")
    st.sidebar.color_picker("لون تظليل الحديث:", key="hadith_bg_color")
    st.sidebar.color_picker("لون تظليل التخريج:", key="grade_bg_color")

st.sidebar.subheader("7. المسافات بين الأقسام")
gap_intro_hadith = st.sidebar.slider("المسافة بين السند والحديث:", 0, 200, 60)
gap_hadith_grade = st.sidebar.slider("المسافة بين الحديث والتخريج:", 0, 200, 60)
selected_font_file = st.sidebar.selectbox("نوع الخط:", available_fonts, index=default_font_index) if available_fonts else None

st.sidebar.subheader("8. الشعار (اللوغو)")
logo_file = st.sidebar.file_uploader("رفع الشعار (PNG أو JPG):", type=["png", "jpg", "jpeg"], key=f"logo_{st.session_state.uploader_key}")
if logo_file:
    logo_size_pct = st.sidebar.slider("حجم الشعار (%)", min_value=5, max_value=100, value=20)
    logo_opacity = st.sidebar.slider("شفافية الشعار (%)", min_value=10, max_value=100, value=100)
    st.sidebar.write("**موضع الشعار:**")
    logo_x_pct = st.sidebar.slider("المحور الأفقي", 0, 100, 50, label_visibility="collapsed")
    logo_y_pct = st.sidebar.slider("المحور العمودي", 0, 100, 90, label_visibility="collapsed")
    
    try:
        preview_logo = Image.open(logo_file)
        aspect = preview_logo.height / preview_logo.width
        map_w = 200
        map_h = int(map_w * (image_height / image_width))
        minimap = Image.new('RGB', (map_w, map_h), color="#ECECEC")
        draw_map = ImageDraw.Draw(minimap)
        draw_map.rectangle([(0,0), (map_w-1, map_h-1)], outline="#B0B0B0", width=2)
        logo_map_w = max(5, int(map_w * (logo_size_pct / 100.0)))
        logo_map_h = max(5, int(logo_map_w * aspect))
        map_x = int((map_w - logo_map_w) * (logo_x_pct / 100.0))
        map_y = int((map_h - logo_map_h) * (logo_y_pct / 100.0))
        draw_map.rectangle([(map_x, map_y), (map_x + logo_map_w, map_y + logo_map_h)], fill="#FF4B4B", outline="#990000")
        st.sidebar.image(minimap, caption="موقع اللوغو (المربع الأحمر)")
    except Exception:
        pass

# ================= واجهة الإدخال =================
col_btn1, col_btn2, col_btn3 = st.columns(3)
with col_btn1:
    st.button("✨ توليد الصورة", on_click=generate_action, type="primary", use_container_width=True)
with col_btn2:
    st.button("🗑️ تفريغ النص", on_click=clear_text, use_container_width=True)
with col_btn3:
    st.button("🔄 إنشاء جديد", on_click=reset_app, use_container_width=True)

st.text_area(
    "أدخل النص هنا:",
    key="text_input",
    height=200,
    placeholder="الصق نص الحديث هنا...\nيجب ترك سطر فارغ (اضغط Enter مرتين) للفصل بين السند، والحديث، والتخريج."
)

if not st.session_state.image_generated:
    st.info("💡 اكتب النص واضغط (توليد الصورة). التعديلات الجانبية ستُطبق تلقائياً بعد التوليد الأول.")

# ================= أدوات ومعالجات النص =================
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

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)
    except Exception:
        return ImageFont.truetype(path, size)

def wrap_text(text, font, max_width):
    if not text.strip(): return ""
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
    if not text: return 0
    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing, direction="rtl", language="ar")
    return bbox[3]

# ================= توليد الصورة =================
# نعتمد هنا على "confirmed_text" لكي لا يتأثر التحديث الآلي بالتلاعب بمربع النص
if st.session_state.image_generated and st.session_state.confirmed_text.strip() and selected_font_file:
    try:
        intro_part, hadith_part, grade_part = parse_text_manual(st.session_state.confirmed_text)
        img = Image.new('RGB', (image_width, image_height), color=st.session_state.bg_color)

        # دمج صورة الخلفية المرفوعة بـ Opacity
        if bg_image_file:
            bg_pil = Image.open(bg_image_file).convert("RGBA")
            if bg_scale_mode == "تمديد (Stretch)":
                bg_pil = bg_pil.resize((image_width, image_height))
                paste_pos = (0, 0)
            elif bg_scale_mode == "ملء الشاشة (Cover)":
                bg_ratio = bg_pil.width / bg_pil.height
                img_ratio = image_width / image_height
                if bg_ratio > img_ratio:
                    new_w = int(image_height * bg_ratio)
                    bg_pil = bg_pil.resize((new_w, image_height))
