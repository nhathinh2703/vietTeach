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
# 1. ĐỌC CẤU HÌNH TỪ FILE CONFIG.XML
# ==========================================
def load_config(xml_path="config.xml"):
    config = {
        "brand_name": "vietTeach",
        "tagline": "Hệ sinh thái tiện ích hỗ trợ Giáo viên Việt Nam",
        "copyright": "© 2026 vietTeach. Tất cả các quyền được bảo lưu.",
        "support_email": "contact@vietteach.edu.vn",
        "socials": [],
        "donate": {"enabled": False}
    }
    if not os.path.exists(xml_path):
        return config

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # App Info
        app_info = root.find("appInfo")
        if app_info is not None:
            config["brand_name"] = app_info.findtext("brandName", config["brand_name"])
            config["tagline"] = app_info.findtext("tagline", config["tagline"])
            config["copyright"] = app_info.findtext("copyright", config["copyright"])
            config["support_email"] = app_info.findtext("supportEmail", config["support_email"])

        # Socials
        socials_node = root.find("socials")
        if socials_node is not None:
            for s in socials_node.findall("social"):
                is_enabled = s.findtext("enabled", "false").strip().lower() == "true"
                if is_enabled:
                    config["socials"].append({
                        "id": s.get("id", ""),
                        "name": s.findtext("name", ""),
                        "url": s.findtext("url", "#"),
                        "color": s.findtext("color", "#2563eb")
                    })

        # Monetization (Donate)
        donate_node = root.find("monetization/donate")
        if donate_node is not None:
            is_donate_on = donate_node.get("enabled", "false").strip().lower() == "true"
            config["donate"] = {
                "enabled": is_donate_on,
                "message": donate_node.findtext("message", "Ủng hộ duy trì hệ thống"),
                "bank_name": donate_node.findtext("bankName", ""),
                "account_number": donate_node.findtext("accountNumber", ""),
                "account_holder": donate_node.findtext("accountHolder", ""),
                "qr_image": donate_node.findtext("qrImage", "")
            }

    except Exception as e:
        print(f"Lỗi đọc config.xml: {e}")

    return config

CFG = load_config()

# ==========================================
# 2. CẤU HÌNH TRANG WEB STREAMLIT
# ==========================================
st.set_page_config(
    page_title=f"{CFG['brand_name']} - Tiện Ích Giáo Viên",
    page_icon="🎓",
    layout="centered"
)

