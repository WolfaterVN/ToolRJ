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
VERSION = "2.2"
UPDATE_URL = "https://raw.githubusercontent.com/WolfaterVN/ToolRJ/refs/heads/main/autorejoin.py"

# Bảng màu
R, G, Y, B, W = '\033[1;31m', '\033[1;32m', '\033[1;33m', '\033[1;34m', '\033[1;37m'

def parse_version(value):
    parts = re.findall(r"\d+", str(value))
    return tuple(int(p) for p in parts) if parts else (0,)

def extract_remote_version(content):
    patterns = [
        r'VERSION\s*=\s*"([\d.]+)"',
        r"VERSION\s*=\s*'([\d.]+)'"
    ]
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1)
    return None

def is_newer_version(remote_version, current_version):
    return parse_version(remote_version) > parse_version(current_version)

def sh(command):
    return subprocess.getoutput(command).strip()

def is_numeric_account_id(value):
    return str(value).isdigit() and len(str(value)) >= 6

def get_auto_package():
    """Tự động nhận diện package Roblox phù hợp trên máy"""
    candidates = ["com.vng.roblox", "com.roblox.client"]
    installed_raw = sh("pm list packages 2>/dev/null")
    installed = [p for p in candidates if (f"package:{p}" in installed_raw or p in installed_raw)]

    if not installed:
        return "com.roblox.client"

    if "com.vng.roblox" in installed and "com.roblox.client" in installed:
        vng_id = get_auto_id("com.vng.roblox")
        global_id = get_auto_id("com.roblox.client")
        vng_ok = is_numeric_account_id(vng_id)
        global_ok = is_numeric_account_id(global_id)

        if vng_ok and not global_ok:
            return "com.vng.roblox"
        if global_ok and not vng_ok:
            return "com.roblox.client"

        for pkg in ["com.vng.roblox", "com.roblox.client"]:
            if sh(f"pidof {pkg} 2>/dev/null"):
                return pkg

        return "com.vng.roblox"

    for pkg in installed:
        if sh(f"pidof {pkg} 2>/dev/null"):
            return pkg

    return installed[0]

def get_auto_id(pkg):
    """Quét sâu shared_prefs để lấy Account ID trên máy đã root"""
    try:
        root_ok = sh("su -c 'id -u 2>/dev/null'")
        if root_ok != "0":
            return "Lỗi Root"

        pref_dir = f"/data/data/{pkg}/shared_prefs"
        list_cmd = f"su -c 'find {pref_dir} -maxdepth 1 -type f -name \"*.xml\" 2>/dev/null'"
        xml_files = [line.strip() for line in sh(list_cmd).splitlines() if line.strip()]

        if not xml_files:
            return "Chưa đăng nhập"

        patterns = [
            r'name="UserID"\s+value="(\d{6,})"',
            r'name="UserId"\s+value="(\d{6,})"',
            r'name="userid"\s+value="(\d{6,})"',
            r'name="browserTrackerId"\s+value="(\d{6,})"',
            r'"UserID"\s*:\s*"?(\d{6,})"?',
            r'"userId"\s*:\s*"?(\d{6,})"?'
        ]

        for xml_path in xml_files:
            content = sh(f"su -c 'cat {xml_path} 2>/dev/null'")
            if not content:
                continue

            for pattern in patterns:
                match = re.search(pattern, content, flags=re.IGNORECASE)
                if match:
                    return match.group(1)

        fallback_cmd = (
            f"su -c 'grep -RhoE \"[0-9]{{6,}}\" {pref_dir}/*.xml 2>/dev/null | head -n 1'"
        )
        fallback_id = sh(fallback_cmd)
        if fallback_id.isdigit() and len(fallback_id) >= 6:
            return fallback_id

        return "Chưa đăng nhập"
    except Exception:
        return "Lỗi Root"

def auto_update(show_latest_msg=False):
    print(f"{Y}[*] Đang kiểm tra phiên bản mới...{W}")
    try:
        response = requests.get(UPDATE_URL, timeout=10, verify=False)
        if response.status_code == 200:
            remote_ver = extract_remote_version(response.text)
            if not remote_ver:
                print(f"{R}[!] Không đọc được VERSION từ server.{W}")
                return False

            if is_newer_version(remote_ver, VERSION):
                print(f"{G}[+] Tìm thấy bản {remote_ver}. Đang tự động cập nhật...{W}")
                tmp_file = __file__ + ".new"
                backup_file = __file__ + ".bak"

                with open(tmp_file, "w", encoding="utf-8") as f:
                    f.write(response.text)

                if os.path.exists(backup_file):
                    os.remove(backup_file)
                os.replace(__file__, backup_file)
                os.replace(tmp_file, __file__)

                print(f"{G}[✔] Xong! Khởi động lại Hub...{W}")
                time.sleep(1.5)
                os.execv(sys.executable, [sys.executable] + sys.argv)
                return True
            elif show_latest_msg:
                print(f"{G}[✓] Bạn đang ở phiên bản mới nhất ({VERSION}).{W}")
        else:
            print(f"{R}[!] Không thể tải bản cập nhật (HTTP {response.status_code}).{W}")
    except Exception as e:
        print(f"{R}[!] Lỗi cập nhật: {e}{W}")
    return False

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
            auto_update(show_latest_msg=True)
            time.sleep(1.2)
        elif choice == '5':
            sys.exit()

if __name__ == "__main__":
    main()