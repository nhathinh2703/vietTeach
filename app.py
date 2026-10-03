import streamlit as st
import re
import os
import requests
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import urllib3
import xml.etree.ElementTree as ET

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 1. ĐỌC DỮ LIỆU ĐỘNG TỪ FILE CONFIG.XML
# ==========================================
def load_config(xml_path="config.xml"):
    config = {
        "master_name": "vietApps",
        "app_name": "viTeach",
        "badge": "FREE",
        "version": "v1.0.2",
        "tagline": "Hệ sinh thái ứng dụng miễn phí",
        "app_title": "Tiện ích Giáo dục & Tải Sách NXBGD",
        "app_desc": "Tải trọn bộ Sách Giáo Viên, Sách Bài Tập từ taphuan.nxbgd.vn chất lượng gốc.",
        "copyright": "© 2026 vietApps – Hệ sinh thái ứng dụng miễn phí",
        "support_email": "hotro@vietapps.vn",
        "ecosystem": [],
        "socials": [],
        "guide_steps": []
    }
    if not os.path.exists(xml_path):
        return config

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Brand
        brand = root.find("brand")
        if brand is not None:
            config["master_name"] = brand.findtext("masterName", config["master_name"])
            config["app_name"] = brand.findtext("appName", config["app_name"])
            config["badge"] = brand.findtext("badge", config["badge"])
            config["version"] = brand.findtext("version", config["version"])
            config["tagline"] = brand.findtext("tagline", config["tagline"])
            config["app_title"] = brand.findtext("appTitle", config["app_title"])
            config["app_desc"] = brand.findtext("appDescription", config["app_desc"])
            config["copyright"] = brand.findtext("copyright", config["copyright"])
            config["support_email"] = brand.findtext("supportEmail", config["support_email"])

        # Ecosystem
        eco = root.find("ecosystem")
        if eco is not None:
            for item in eco.findall("app"):
                config["ecosystem"].append({
                    "id": item.get("id", ""),
                    "name": item.findtext("name", ""),
                    "badge": item.findtext("badge", ""),
                    "tagline": item.findtext("tagline", ""),
                    "url": item.findtext("url", "#"),
                    "icon": item.findtext("icon", "grid")
                })

        # Socials
        socials_node = root.find("socials")
        if socials_node is not None:
            for s in socials_node.findall("social"):
                if s.findtext("enabled", "false").strip().lower() == "true":
                    config["socials"].append({
                        "id": s.get("id", ""),
                        "name": s.findtext("name", ""),
                        "url": s.findtext("url", "#"),
                        "color": s.findtext("color", "#2563eb")
                    })

        # Guide Steps
        guide = root.find("guideSteps")
        if guide is not None:
            for stp in guide.findall("step"):
                config["guide_steps"].append({
                    "number": stp.findtext("number", "•"),
                    "title": stp.findtext("title", ""),
                    "desc": stp.findtext("desc", "")
                })

    except Exception as e:
        print(f"Lỗi đọc config.xml: {e}")

    return config

CFG = load_config()