# Custom CSS cho giao diện chuyên nghiệp và gọn gàng
st.markdown("""
<style>
    /* Ẩn bớt footer mặc định của Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Styling Header */
    .vt-header {
        text-align: center;
        padding: 20px 0 15px 0;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 25px;
    }
    .vt-logo {
        font-size: 32px;
        font-weight: 800;
        color: #1e3a8a;
        letter-spacing: -0.5px;
        margin: 0;
    }
    .vt-tagline {
        font-size: 14px;
        color: #64748b;
        margin-top: 4px;
    }

    /* Menu các ứng dụng */
    .vt-nav {
        display: flex;
        justify-content: center;
        gap: 12px;
        margin-top: 15px;
    }
    .vt-nav-item-active {
        background-color: #eff6ff;
        color: #1d4ed8;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        border: 1px solid #bfdbfe;
    }
    .vt-nav-item-upcoming {
        background-color: #f8fafc;
        color: #94a3b8;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 13px;
        border: 1px dashed #cbd5e1;
    }

    /* Footer Styling */
    .vt-footer {
        margin-top: 45px;
        padding: 25px 0 15px 0;
        border-top: 1px solid #e2e8f0;
        text-align: center;
    }
    .vt-social-links {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 16px;
    }
    .vt-social-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 8px;
        color: #ffffff !important;
        text-decoration: none !important;
        font-size: 13px;
        font-weight: 500;
        transition: transform 0.15s ease, opacity 0.15s ease;
    }
    .vt-social-btn:hover {
        opacity: 0.9;
        transform: translateY(-2px);
    }
    .vt-copyright {
        font-size: 12px;
        color: #94a3b8;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HEADER GIAO DIỆN CHÍNH
# ==========================================
st.markdown(f"""
<div class="vt-header">
    <h1 class="vt-logo">🎓 {CFG['brand_name']}</h1>
    <div class="vt-tagline">{CFG['tagline']}</div>
    <div class="vt-nav">
        <span class="vt-nav-item-active">📚 Tải SGV / SBT NXBGD</span>
        <span class="vt-nav-item-upcoming">🤖 Soạn đề & bài giảng AI (Sắp ra mắt)</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 4. CHỨC NĂNG TẢI SÁCH
# ==========================================
with st.expander("💡 Hướng dẫn nhanh cho Thầy/Cô", expanded=False):
    st.markdown("""
    1. Truy cập trang đọc sách: **[taphuan.nxbgd.vn](https://taphuan.nxbgd.vn)**
    2. Tìm cuốn sách muốn tải (Sách giáo viên, Sách bài tập, Chuyên đề,...).
    3. Sao chép đường link trên thanh địa chỉ (Dạng: `https://taphuan.nxbgd.vn/tap-huan/doc-sach/...`).
    4. Dán vào ô bên dưới và bấm nút **Bắt đầu tải**.
    """)

url = st.text_input(
    "🔗 Liên kết sách cần tải:",
    placeholder="https://taphuan.nxbgd.vn/tap-huan/doc-sach/sgv-tin-hoc-12.4926897532"
)

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

if st.button("🚀 Bắt đầu tải sách", type="primary", use_container_width=True):
    if not url or "taphuan.nxbgd.vn" not in url or "doc-sach" not in url:
        st.error("⚠️ Đường link chưa đúng định dạng. Vui lòng nhập link sách từ taphuan.nxbgd.vn")
    else:
        info_box = st.empty()
        progress_bar = st.progress(0)
        status_text = st.empty()

        info_box.info("🔍 Đang kết nối lấy dữ liệu sách...")

        try:
            title, page_urls = fetch_book_info(url)
            if not page_urls:
                info_box.error("❌ Không tìm thấy các trang sách. Vui lòng kiểm tra lại link!")
            else:
                total_pages = len(page_urls)
                info_box.success(f"📖 **{title}** (Tổng cộng: **{total_pages} trang**)")

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

                # Tải đa luồng 6 trang để giữ máy chủ ổn định
                with ThreadPoolExecutor(max_workers=6) as executor:
                    for idx, img in executor.map(download_single_page, enumerate(page_urls)):
                        images[idx] = img
                        completed += 1
                        pct = int((completed / total_pages) * 100)
                        progress_bar.progress(pct)
                        status_text.markdown(f"📥 Đang tải: **{completed}/{total_pages}** trang ({pct}%)")

                status_text.markdown("⚙️ Đang đóng gói file PDF chất lượng cao...")
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
                    st.success("🎉 **Đã hoàn tất đóng gói file PDF!**")

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
# 5. KHU VỰC MONETIZATION (DONATE NẾU BẬT)
# ==========================================
if CFG["donate"]["enabled"]:
    st.markdown("---")
    donate = CFG["donate"]
    st.markdown(f"""
    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px; text-align: center;">
        <h4 style="color: #1e293b; margin-bottom: 8px;">☕ {donate['message']}</h4>
        <p style="color: #64748b; font-size: 14px; margin-bottom: 12px;">Ngân hàng: <b>{donate['bank_name']}</b> | STK: <b>{donate['account_number']}</b> ({donate['account_holder']})</p>
    </div>
    """, unsafe_allow_html=True)
    if donate.get("qr_image"):
        st.image(donate["qr_image"], width=200)

# ==========================================
# 6. FOOTER CHUYÊN NGHIỆP (TỰ ĐỘNG TỪ XML)
# ==========================================
social_html_list = []
for s in CFG["socials"]:
    btn_html = f"""<a href="{s['url']}" target="_blank" class="vt-social-btn" style="background-color: {s['color']};">
        <span>{s['name']}</span>
    </a>"""
    social_html_list.append(btn_html)

socials_joined = "\n".join(social_html_list)

st.markdown(f"""
<div class="vt-footer">
    <div style="font-size: 13px; color: #64748b; margin-bottom: 12px; font-weight: 600;">
        KẾT NỐI VỚI CỘNG ĐỒNG {CFG['brand_name'].upper()}
    </div>
    <div class="vt-social-links">
        {socials_joined}
    </div>
    <div class="vt-copyright">
        {CFG['copyright']} • Hỗ trợ: <a href="mailto:{CFG['support_email']}" style="color: #64748b; text-decoration: none;">{CFG['support_email']}</a>
    </div>
</div>
""", unsafe_allow_html=True)
