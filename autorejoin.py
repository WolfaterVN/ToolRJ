import os
import time
import subprocess
import re
import sys
import requests

# --- Cấu hình Version & URL ---
VERSION = "1.5"
# Thay link này bằng link RAW code của bạn trên GitHub/Pastebin
UPDATE_URL = "https://raw.githubusercontent.com/user/repo/main/autorejoin.py"

# --- Bảng màu ---
R, G, Y, B, W = '\033[1;31m', '\033[1;32m', '\033[1;33m', '\033[1;34m', '\033[1;37m'

def clear():
    os.system('clear')

def auto_update():
    """Kiểm tra và tự động cập nhật script"""
    print(f"{Y}[*] Đang kiểm tra cập nhật...{W}")
    try:
        # Lấy nội dung code mới từ server
        response = requests.get(UPDATE_URL, timeout=5)
        if response.status_code == 200:
            # Tìm version trong code mới
            new_version = re.search(r'VERSION = "([\d.]+)"', response.text).group(1)
            if new_version != VERSION:
                print(f"{G}[+] Đã tìm thấy bản mới: {new_version} (Bản hiện tại: {VERSION})")
                print(f"{Y}[!] Đang tải và cài đặt...{W}")
                
                # Ghi đè file hiện tại
                script_path = os.path.abspath(__file__)
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(response.text)
                
                print(f"{G}[✔] Cập nhật thành công! Đang khởi động lại...{W}")
                time.sleep(2)
                # Khởi động lại script
                os.execv(sys.executable, ['python'] + sys.argv)
            else:
                print(f"{G}[✔] Bạn đang sử dụng phiên bản mới nhất ({VERSION}).")
        else:
            print(f"{R}[!] Không thể kết nối máy chủ cập nhật.")
    except Exception as e:
        print(f"{R}[!] Lỗi cập nhật: {e}")
    time.sleep(1.5)

def get_package():
    for p in ["com.vng.roblox", "com.roblox.client"]:
        check = subprocess.getoutput(f"pm list packages {p}")
        if p in check: return p
    return "com.roblox.client"

def get_roblox_id(pkg):
    try:
        cmd = f"su -c \"grep -hroP '(?<=UserID\" value=\")\\d+' /data/data/{pkg}/shared_prefs/ || grep -hroP '(?<=browserTrackerId\">)\\d+' /data/data/{pkg}/shared_prefs/\""
        result = subprocess.getoutput(cmd).split('\n')[0]
        if result and result.isdigit(): return result
        return "Chưa đăng nhập"
    except: return "Lỗi Root/Data"

def is_running(pkg):
    return len(subprocess.getoutput(f"pidof {pkg}")) > 0

def launch(pkg, link=None):
    os.system(f"su -c 'am force-stop {pkg}'")
    time.sleep(1)
    if link:
        os.system(f"su -c 'am start -a android.intent.action.VIEW -d \"{link}\" {pkg}'")
    else:
        os.system(f"su -c 'monkey -p {pkg} -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1'")

def auto_loop(pkg, link=None):
    clear()
    print(f"{G}>>> ĐANG GIÁM SÁT GAME (V{VERSION}) <<<")
    print(f"{W}Package: {Y}{pkg}")
    print(f"{R}Nhấn Ctrl+C để thoát về Hub")
    while True:
        try:
            if not is_running(pkg):
                print(f"{R}[!] Game văng! {G}Rejoin...")
                launch(pkg, link)
                time.sleep(15)
            time.sleep(3)
        except KeyboardInterrupt: break

# --- GIAO DIỆN CHÍNH ---
clear()
auto_update() # Tự động chạy khi mở tool
current_pkg = get_package()

while True:
    clear()
    current_id = get_roblox_id(current_pkg)
    print(f"{B}==========================================")
    print(f"{G}    DELTA ULTIMATE HUB - AUTO UPDATE      ")
    print(f"{W}    Version: {Y}{VERSION} {B}| {W}Status: {G}Rooted")
    print(f"{B}==========================================")
    print(f"{W} [1] Package: {Y}{current_pkg}")
    print(f"{W} [2] UserID:  {G}{current_id} {W}(Auto Scan)")
    print(f"{W} [3] BẮT ĐẦU AUTO REJOIN {B}(Public)")
    print(f"{W} [4] BẮT ĐẦU AUTO REJOIN {B}(Private)")
    print(f"{W} [5] Dọn RAM & Optimize UgPhone")
    print(f"{W} [6] Kiểm tra cập nhật thủ công")
    print(f"{W} [7] Thoát")
    print(f"{B}==========================================")

    choice = input(f"{Y}Chọn số: {W}")

    if choice == '1':
        print(f"\n1. Global | 2. VNG")
        c = input("Chọn: ")
        current_pkg = "com.vng.roblox" if c == '2' else "com.roblox.client"
    elif choice == '3':
        auto_loop(current_pkg)
    elif choice == '4':
        url = input(f"{Y}Dán link Private: {W}")
        auto_loop(current_pkg, url)
    elif choice == '5':
        os.system("su -c 'sync && echo 3 > /proc/sys/vm/drop_caches'")
        print(f"{G}Tối ưu thành công!")
        time.sleep(1)
    elif choice == '6':
        auto_update()
    elif choice == '7':
        sys.exit()