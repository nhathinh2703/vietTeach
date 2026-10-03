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
# 1. ĐỌC DỮ LIỆU TỪ CONFIG.XML
# ==========================================
def load_config(xml_path="config.xml"):
    config = {
        "master_name": "vietApps",
        "app_name": "viTeach",
        "badge": "FREE",
        "version": "v1.0.2",
        "tagline": "Hệ sinh thái ứng dụng miễn phí",
        "app_title": "Tiện ích Giáo dục & Tải Sách NXBGD",
        "app_desc": "Tải trọn bộ Sách Giáo Viên, Sách Bài Tập và Chuyên đề từ taphuan.nxbgd.vn chất lượng gốc.",
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

        eco = root.find("ecosystem")
        if eco is not None:
            for item in eco.findall("app"):
                config["ecosystem"].append({
                    "id": item.get("id", ""),
                    "name": item.findtext("name", ""),
                    "badge": item.findtext("badge", ""),
                    "tagline": item.findtext("tagline", ""),
                    "url": item.findtext("url", "#")
                })

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
# 2. CẤU HÌNH TRANG (LAYOUT WIDE - KHÔNG CUỘN)
# ==========================================
st.set_page_config(
    page_title=f"{CFG['app_name']} – {CFG['app_title']}",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Tối ưu CSS gọn gàng, chuẩn phong cách viFix, vừa vặn 1 màn hình
st.markdown("""
<style>
    /* Ẩn các thanh mặc định của Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Container mở rộng thoáng đãng, padding gọn gàng */
    .block-container {
        max-width: 1200px !important;
        padding-top: 1rem !important;
        padding-bottom: 0.8rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }

    /* Giảm khoảng cách thừa giữa các widget của Streamlit */
    div[data-testid="stVerticalBlock"] {
        gap: 0.6rem !important;
    }

    /* NAVBAR GỌN GÀNG */
    .vt-nav-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 18px;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        margin-bottom: 18px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .vt-brand-left {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .vt-brand-icon {
        width: 32px;
        height: 32px;
        border-radius: 10px;
        background: linear-gradient(135deg, #2563eb, #4f46e5);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 16px;
        box-shadow: 0 3px 8px rgba(37, 99, 235, 0.25);
    }
    .vt-brand-title {
        font-size: 19px;
        font-weight: 900;
        background: linear-gradient(90deg, #2563eb, #4f46e5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.4px;
    }
    .vt-brand-badge {
        font-size: 9px;
        font-weight: 800;
        padding: 2px 7px;
        border-radius: 12px;
        background: #dbeafe;
        color: #1d4ed8;
        margin-left: 6px;
    }
    .vt-nav-right {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .vt-btn-link {
        font-size: 11.5px;
        font-weight: 700;
        color: #2563eb;
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        padding: 4px 10px;
        border-radius: 9px;
        text-decoration: none !important;
        transition: all 0.15s ease;
    }
    .vt-btn-link:hover {
        background: #dbeafe;
    }
    .vt-ver-badge {
        font-family: ui-monospace, monospace;
        font-size: 11px;
        font-weight: 700;
        color: #475569;
        background: #f1f5f9;
        padding: 4px 10px;
        border-radius: 9px;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    .vt-pulse {
        width: 6px;
        height: 6px;
        background: #3b82f6;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
    }

    /* CỘT TRÁI: THÔNG TIN & HƯỚNG DẪN */
    .vt-hero-pill {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 3px 11px;
        border-radius: 9999px;
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        color: #1d4ed8;
        font-size: 11px;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .vt-hero-h1 {
        font-size: 27px;
        font-weight: 900;
        color: #0f172a;
        line-height: 1.25;
        letter-spacing: -0.5px;
        margin: 0 0 8px 0;
    }
    .vt-gradient-clip {
        background: linear-gradient(90deg, #2563eb, #4f46e5, #0891b2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .vt-hero-p {
        font-size: 13px;
        color: #64748b;
        line-height: 1.5;
        margin-bottom: 14px;
    }

    /* THẺ HƯỚNG DẪN 3 BƯỚC GỌN GÀNG */
    .vt-steps-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 12px 14px;
        margin-bottom: 14px;
    }
    .vt-step-row {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 6px 0;
    }
    .vt-step-row:not(:last-child) {
        border-bottom: 1px dashed #e2e8f0;
    }
    .vt-num-badge {
        width: 20px;
        height: 20px;
        border-radius: 6px;
        background: #2563eb;
        color: white;
        font-size: 10.5px;
        font-weight: 800;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        margin-top: 2px;
    }
    .vt-step-content {
        font-size: 12px;
        color: #334155;
        line-height: 1.45;
    }

    /* MINI ECOSYSTEM LINKS */
    .vt-eco-pills {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 6px;
        font-size: 11.5px;
    }
    .vt-eco-tag {
        color: #64748b;
        font-weight: 600;
        margin-right: 4px;
    }
    .vt-app-chip {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 3px 9px;
        border-radius: 8px;
        background: #ffffff;
        border: 1px solid #cbd5e1;
        color: #1e293b !important;
        text-decoration: none !important;
        font-weight: 600;
        font-size: 11px;
        transition: all 0.15s ease;
    }
    .vt-app-chip:hover {
        border-color: #2563eb;
        color: #2563eb !important;
    }

    /* CỘT PHẢI: CARD TẢI SÁCH */
    .vt-card-right {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 20px 22px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
    }
    .vt-card-header {
        font-size: 15px;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 7px;
    }

    /* Custom Input & Button */
    div[data-testid="stTextInput"] label {
        font-size: 12px !important;
        font-weight: 700 !important;
        color: #475569 !important;
        margin-bottom: 2px !important;
    }
    div[data-testid="stTextInput"] input {
        border-radius: 10px !important;
        border: 1px solid #cbd5e1 !important;
        font-size: 12.5px !important;
        padding: 9px 12px !important;
        background: #f8fafc !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #2563eb !important;
        background: #ffffff !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
    }
    div[data-testid="stButton"] button {
        border-radius: 11px !important;
        background: #2563eb !important;
        color: white !important;
        font-weight: 800 !important;
        font-size: 13.5px !important;
        padding: 10px 18px !important;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.22) !important;
        border: none !important;
        margin-top: 4px !important;
    }
    div[data-testid="stButton"] button:hover {
        background: #1d4ed8 !important;
    }

    /* FOOTER TRÊN 1 DÒNG GỌN GÀNG */
    .vt-bottom-footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 18px;
        padding-top: 12px;
        border-top: 1px solid #e2e8f0;
    }
    .vt-socials-group {
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .vt-social-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: 20px;
        color: #ffffff !important;
        font-size: 11px;
        font-weight: 600;
        text-decoration: none !important;
        transition: opacity 0.15s;
    }
    .vt-social-badge:hover {
        opacity: 0.88;
    }
    .vt-footer-copy {
        font-size: 11px;
        color: #94a3b8;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. TOP NAVBAR
# ==========================================
st.markdown(f"""
<div class="vt-nav-bar">
    <div class="vt-brand-left">
        <div class="vt-brand-icon">📚</div>
        <div>
            <span class="vt-brand-title">{CFG['app_name']}</span>
            <span class="vt-brand-badge">{CFG['badge']}</span>
        </div>
    </div>
    <div class="vt-nav-right">
        <a href="https://vifix.vercel.app/" target="_blank" class="vt-btn-link">🔧 viFix Web</a>
        <div class="vt-ver-badge">
            <span class="vt-pulse"></span>
            <span>{CFG['version']}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 4. CHIA 2 CỘT RESPONSIVE (VỪA VẶN 1 MÀN HÌNH)
# ==========================================
col_left, col_right = st.columns([1.1, 1], gap="large")

with col_left:
    st.markdown(f"""
    <div class="vt-hero-pill">✨ {CFG['tagline']}</div>
    <h1 class="vt-hero-h1">
        Tiện ích Giáo dục <br>
        <span class="vt-gradient-clip">và Tải Sách NXBGD</span>
    </h1>
    <p class="vt-hero-p">{CFG['app_desc']}</p>
    """, unsafe_allow_html=True)

    # 3 Bước hướng dẫn hiển thị trực tiếp (không xổ xuống)
    steps_html = []
    for stp in CFG["guide_steps"]:
        steps_html.append(f"""
        <div class="vt-step-row">
            <div class="vt-num-badge">{stp['number']}</div>
            <div class="vt-step-content"><b>{stp['title']}:</b> {stp['desc']}</div>
        </div>
        """)

    st.markdown(f"""
    <div class="vt-steps-box">
        <div style="font-size: 12px; font-weight: 800; color: #0f172a; margin-bottom: 6px;">
            📌 Hướng dẫn sử dụng nhanh:
        </div>
        {''.join(steps_html)}
    </div>
    """, unsafe_allow_html=True)

    # Hệ sinh thái mini
    eco_chips = []
    for app in CFG["ecosystem"]:
        chip = f"""<a href="{app['url']}" target="_blank" class="vt-app-chip">
            <span>{app['name']}</span>
            <span style="font-size: 9px; color: #64748b;">({app['badge']})</span>
        </a>"""
        eco_chips.append(chip)

    st.markdown(f"""
    <div class="vt-eco-pills">
        <span class="vt-eco-tag">🌐 Hệ sinh thái {CFG['master_name']}:</span>
        {''.join(eco_chips)}
    </div>
    """, unsafe_allow_html=True)

with col_right:
    st.markdown("""
    <div class="vt-card-header">
        <span>⚡ Tải Sách Giáo Viên / Sách Bài Tập</span>
    </div>
    """, unsafe_allow_html=True)

    url = st.text_input(
        "Nhập link từ taphuan.nxbgd.vn:",
        placeholder="https://taphuan.nxbgd.vn/tap-huan/doc-sach/sgv-tin-hoc-12.4926897532"
    )

    btn_download = st.button("🚀 Bắt đầu tải sách PDF", type="primary", use_container_width=True)

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

    if btn_download:
        if not url or "taphuan.nxbgd.vn" not in url or "doc-sach" not in url:
            st.error("⚠️ Link chưa đúng định dạng: https://taphuan.nxbgd.vn/tap-huan/doc-sach/...")
        else:
            info_box = st.empty()
            progress_bar = st.progress(0)
            status_text = st.empty()

            info_box.info("🔍 Đang kết nối máy chủ để kiểm tra tài liệu...")

            try:
                title, page_urls = fetch_book_info(url)
                if not page_urls:
                    info_box.error("❌ Không tìm thấy các trang sách. Vui lòng kiểm tra lại link!")
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

                    status_text.markdown("⚙️ Đang đóng gói file PDF chất lượng gốc...")
                    valid_images = [img for img in images if img is not None]

                    if not valid_images:
                        st.error("❌ Không thể nạp trang ảnh sách.")
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
                        st.success("🎉 **Đã đóng gói PDF thành công!**")

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
# 5. FOOTER GỌN GÀNG (1 DÒNG - KHÔNG CUỘN)
# ==========================================
social_pills = []
for s in CFG["socials"]:
    pill = f"""<a href="{s['url']}" target="_blank" class="vt-social-badge" style="background-color: {s['color']};">
        <span>{s['name']}</span>
    </a>"""
    social_pills.append(pill)

st.markdown(f"""
<div class="vt-bottom-footer">
    <div class="vt-socials-group">
        <span style="font-size: 11px; font-weight: 700; color: #64748b; margin-right: 4px;">Kết nối:</span>
        {''.join(social_pills)}
    </div>
    <div class="vt-footer-copy">
        {CFG['copyright']} • {CFG['support_email']}
    </div>
</div>
""", unsafe_allow_html=True)
