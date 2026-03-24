import os, time, subprocess, re, sys

# Tự động cài thư viện nếu thiếu
try:
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    os.system('pip install requests urllib3')
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CẤU HÌNH ---
VERSION = "2.0"
UPDATE_URL = "https://raw.githubusercontent.com/WolfaterVN/ToolRJ/refs/heads/main/autorejoin.py"

# Bảng màu
R, G, Y, B, W = '\033[1;31m', '\033[1;32m', '\033[1;33m', '\033[1;34m', '\033[1;37m'

def get_auto_package():
    """Tự động nhận diện bản Roblox đang cài trên máy"""
    pkgs = ["com.vng.roblox", "com.roblox.client"]
    for p in pkgs:
        check = subprocess.getoutput(f"pm list packages {p}")
        if p in check:
            return p
    return "com.roblox.client" # Mặc định nếu không tìm thấy

def get_auto_id(pkg):
    """Quét sâu vào hệ thống để lấy ID ngay lập tức"""
    try:
        # Quét tất cả file .xml trong shared_prefs để tìm UserID
        cmd = f"su -c \"grep -hroP '(?<=UserID\" value=\")\\d+' /data/data/{pkg}/shared_prefs/ 2>/dev/null\""
        res = subprocess.getoutput(cmd).strip().split('\n')[0]
        if res.isdigit() and len(res) > 5:
            return res
        
        # Phương án dự phòng 2: Quét BrowserTracker
        cmd2 = f"su -c \"grep -hroP '(?<=browserTrackerId\">)\\d+' /data/data/{pkg}/shared_prefs/ 2>/dev/null\""
        res2 = subprocess.getoutput(cmd2).strip().split('\n')[0]
        if res2.isdigit(): return res2
            
        return "Chưa đăng nhập"
    except:
        return "Lỗi Root"

def auto_update():
    print(f"{Y}[*] Đang kiểm tra phiên bản mới...{W}")
    try:
        response = requests.get(UPDATE_URL, timeout=10, verify=False)
        if response.status_code == 200:
            remote_ver = re.search(r'VERSION = "([\d.]+)"', response.text).group(1)
            if remote_ver != VERSION:
                print(f"{G}[+] Tìm thấy bản {remote_ver}. Đang tự động cập nhật...{W}")
                with open(__file__, "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f"{G}[✔] Xong! Khởi động lại Hub...{W}")
                time.sleep(1.5)
                os.execv(sys.executable, ['python'] + sys.argv)
    except: pass

def launch_game(pkg, link=None):
    os.system(f"su -c 'am force-stop {pkg}'")
    time.sleep(1)
    if link:
        os.system(f"su -c 'am start -a android.intent.action.VIEW -d \"{link}\" {pkg}'")
    else:
        os.system(f"su -c 'monkey -p {pkg} -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1'")

def start_monitor(pkg, link=None):
    os.system('clear')
    uid = get_auto_id(pkg)
    print(f"{G}>>> TRẠNG THÁI: ĐANG TREO GAME <<<")
    print(f"{W}Account ID: {Y}{uid}")
    print(f"{W}Package   : {B}{pkg}")
    print(f"{R}Nhấn Ctrl+C để dừng và về Menu")
    print(f"{G}------------------------------------")
    
    while True:
        try:
            # Kiểm tra xem Roblox có còn sống (PID) không
            pid = subprocess.getoutput(f"pidof {pkg}")
            if not pid:
                print(f"{R}[{time.strftime('%H:%M:%S')}] Phát hiện văng game! Rejoin ngay...")
                launch_game(pkg, link)
                time.sleep(20) # Đợi game khởi động
            time.sleep(5)
        except KeyboardInterrupt: break

# --- GIAO DIỆN CHÍNH (HUB) ---
def main():
    # 1. Tự động kiểm tra cập nhật khi vừa mở
    auto_update()
    
    while True:
        os.system('clear')
        # 2. Tự động lấy Package và ID ngay tại Menu chính
        current_pkg = get_auto_package()
        current_id = get_auto_id(current_pkg)
        
        print(f"{B}==========================================")
        print(f"{G}    DELTA ULTIMATE HUB - AUTO SYSTEM      ")
        print(f"{W}    Version: {Y}{VERSION} {B}| {W}Status: {G}Rooted")
        print(f"{B}==========================================")
        print(f"{W} >> Package Tự Nhận: {Y}{current_pkg}")
        print(f"{W} >> Account ID Quét: {G}{current_id}")
        print(f"{B}==========================================")
        print(f"{W} [1] {G}Auto Rejoin (Public Server)")
        print(f"{W} [2] {G}Auto Rejoin (Private Link)")
        print(f"{W} [3] {B}Dọn RAM & Tối ưu UgPhone")
        print(f"{W} [4] {Y}Kiểm tra cập nhật thủ công")
        print(f"{W} [5] {R}Thoát")
        print(f"{B}==========================================")
        
        choice = input(f"{Y}Chọn số: {W}")
        
        if choice == '1':
            start_monitor(current_pkg)
        elif choice == '2':
            url = input(f"{Y}Dán link Private: {W}")
            start_monitor(current_pkg, url)
        elif choice == '3':
            os.system("su -c 'sync && echo 3 > /proc/sys/vm/drop_caches'")
            print(f"{G}Đã tối ưu RAM!"); time.sleep(1)
        elif choice == '4':
            auto_update()
        elif choice == '5':
            sys.exit()

if __name__ == "__main__":
    main()