# ==========================================
# 2. CẤU HÌNH TRANG STREAMLIT
# ==========================================
st.set_page_config(
    page_title=f"{CFG['app_name']} – {CFG['app_title']}",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS phong cách đồng bộ viFix (Tailwind / Modern SaaS style)
st.markdown("""
<style>
    /* Ẩn các thành phần mặc định của Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 800px;
    }

    /* Phông chữ & Nền chung */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    /* NAVBAR ĐỒNG BỘ VIFIX */
    .vt-navbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 18px;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        margin-bottom: 24px;
    }
    .vt-brand-group {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .vt-brand-icon {
        width: 36px;
        height: 36px;
        border-radius: 11px;
        background: linear-gradient(135deg, #2563eb, #4f46e5);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 18px;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.25);
    }
    .vt-brand-text {
        font-size: 20px;
        font-weight: 900;
        background: linear-gradient(90deg, #2563eb, #4f46e5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
    }
    .vt-badge-pro {
        font-size: 9px;
        font-weight: 800;
        letter-spacing: 0.5px;
        padding: 2px 7px;
        border-radius: 20px;
        background: #dbeafe;
        color: #1d4ed8;
        margin-left: 6px;
        vertical-align: middle;
    }
    .vt-nav-tools {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .vt-version-tag {
        font-family: ui-monospace, monospace;
        font-size: 11px;
        font-weight: 700;
        color: #475569;
        background: #f1f5f9;
        padding: 4px 10px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .vt-pulse-dot {
        width: 7px;
        height: 7px;
        background: #3b82f6;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
    }
    .vt-eco-btn {
        font-size: 11px;
        font-weight: 700;
        color: #2563eb;
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        padding: 4px 10px;
        border-radius: 10px;
        text-decoration: none;
        transition: all 0.2s;
    }
    .vt-eco-btn:hover {
        background: #dbeafe;
    }

    /* HERO SECTION */
    .vt-hero {
        text-align: center;
        margin-bottom: 24px;
    }
    .vt-pill-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 14px;
        border-radius: 9999px;
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        color: #1d4ed8;
        font-size: 12px;
        font-weight: 700;
        margin-bottom: 12px;
    }
    .vt-title {
        font-size: 32px;
        font-weight: 900;
        color: #0f172a;
        line-height: 1.2;
        letter-spacing: -0.8px;
        margin-bottom: 10px;
    }
    .vt-gradient-text {
        background: linear-gradient(90deg, #2563eb, #4f46e5, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .vt-desc {
        font-size: 14px;
        color: #64748b;
        font-weight: 500;
        max-width: 580px;
        margin: 0 auto;
        line-height: 1.5;
    }

    /* 3 BƯỚC HƯỚNG DẪN HIỂN THỊ LUÔN (RESPONSIVE) */
    .vt-guide-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-bottom: 24px;
    }
    @media (max-width: 640px) {
        .vt-guide-container {
            grid-template-columns: 1fr;
            gap: 10px;
        }
    }
    .vt-step-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 14px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .vt-step-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 6px;
    }
    .vt-step-number {
        width: 22px;
        height: 22px;
        border-radius: 6px;
        background: #2563eb;
        color: white;
        font-size: 11px;
        font-weight: 800;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .vt-step-title {
        font-size: 13px;
        font-weight: 800;
        color: #0f172a;
    }
    .vt-step-desc {
        font-size: 11.5px;
        color: #64748b;
        line-height: 1.45;
    }

    /* FORM CARD KHUNG NHẬP */
    .vt-main-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 24px;
        padding: 22px 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01);
        margin-bottom: 28px;
    }

    /* Tùy chỉnh input & button Streamlit cho đồng bộ */
    div[data-testid="stTextInput"] label {
        font-size: 12px !important;
        font-weight: 700 !important;
        color: #334155 !important;
    }
    div[data-testid="stTextInput"] input {
        border-radius: 12px !important;
        border: 1px solid #cbd5e1 !important;
        font-size: 13px !important;
        padding: 10px 14px !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
    }
    div[data-testid="stButton"] button {
        border-radius: 12px !important;
        background: #2563eb !important;
        color: white !important;
        font-weight: 800 !important;
        font-size: 14px !important;
        padding: 12px 20px !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
        transition: all 0.2s ease !important;
        border: none !important;
    }
    div[data-testid="stButton"] button:hover {
        background: #1d4ed8 !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.35) !important;
    }

    /* HỆ SINH THÁI VIETAPPS CARDS */
    .vt-eco-section {
        margin-top: 32px;
        border-top: 1px solid #e2e8f0;
        padding-top: 24px;
    }
    .vt-eco-title {
        font-size: 14px;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .vt-eco-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
    }
    @media (max-width: 640px) {
        .vt-eco-grid {
            grid-template-columns: 1fr;
        }
    }
    .vt-eco-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 12px 14px;
        text-decoration: none !important;
        display: block;
        transition: all 0.2s ease;
    }
    .vt-eco-card:hover {
        background: #ffffff;
        border-color: #93c5fd;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transform: translateY(-2px);
    }
    .vt-eco-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 4px;
    }
    .vt-eco-app-name {
        font-size: 13px;
        font-weight: 800;
        color: #0f172a;
    }
    .vt-eco-badge {
        font-size: 9px;
        font-weight: 800;
        padding: 1px 6px;
        border-radius: 6px;
        background: #e2e8f0;
        color: #475569;
    }
    .vt-eco-badge-active {
        background: #dbeafe;
        color: #1d4ed8;
    }
    .vt-eco-app-desc {
        font-size: 11px;
        color: #64748b;
        line-height: 1.4;
    }

    /* FOOTER ĐỒNG BỘ */
    .vt-footer {
        margin-top: 36px;
        border-top: 1px solid #e2e8f0;
        padding: 20px 0 10px 0;
        text-align: center;
    }
    .vt-socials-container {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 14px;
    }
    .vt-social-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 12px;
        border-radius: 9999px;
        color: white !important;
        font-size: 12px;
        font-weight: 600;
        text-decoration: none !important;
        transition: opacity 0.2s;
    }
    .vt-social-pill:hover {
        opacity: 0.88;
    }
    .vt-footer-text {
        font-size: 11.5px;
        color: #94a3b8;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. RENDER NAVBAR ĐỒNG BỘ VIFIX
# ==========================================
st.markdown(f"""
<div class="vt-navbar">
    <div class="vt-brand-group">
        <div class="vt-brand-icon">📚</div>
        <div>
            <span class="vt-brand-text">{CFG['app_name']}</span>
            <span class="vt-badge-pro">{CFG['badge']}</span>
        </div>
    </div>
    <div class="vt-nav-tools">
        <a href="https://vifix.vercel.app/" target="_blank" class="vt-eco-btn" title="Chuyển sang ứng dụng viFix">🔧 viFix</a>
        <div class="vt-version-tag">
            <span class="vt-pulse-dot"></span>
            <span>{CFG['version']}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 4. RENDER HERO SECTION
# ==========================================
st.markdown(f"""
<div class="vt-hero">
    <div class="vt-pill-badge">
        <span>✨ {CFG['tagline']}</span>
    </div>
    <h1 class="vt-title">
        Tiện ích Giáo dục <br>
        <span class="vt-gradient-text">và Tải Sách NXBGD</span>
    </h1>
    <p class="vt-desc">{CFG['app_desc']}</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 5. RENDER 3 BƯỚC HƯỚNG DẪN (HIỂN THỊ TRỰC QUAN)
# ==========================================
steps_html = []
for stp in CFG["guide_steps"]:
    steps_html.append(f"""
    <div class="vt-step-card">
        <div class="vt-step-header">
            <span class="vt-step-number">{stp['number']}</span>
            <span class="vt-step-title">{stp['title']}</span>
        </div>
        <div class="vt-step-desc">{stp['desc']}</div>
    </div>
    """)

st.markdown(f"""
<div class="vt-guide-container">
    {''.join(steps_html)}
</div>
""", unsafe_allow_html=True)

# ==========================================
# 6. KHUNG CHỨC NĂNG TẢI SÁCH CHÍNH
# ==========================================
def fetch_book_info(book_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(book_url, headers=headers, verify=False, timeout=15)
    if res.status_code != 200:
        return None, []
    
    html = res.text
    title_m = re.search(r'title:\s*["\']([^"\']+)["\']', html)
    if not title_m:
        title_m = re.search(r'<title>(.*?)</title>', html)
    title = title_m.group(1).encode('utf-8').decode('unicode_escape') if title_m else "Sach_NXBGD"
    clean_title = re.sub(r'[\\/:*?"<>|]+', '_', title).strip()

    urls = re.findall(r'https://taphuan\.nxbgd\.vn/storage/upload/taphuan/[^\s"\'<>]+', html)
    seen = set()
    page_urls = [u for u in urls if not (u in seen or seen.add(u))]

    return clean_title, page_urls

url = st.text_input(
    "Liên kết sách cần tải (từ taphuan.nxbgd.vn):",
    placeholder="https://taphuan.nxbgd.vn/tap-huan/doc-sach/sgv-tin-hoc-12.4926897532"
)

if st.button("🚀 Bắt đầu tải sách PDF", type="primary", use_container_width=True):
    if not url or "taphuan.nxbgd.vn" not in url or "doc-sach" not in url:
        st.error("⚠️ Liên kết chưa chính xác! Vui lòng nhập link dạng: https://taphuan.nxbgd.vn/tap-huan/doc-sach/...")
    else:
        info_box = st.empty()
        progress_bar = st.progress(0)
        status_text = st.empty()

        info_box.info("🔍 Đang kết nối máy chủ để kiểm tra tài liệu...")

        try:
            title, page_urls = fetch_book_info(url)
            if not page_urls:
                info_box.error("❌ Không tìm thấy dữ liệu trang sách. Hãy đảm bảo sách mở được trên web!")
            else:
                total_pages = len(page_urls)
                info_box.success(f"📖 **{title}** — Đã tìm thấy **{total_pages} trang**")

                headers = {"User-Agent": "Mozilla/5.0"}

                def download_single_page(item):
                    idx, img_url = item
                    for _ in range(3):
                        try:
                            r = requests.get(img_url, headers=headers, timeout=15, verify=False)
                            if r.status_code == 200:
                                return idx, Image.open(BytesIO(r.content)).convert("RGB")
                        except Exception:
                            pass
                    return idx, None

                images = [None] * total_pages
                completed = 0

                with ThreadPoolExecutor(max_workers=6) as executor:
                    for idx, img in executor.map(download_single_page, enumerate(page_urls)):
                        images[idx] = img
                        completed += 1
                        pct = int((completed / total_pages) * 100)
                        progress_bar.progress(pct)
                        status_text.markdown(f"📥 Tiến độ: **{completed}/{total_pages}** trang ({pct}%)")

                status_text.markdown("⚙️ Đang xuất file PDF chất lượng gốc...")
                valid_images = [img for img in images if img is not None]

                if not valid_images:
                    st.error("❌ Lỗi xử lý hình ảnh.")
                else:
                    pdf_buffer = BytesIO()
                    valid_images[0].save(
                        pdf_buffer,
                        format="PDF",
                        save_all=True,
                        append_images=valid_images[1:],
                        quality=92
                    )
                    pdf_buffer.seek(0)

                    status_text.empty()
                    st.balloons()
                    st.success("🎉 **Hoàn thành đóng gói file PDF!**")

                    st.download_button(
                        label=f"📥 Tải xuống: {title}.pdf",
                        data=pdf_buffer,
                        file_name=f"{title}.pdf",
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True
                    )

        except Exception as e:
            st.error(f"❌ Có lỗi phát sinh: {str(e)}")

# ==========================================
# 7. HỆ SINH THÁI VIETAPPS (ECOSYSTEM CARDS)
# ==========================================
eco_cards_html = []
for app in CFG["ecosystem"]:
    badge_cls = "vt-eco-badge-active" if app["badge"] in ["FREE", "PRO"] else "vt-eco-badge"
    card_html = f"""
    <a href="{app['url']}" target="_blank" class="vt-eco-card">
        <div class="vt-eco-card-header">
            <span class="vt-eco-app-name">{app['name']}</span>
            <span class="{badge_cls}">{app['badge']}</span>
        </div>
        <div class="vt-eco-app-desc">{app['tagline']}</div>
    </a>
    """
    eco_cards_html.append(card_html)

st.markdown(f"""
<div class="vt-eco-section">
    <div class="vt-eco-title">
        <span>🌐 Hệ sinh thái ứng dụng {CFG['master_name']}</span>
    </div>
    <div class="vt-eco-grid">
        {''.join(eco_cards_html)}
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 8. FOOTER VÀ KẾT NỐI MẠNG XÃ HỘI
# ==========================================
social_pills = []
for s in CFG["socials"]:
    pill = f"""<a href="{s['url']}" target="_blank" class="vt-social-pill" style="background-color: {s['color']};">
        <span>{s['name']}</span>
    </a>"""
    social_pills.append(pill)

st.markdown(f"""
<div class="vt-footer">
    <div style="font-size: 12px; font-weight: 700; color: #64748b; margin-bottom: 10px;">
        KẾT NỐI VỚI CỘNG ĐỒNG {CFG['master_name'].upper()}
    </div>
    <div class="vt-socials-container">
        {''.join(social_pills)}
    </div>
    <div class="vt-footer-text">
        {CFG['copyright']} • Email: {CFG['support_email']}
    </div>
</div>
""", unsafe_allow_html=True)
