import os, time, subprocess, re, sys, json

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
VERSION = "2.3.4"
PKG_VNG = "com.roblox.client.vnggames"
PKG_GLOBAL = "com.roblox.client"
UPDATE_REPO = "WolfaterVN/ToolRJ"
UPDATE_BRANCH = "main"
UPDATE_FILE = "autorejoin.py"
UPDATE_URLS = [
    f"https://raw.githubusercontent.com/{UPDATE_REPO}/refs/heads/{UPDATE_BRANCH}/{UPDATE_FILE}",
    f"https://raw.githubusercontent.com/{UPDATE_REPO}/{UPDATE_BRANCH}/{UPDATE_FILE}"
]

# Bảng màu
R, G, Y, B, W = '\033[1;31m', '\033[1;32m', '\033[1;33m', '\033[1;34m', '\033[1;37m'
ROOT_AVAILABLE = None
ROOT_WARNED = False

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

def has_root_access():
    global ROOT_AVAILABLE
    if ROOT_AVAILABLE is not None:
        return ROOT_AVAILABLE

    su_path = sh("command -v su 2>/dev/null")
    if not su_path:
        ROOT_AVAILABLE = False
        return ROOT_AVAILABLE

    ROOT_AVAILABLE = sh("su -c 'id -u 2>/dev/null'") == "0"
    return ROOT_AVAILABLE

def run_android_cmd(command, require_root=False, quiet=False):
    global ROOT_WARNED

    if has_root_access():
        return os.system(f"su -c '{command}'")

    if require_root:
        if not quiet and not ROOT_WARNED:
            print(f"{R}[!] Thiết bị chưa có quyền root/su. Một số chức năng sẽ bị giới hạn.{W}")
            ROOT_WARNED = True
        return 1

    return os.system(command)

# --- CONFIG MANAGEMENT ---
CONFIG_FILE = os.path.join(os.path.dirname(__file__) or ".", "autorejoin_config.json")

def load_config():
    """Tải cấu hình từ file JSON"""
    if not os.path.exists(CONFIG_FILE):
        return {"package": "", "account_id": "", "private_link": ""}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"package": "", "account_id": "", "private_link": ""}

