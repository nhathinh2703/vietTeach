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

# Hàm render HTML an toàn, loại bỏ thụt lề để tránh lỗi Markdown code block
def render_html(html_str):
    cleaned = "\n".join(line.strip() for line in html_str.strip().splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)

# ==========================================
# 1. ĐỌC DỮ LIỆU TỪ CONFIG.XML
# ==========================================
def load_config(xml_path="config.xml"):
    config = {
        "master_name": "vietApps",
        "app_name": "vietTeach",
        "badge": "FREE",
        "tagline": "Hệ sinh thái ứng dụng miễn phí phục vụ cộng đồng",
        "app_title": "Tiện ích giáo dục và tải sách giáo viên",
        "app_desc": "Hỗ trợ giáo viên tải trọn bộ sách giáo viên, sách bài tập và chuyên đề từ taphuan.nxbgd.vn hoàn toàn miễn phí.",
        "copyright": "© 2026 vietApps – Hệ sinh thái ứng dụng miễn phí",
        "support_email": "hotro@vietapps.vn",
        "connect_message": "Kết nối với chúng tôi để xem hướng dẫn và sử dụng các tiện ích miễn phí",
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
            config["tagline"] = brand.findtext("tagline", config["tagline"])
            config["app_title"] = brand.findtext("appTitle", config["app_title"])
            config["app_desc"] = brand.findtext("appDescription", config["app_desc"])
            config["copyright"] = brand.findtext("copyright", config["copyright"])
            config["support_email"] = brand.findtext("supportEmail", config["support_email"])
            config["connect_message"] = brand.findtext("connectMessage", config["connect_message"])

        eco = root.find("ecosystem")
        if eco is not None:
            for item in eco.findall("app"):
                config["ecosystem"].append({
                    "id": item.get("id", ""),
                    "name": item.findtext("name", ""),
                    "badge": item.findtext("badge", ""),
                    "badge_color": item.findtext("badgeColor", "#2563eb"),
                    "tagline": item.findtext("tagline", ""),
                    "description": item.findtext("description", ""),
                    "url": item.findtext("url", "#"),
                    "icon": item.findtext("icon", "📦")
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
                    "desc": stp.findtext("desc", ""),
                    "example": stp.findtext("example", "")
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
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS với cỡ chữ to rõ ràng, chuẩn viFix
render_html("""
<style>
    /* Ẩn bớt thanh menu mặc định của Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Khung rộng 1200px chuẩn viFix */
    .block-container {
        max-width: 1220px !important;
        padding-top: 1rem !important;
        padding-bottom: 0.8rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 0.7rem !important;
    }

    /* NAVBAR */
    .vt-nav-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 20px;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        margin-bottom: 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .vt-brand-left {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .vt-brand-icon {
        width: 38px;
        height: 38px;
        border-radius: 11px;
        background: linear-gradient(135deg, #2563eb, #4f46e5);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 19px;
        box-shadow: 0 3px 8px rgba(37, 99, 235, 0.25);
    }
    .vt-brand-title {
        font-size: 22px;
        font-weight: 900;
        background: linear-gradient(90deg, #2563eb, #4f46e5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.4px;
    }
    .vt-brand-badge {
        font-size: 10px;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: 12px;
        background: #dbeafe;
        color: #1d4ed8;
        margin-left: 6px;
    }
    .vt-nav-tagline {
        font-size: 13px;
        color: #64748b;
        font-weight: 500;
    }

    /* CỘT TRÁI: TIÊU ĐỀ & HƯỚNG DẪN */
    .vt-hero-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 9999px;
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        color: #1d4ed8;
        font-size: 12.5px;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .vt-hero-h1 {
        font-size: 28px;
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
        font-size: 14.5px;
        color: #475569;
        line-height: 1.5;
        margin-bottom: 14px;
    }

    /* KHUNG 3 BƯỚC HƯỚNG DẪN */
    .vt-steps-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 14px 16px;
        margin-bottom: 16px;
    }
    .vt-step-row {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 8px 0;
    }
    .vt-step-row:not(:last-child) {
        border-bottom: 1px dashed #e2e8f0;
    }
    .vt-num-badge {
        width: 24px;
        height: 24px;
        border-radius: 7px;
        background: #2563eb;
        color: white;
        font-size: 12px;
        font-weight: 800;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        margin-top: 1px;
    }
    .vt-step-content {
        font-size: 13.5px;
        color: #334155;
        line-height: 1.5;
    }
    .vt-step-example {
        font-size: 12px;
        color: #0284c7;
        background: #f0f9ff;
        padding: 3px 8px;
        border-radius: 6px;
        margin-top: 4px;
        display: inline-block;
        word-break: break-all;
        border: 1px solid #e0f2fe;
    }

    /* CỘT PHẢI: CARD TẢI SÁCH */
    .vt-card-header {
        font-size: 17px;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    div[data-testid="stTextInput"] label {
        font-size: 13.5px !important;
        font-weight: 700 !important;
        color: #334155 !important;
        margin-bottom: 3px !important;
    }
    div[data-testid="stTextInput"] input {
        border-radius: 11px !important;
        border: 1px solid #cbd5e1 !important;
        font-size: 14px !important;
        padding: 10px 14px !important;
        background: #f8fafc !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #2563eb !important;
        background: #ffffff !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
    }
    div[data-testid="stButton"] button {
        border-radius: 12px !important;
        background: #2563eb !important;
        color: white !important;
        font-weight: 800 !important;
        font-size: 15px !important;
        padding: 11px 20px !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.22) !important;
        border: none !important;
    }
    div[data-testid="stButton"] button:hover {
        background: #1d4ed8 !important;
    }

    /* DANH MỤC ỨNG DỤNG KHÁC (VIFIX CARD) */
    .vt-eco-wrapper {
        margin-top: 16px;
        border-top: 1px solid #e2e8f0;
        padding-top: 14px;
    }
    .vt-eco-heading {
        font-size: 14px;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 8px;
    }
    .vt-app-item-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 12px 16px;
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 14px;
        text-decoration: none !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .vt-app-item-left {
        flex: 1;
    }
    .vt-app-item-title {
        font-size: 14px;
        font-weight: 800;
        color: #0f172a;
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 4px;
    }
    .vt-app-item-badge {
        font-size: 10px;
        font-weight: 800;
        padding: 2px 7px;
        border-radius: 6px;
        color: white;
    }
    .vt-app-item-desc {
        font-size: 12.5px;
        color: #64748b;
        line-height: 1.45;
    }
    .vt-app-item-btn {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 6px 12px;
        border-radius: 9px;
        background: #eff6ff;
        color: #2563eb !important;
        font-size: 12px;
        font-weight: 700;
        border: 1px solid #bfdbfe;
        white-space: nowrap;
        text-decoration: none !important;
        margin-top: 4px;
    }
    .vt-app-item-btn:hover {
        background: #dbeafe;
    }

    /* FOOTER */
    .vt-bottom-footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 18px;
        padding-top: 14px;
        border-top: 1px solid #e2e8f0;
    }
    .vt-socials-group {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
    }
    .vt-connect-label {
        font-size: 13px;
        font-weight: 700;
        color: #475569;
        margin-right: 4px;
    }
    .vt-social-badge {
        display: inline-flex;
        align-items: center;
        padding: 5px 12px;
        border-radius: 20px;
        color: #ffffff !important;
        font-size: 12px;
        font-weight: 600;
        text-decoration: none !important;
    }
    .vt-footer-copy {
        font-size: 12px;
        color: #94a3b8;
    }
</style>
""")

# ==========================================
# 3. TOP NAVBAR (ĐÃ BỎ LINK VIFIX VÀ VERSION)
# ==========================================
render_html(f"""
<div class="vt-nav-bar">
    <div class="vt-brand-left">
        <div class="vt-brand-icon">📚</div>
        <div>
            <span class="vt-brand-title">{CFG['app_name']}</span>
            <span class="vt-brand-badge">{CFG['badge']}</span>
        </div>
    </div>
    <div class="vt-nav-tagline">
        Hệ sinh thái ứng dụng miễn phí {CFG['master_name']}
    </div>
</div>
""")

# ==========================================
# 4. CHIA 2 CỘT (VỪA VẶN 1 MÀN HÌNH KHÔNG CUỘN)
# ==========================================
col_left, col_right = st.columns([1.15, 1], gap="large")

with col_left:
    render_html(f"""
    <div class="vt-hero-pill">✨ {CFG['tagline']}</div>
    <h1 class="vt-hero-h1">
        Tiện ích giáo dục <br>
        <span class="vt-gradient-clip">và tải sách giáo viên</span>
    </h1>
    <p class="vt-hero-p">{CFG['app_desc']}</p>
    """)

    # 3 Bước hướng dẫn hiển thị trực tiếp (kèm link và ví dụ)
    steps_html = []
    for stp in CFG["guide_steps"]:
        ex_html = f"<div class='vt-step-example'>{stp['example']}</div>" if stp.get("example") else ""
        steps_html.append(f"""
        <div class="vt-step-row">
            <div class="vt-num-badge">{stp['number']}</div>
            <div class="vt-step-content">
                <b>{stp['title']}:</b> {stp['desc']}
                {ex_html}
            </div>
        </div>
        """)

    render_html(f"""
    <div class="vt-steps-box">
        <div style="font-size: 13.5px; font-weight: 800; color: #0f172a; margin-bottom: 6px;">
            📌 Hướng dẫn sử dụng:
        </div>
        {''.join(steps_html)}
    </div>
    """)

with col_right:
    render_html("""
    <div class="vt-card-header">
        <span>⚡ Tải sách giáo viên / sách bài tập</span>
    </div>
    """)

    url = st.text_input(
        "Nhập liên kết từ taphuan.nxbgd.vn:",
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
# 5. GIỚI THIỆU ỨNG DỤNG KHÁC (CHỈ HIỂN THỊ VIFIX KÈM MÔ TẢ)
# ==========================================
eco_cards_html = []
for app in CFG["ecosystem"]:
    card_html = f"""
    <div class="vt-app-item-card">
        <div class="vt-app-item-left">
            <div class="vt-app-item-title">
                <span>{app['icon']}</span>
                <span>{app['name']}</span>
                <span class="vt-app-item-badge" style="background-color: {app['badge_color']};">{app['badge']}</span>
                <span style="font-size:12.5px;color:#64748b;font-weight:600;">– {app['tagline']}</span>
            </div>
            <div class="vt-app-item-desc">{app['description']}</div>
        </div>
        <a href="{app['url']}" target="_blank" class="vt-app-item-btn">
            Bắt đầu sử dụng ↗
        </a>
    </div>
    """
    eco_cards_html.append(card_html)

render_html(f"""
<div class="vt-eco-wrapper">
    <div class="vt-eco-heading">
        <span>🌐 Ứng dụng khác trong hệ sinh thái {CFG['master_name']}:</span>
    </div>
    {''.join(eco_cards_html)}
</div>
""")

# ==========================================
# 6. FOOTER KẾT NỐI MẠNG XÃ HỘI
# ==========================================
social_pills = []
for s in CFG["socials"]:
    pill = f"""<a href="{s['url']}" target="_blank" class="vt-social-badge" style="background-color: {s['color']};">
        <span>{s['name']}</span>
    </a>"""
    social_pills.append(pill)

render_html(f"""
<div class="vt-bottom-footer">
    <div class="vt-socials-group">
        <span class="vt-connect-label">💬 {CFG['connect_message']}:</span>
        {''.join(social_pills)}
    </div>
    <div class="vt-footer-copy">
        {CFG['copyright']} • {CFG['support_email']}
    </div>
</div>
""")
