import streamlit as st
import re
import os
import tempfile
import requests
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Cấu hình trang
st.set_page_config(
    page_title="Tải SGV/SBT NXBGD Miễn Phí",
    page_icon="📚",
    layout="centered"
)

# Giao diện chính
st.markdown("""
    <div style='text-align: center; margin-bottom: 25px;'>
        <h1 style='color: #1e3a8a; margin-bottom: 5px;'>📚 Công Cụ Tải SGV / SBT NXBGD</h1>
        <p style='color: #4b5563; font-size: 16px;'>Dành riêng cho giáo viên - Tải sách chất lượng gốc từ taphuan.nxbgd.vn</p>
    </div>
""", unsafe_allow_html=True)

with st.expander("📖 Hướng dẫn sử dụng cho Thầy/Cô", expanded=False):
    st.markdown("""
    1. Truy cập trang web tập huấn của NXB Giáo Dục: **[taphuan.nxbgd.vn](https://taphuan.nxbgd.vn)**
    2. Chọn cuốn sách muốn đọc (SGV, SBT, Chuyên đề,...).
    3. Sao chép đường link trên thanh địa chỉ (Dạng: `https://taphuan.nxbgd.vn/tap-huan/doc-sach/...`).
    4. Dán link vào ô bên dưới và nhấn **Bắt đầu tải sách**.
    """)

url = st.text_input(
    "🔗 Dán liên kết sách tại đây:",
    placeholder="https://taphuan.nxbgd.vn/tap-huan/doc-sach/sgv-tin-hoc-12.4926897532"
)

def fetch_book_info(book_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(book_url, headers=headers, verify=False, timeout=15)
    if res.status_code != 200:
        return None, None, []
    
    html = res.text
    
    # Tìm tên sách
    title_m = re.search(r'title:\s*["\']([^"\']+)["\']', html)
    if not title_m:
        title_m = re.search(r'<title>(.*?)</title>', html)
    title = title_m.group(1).encode('utf-8').decode('unicode_escape') if title_m else "Sach_NXBGD"
    clean_title = re.sub(r'[\\/:*?"<>|]+', '_', title).strip()

    # Lấy danh sách link ảnh
    urls = re.findall(r'https://taphuan\.nxbgd\.vn/storage/upload/taphuan/[^\s"\'<>]+', html)
    seen = set()
    page_urls = [u for u in urls if not (u in seen or seen.add(u))]

    return clean_title, page_urls

if st.button("🚀 Bắt đầu tải sách", type="primary", use_container_width=True):
    if not url or "taphuan.nxbgd.vn" not in url or "doc-sach" not in url:
        st.error("⚠️ Đường link không hợp lệ! Vui lòng nhập link dạng: https://taphuan.nxbgd.vn/tap-huan/doc-sach/...")
    else:
        info_placeholder = st.empty()
        progress_bar = st.progress(0)
        status_text = st.empty()

        info_placeholder.info("🔍 Đang kết nối tới máy chủ NXBGD để lấy thông tin sách...")

        try:
            title, page_urls = fetch_book_info(url)
            if not page_urls:
                info_placeholder.error("❌ Không tìm thấy dữ liệu ảnh của cuốn sách này. Vui lòng kiểm tra lại link!")
            else:
                total_pages = len(page_urls)
                info_placeholder.success(f"📖 **Sách:** {title} | **Tổng số:** {total_pages} trang")

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

                # Tải đa luồng 10 trang cùng lúc
                with ThreadPoolExecutor(max_workers=10) as executor:
                    for idx, img in executor.map(download_single_page, enumerate(page_urls)):
                        images[idx] = img
                        completed += 1
                        pct = int((completed / total_pages) * 100)
                        progress_bar.progress(pct)
                        status_text.markdown(f"📥 Đang tải trang: **{completed}/{total_pages}** ({pct}%)")

                status_text.markdown("⚙️ Đang đóng gói file PDF chất lượng cao, vui lòng đợi giây lát...")
                valid_images = [img for img in images if img is not None]

                if not valid_images:
                    st.error("❌ Không tải được hình ảnh trang sách.")
                else:
                    # Xuất PDF vào bộ nhớ tạm
                    pdf_buffer = BytesIO()
                    valid_images[0].save(
                        pdf_buffer,
                        format="PDF",
                        save_all=True,
                        append_images=valid_images[1:],
                        quality=95
                    )
                    pdf_buffer.seek(0)

                    status_text.empty()
                    st.balloons()
                    st.success("🎉 **Đã xử lý xong toàn bộ sách!**")

                    st.download_button(
                        label=f"📥 Tải xuống file PDF ({title}.pdf)",
                        data=pdf_buffer,
                        file_name=f"{title}.pdf",
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True
                    )

        except Exception as e:
            st.error(f"❌ Có lỗi xảy ra trong quá trình xử lý: {str(e)}")

st.markdown("---")
st.caption("Ứng dụng hỗ trợ cộng đồng giáo viên Việt Nam • vietTeach")