def save_config(config):
    """Lưu cấu hình vào file JSON"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"{R}[!] Lỗi lưu config: {e}{W}")
        return False

def delete_config():
    """Xóa file cấu hình"""
    if os.path.exists(CONFIG_FILE):
        try:
            os.remove(CONFIG_FILE)
            print(f"{G}[✓] Đã xóa config!{W}")
            time.sleep(1)
            return True
        except Exception as e:
            print(f"{R}[!] Không thể xóa config: {e}{W}")
            time.sleep(1)
            return False
    return False

def is_numeric_account_id(value):
    return str(value).isdigit() and len(str(value)) >= 6

def get_installed_roblox_packages():
    candidates = [PKG_VNG, PKG_GLOBAL]
    installed_raw = sh("pm list packages 2>/dev/null")
    return [p for p in candidates if f"package:{p}" in installed_raw]

def select_package_manual(saved_package=""):
    installed = get_installed_roblox_packages()
    
    if saved_package and saved_package in installed:
        default_pkg = saved_package
    else:
        default_pkg = PKG_VNG if PKG_VNG in installed else PKG_GLOBAL

    while True:
        os.system('clear')
        print(f"{B}==========================================")
        print(f"{G}           CHỌN ROBLOX PACKAGE            ")
        print(f"{B}==========================================")
        print(f"{W} [1] {G}{PKG_VNG}")
        print(f"{W} [2] {G}{PKG_GLOBAL}")
        if saved_package:
            print(f"{W} [Enter] {Y}Giữ: {default_pkg}")
        else:
            print(f"{W} [Enter] {Y}Mặc định: {default_pkg}")
        print(f"{B}==========================================")

        pick = input(f"{Y}Chọn package: {W}").strip()
        if pick == "1":
            selected = PKG_VNG
        elif pick == "2":
            selected = PKG_GLOBAL
        elif pick == "":
            selected = default_pkg
        else:
            print(f"{R}[!] Lựa chọn không hợp lệ.{W}")
            time.sleep(1)
            continue

        if installed and selected not in installed:
            print(f"{R}[!] {selected} chưa cài trên máy. Vui lòng chọn lại.{W}")
            time.sleep(1.2)
            continue

        return selected

def input_account_id(default_value=""):
    while True:
        prompt = f"{Y}Nhập Account ID"
        if default_value:
            prompt += f" (Enter để giữ {default_value})"
        prompt += f": {W}"

        value = input(prompt).strip()
        if not value and default_value:
            return default_value
        if value.isdigit() and len(value) >= 6:
            return value

        print(f"{R}[!] Account ID không hợp lệ (chỉ số, tối thiểu 6 ký tự).{W}")
        time.sleep(1)

def get_auto_package():
    """Tự động nhận diện package Roblox phù hợp trên máy"""
    candidates = [PKG_VNG, PKG_GLOBAL]
    installed_raw = sh("pm list packages 2>/dev/null")
    installed = [p for p in candidates if (f"package:{p}" in installed_raw or p in installed_raw)]

    if not installed:
        return PKG_GLOBAL

    if PKG_VNG in installed and PKG_GLOBAL in installed:
        vng_id = get_auto_id(PKG_VNG)
        global_id = get_auto_id(PKG_GLOBAL)
        vng_ok = is_numeric_account_id(vng_id)
        global_ok = is_numeric_account_id(global_id)

        if vng_ok and not global_ok:
            return PKG_VNG
        if global_ok and not vng_ok:
            return PKG_GLOBAL

        for pkg in [PKG_VNG, PKG_GLOBAL]:
            if sh(f"pidof {pkg} 2>/dev/null"):
                return pkg

        return PKG_VNG

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

def check_internet():
    """Kiểm tra kết nối internet"""
    try:
        r = requests.head("https://github.com", timeout=5, verify=False)
        return r.status_code < 500
    except:
        return False

def auto_update(show_latest_msg=False, check_online=False):
    if check_online:
        print(f"{Y}[*] Kiểm tra kết nối mạng...{W}")
        if not check_internet():
            print(f"{R}[!] Không có kết nối internet. Bỏ qua auto update.{W}")
            time.sleep(1)
            return False
        print(f"{G}[✓] Kết nối mạng OK!{W}")

    print(f"{Y}[*] Đang kiểm tra phiên bản mới...{W}")
    try:
        response = None
        source_url = None
        for url in UPDATE_URLS:
            try:
                print(f"{Y}[*] Đang tải từ: {B}{url}{W}")
            except: pass
            r = requests.get(url, timeout=10, verify=False)
            if r.status_code == 200:
                response = r
                source_url = url
                print(f"{G}[✓] Kết nối thành công!{W}")
                break

        if response is not None:
            remote_ver = extract_remote_version(response.text)
            print(f"{Y}[*] Phiên bản remote: {B}{remote_ver}{W}")
            print(f"{Y}[*] Phiên bản hiện tại: {B}{VERSION}{W}")
            if not remote_ver:
                print(f"{R}[!] Không đọc được VERSION từ server.{W}")
                return False

            if is_newer_version(remote_ver, VERSION):
                print(f"{G}[+] Tìm thấy bản {remote_ver} mới hơn. Đang tự động cập nhật...{W}")
                tmp_file = __file__ + ".new"
                backup_file = __file__ + ".bak"

                print(f"{Y}[*] Ghi file tạm: {tmp_file}{W}")
                with open(tmp_file, "w", encoding="utf-8") as f:
                    f.write(response.text)

                print(f"{Y}[*] Backup file cũ: {backup_file}{W}")
                if os.path.exists(backup_file):
                    os.remove(backup_file)
                os.replace(__file__, backup_file)
                os.replace(tmp_file, __file__)
                print(f"{G}[✓] File cập nhật xong!{W}")

                print(f"{G}[✔] Cập nhật hoàn tất! Khởi động lại...{W}")
                time.sleep(1.5)
                try:
                    import subprocess
                    subprocess.Popen([sys.executable] + sys.argv)
                    print(f"{G}[*] Nhấn Enter để tiếp tục...{W}")
                    sys.exit(0)
                except Exception as restart_err:
                    print(f"{Y}[!] Không thể auto-restart: {restart_err}{W}")
                    print(f"{G}[✓] Vui lòng chạy lại script để sử dụng phiên bản mới!{W}")
                    time.sleep(2)
                    sys.exit(0)
                return True
            elif show_latest_msg:
                print(f"{G}[✓] Bạn đang ở phiên bản mới nhất ({VERSION}).{W}")
                return True
        else:
            print(f"{R}[!] Không thể tải bản cập nhật từ mọi URL đã cấu hình.{W}")
    except Exception as e:
        print(f"{R}[!] Lỗi cập nhật: {e}{W}")
        import traceback
        traceback.print_exc()
    return False

def launch_game(pkg, link=None):
    run_android_cmd(f"am force-stop {pkg}", require_root=True, quiet=True)
    time.sleep(1)
    if link:
        run_android_cmd(f"am start -a android.intent.action.VIEW -d \"{link}\" {pkg}")
    else:
        run_android_cmd(f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1 > /dev/null 2>&1")

def start_monitor(pkg, account_id, link=None):
    os.system('clear')
    print(f"{G}>>> TRẠNG THÁI: ĐANG TREO GAME <<<")
    print(f"{W}Account ID: {Y}{account_id}")
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
    # 1. Tự động kiểm tra+ cập nhật khi vừa mở
    auto_update(check_online=True)
    
    # 2. Kiểm tra trạng thái online
    is_online = check_internet()

    # 3. Tải config lưu từ lần trước
    saved_config = load_config()
    current_pkg = saved_config.get("package", "")
    current_id = saved_config.get("account_id", "")
    current_link = saved_config.get("private_link", "")

    # 4. Tự động chọn package + ID nếu config đầy đủ
    if current_pkg and current_id:
        # Config đầy đủ, dùng ngay không hỏi
        print(f"{G}[✓] Đã load config: Package={Y}{current_pkg}{G}, ID={Y}{current_id}{W}")
        time.sleep(1)
    else:
        # Config thiếu, hỏi/nhập
        if not current_pkg:
            current_pkg = select_package_manual(saved_package=current_pkg)
        
        os.system('clear')
        if current_id:
            print(f"{Y}ID cũ: {current_id} (Enter để giữ, hoặc nhập ID mới){W}")
        current_id = input_account_id(default_value=current_id)

    # 5. Lưu config
    config = {"package": current_pkg, "account_id": current_id, "private_link": current_link}
    save_config(config)
    
    while True:
        os.system('clear')
        
        print(f"{B}==========================================")
        print(f"{G}    DELTA ULTIMATE HUB - AUTO SYSTEM      ")
        status_label = f"{G}Rooted" if has_root_access() else f"{Y}No Root"
        online_label = f"{G}Online" if is_online else f"{R}Offline"
        print(f"{W}    Version: {Y}{VERSION} {B}| {W}Status: {status_label}{B} | {W}Net: {online_label}")
        print(f"{B}==========================================")
        print(f"{W} >> Package Đã Chọn: {Y}{current_pkg}")
        print(f"{W} >> Account ID Nhập: {G}{current_id}")
        print(f"{B}==========================================")
        print(f"{W} [1] {G}Auto Rejoin (Public Server)")
        print(f"{W} [2] {G}Auto Rejoin (Private Link)")
        print(f"{W} [3] {B}Dọn RAM & Tối ưu UgPhone")
        print(f"{W} [4] {Y}Kiểm tra cập nhật thủ công")
        print(f"{W} [5] {B}Đổi Package")
        print(f"{W} [6] {B}Đổi Account ID")
        print(f"{W} [7] {Y}Reset Config")
        print(f"{W} [8] {R}Thoát")
        print(f"{B}==========================================")
        
        choice = input(f"{Y}Chọn số: {W}")
        
        if choice == '1':
            start_monitor(current_pkg, current_id)
        elif choice == '2':
            url = input(f"{Y}Dán link Private: {W}")
            if url:
                current_link = url
                config["private_link"] = current_link
                save_config(config)
            start_monitor(current_pkg, current_id, url)
        elif choice == '3':
            if has_root_access():
                run_android_cmd("sync && echo 3 > /proc/sys/vm/drop_caches", require_root=True)
                print(f"{G}Đã tối ưu RAM!{W}")
            else:
                print(f"{Y}[!] Cần root để dọn RAM nâng cao.{W}")
            time.sleep(1)
        elif choice == '4':
            is_online = check_internet()
            if not is_online:
                print(f"{R}[!] Không có kết nối internet!{W}")
                time.sleep(1.5)
            else:
                auto_update(show_latest_msg=True)
            time.sleep(1)
        elif choice == '5':
            current_pkg = select_package_manual(saved_package=current_pkg)
            config["package"] = current_pkg
            save_config(config)
        elif choice == '6':
            current_id = input_account_id(default_value=current_id)
            config["account_id"] = current_id
            save_config(config)
        elif choice == '7':
            print(f"{R}[!] Bạn chắc chắn muốn xóa config? (y/n){W}")
            if input().strip().lower() == 'y':
                delete_config()
                current_pkg = ""
                current_id = ""
                current_link = ""
        elif choice == '8':
            sys.exit()

if __name__ == "__main__":
    main()