import sys
import re
import os
import requests
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def download_book(url, output_path=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print(f"[*] Đang tải dữ liệu trang: {url}")
    res = requests.get(url, headers=headers, verify=False)
    if res.status_code != 200:
        print(f"[!] Lỗi kết nối: HTTP {res.status_code}")
        return

    html = res.text

    # Tìm tiêu đề sách
    title_m = re.search(r'title:\s*["\']([^"\']+)["\']', html)
    if not title_m:
        title_m = re.search(r'<title>(.*?)</title>', html)
    title = title_m.group(1).encode('utf-8').decode('unicode_escape') if title_m else "Sach_NXBGD"
    clean_title = re.sub(r'[\\/:*?"<>|]+', '_', title).strip()

    if not output_path:
        output_path = f"{clean_title}.pdf"

    # Lấy toàn bộ URL ảnh trang sách
    urls = re.findall(r'https://taphuan\.nxbgd\.vn/storage/upload/taphuan/[^\s"\'<>]+', html)
    seen = set()
    page_urls = [u for u in urls if not (u in seen or seen.add(u))]

    if not page_urls:
        print("[!] Không tìm thấy dữ liệu trang sách nào.")
        return

    total = len(page_urls)
    print(f"[*] Tên sách: {clean_title}")
    print(f"[*] Tìm thấy {total} trang. Bắt đầu tải đa luồng...")

    def fetch_img(item):
        idx, img_url = item
        for _ in range(3):
            try:
                r = requests.get(img_url, headers=headers, timeout=15, verify=False)
                if r.status_code == 200:
                    img = Image.open(BytesIO(r.content)).convert("RGB")
                    return idx, img
            except Exception:
                pass
        return idx, None

    images = [None] * total
    completed = 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        for idx, img in executor.map(fetch_img, enumerate(page_urls)):
            images[idx] = img
            completed += 1
            percent = int((completed / total) * 100)
            sys.stdout.write(f"\r[*] Tiến độ tải: {completed}/{total} trang ({percent}%)")
            sys.stdout.flush()

    print("\n[*] Đang đóng gói thành file PDF...")
    valid_images = [img for img in images if img is not None]
    if not valid_images:
        print("[!] Không tải được trang sách nào.")
        return

    valid_images[0].save(
        output_path,
        save_all=True,
        append_images=valid_images[1:],
        quality=95
    )

    abs_path = os.path.abspath(output_path)
    print(f"[+] Xong! File PDF đã được lưu tại:\n    {abs_path}")
    return abs_path

if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://taphuan.nxbgd.vn/tap-huan/doc-sach/sgv-tin-hoc-12.4926897532"
    download_book(target_url)
