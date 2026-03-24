import os, time, subprocess, re, sys

# Kiểm tra và tự cài thư viện nếu thiếu (Fix cho cả máy tính và UgPhone)
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
VERSION = "1.8"
UPDATE_URL = "https://raw.githubusercontent.com/WolfaterVN/ToolRJ/main/autorejoin.py"

R, G, Y, B, W = '\033[1;31m', '\033[1;32m', '\033[1;33m', '\033[1;34m', '\033[1;37m'

def get_roblox_id(pkg):
    """Fix Auto Scan ID: Quét sâu bằng quyền root"""
    try:
        # Lệnh quét trực tiếp vào bộ nhớ xml của Roblox
        cmd = f"su -c \"grep -hroP '(?<=UserID\" value=\")\\d+' /data/data/{pkg}/shared_prefs/ 2>/dev/null\""
        res = subprocess.getoutput(cmd).strip().split('\n')[0]
        if res.isdigit(): return res
        
        # Backup: Quét tracker ID
        cmd2 = f"su -c \"grep -hroP '(?<=browserTrackerId\">)\\d+' /data/data/{pkg}/shared_prefs/ 2>/dev/null\""
        res2 = subprocess.getoutput(cmd2).strip().split('\n')[0]
        return res2 if res2.isdigit() else "Chưa đăng nhập"
    except: return "Lỗi Root"

def auto_update():
    print(f"{Y}[*] Đang kiểm tra cập nhật từ GitHub...{W}")
    try:
        # verify=False để tránh lỗi SSL trên máy ảo
        response = requests.get(UPDATE_URL, timeout=10, verify=False)
        if response.status_code == 200:
            remote_ver = re.search(r'VERSION = "([\d.]+)"', response.text).group(1)
            if remote_ver != VERSION:
                print(f"{G}[+] Đã tìm thấy bản {remote_ver}. Đang tải...{W}")
                with open(__file__, "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f"{G}[✔] Xong! Khởi động lại...{W}")
                time.sleep(1.5)
                os.execv(sys.executable, ['python'] + sys.argv)
            else:
                print(f"{G}[✔] Bạn đang dùng bản mới nhất.{W}")
        else:
            print(f"{R}[!] Lỗi: Repo đang để Private hoặc sai link.{W}")
    except:
        print(f"{R}[!] Lỗi kết nối. Hãy kiểm tra Internet!{W}")
    time.sleep(1)

# --- Phần còn lại giữ nguyên như bản trước ---
def main_hub():
    pkg = "com.vng.roblox" if "com.vng.roblox" in subprocess.getoutput("pm list packages com.vng.roblox") else "com.roblox.client"
    while True:
        os.system('clear')
        uid = get_roblox_id(pkg)
        print(f"{B}==========================================")
        print(f"{G}    DELTA HUB FIX - VERSION {VERSION}")
        print(f"{B}==========================================")
        print(f"{W} [1] Package: {Y}{pkg}")
        print(f"{W} [2] UserID:  {G}{uid}")
        print(f"{W} [3] BẮT ĐẦU AUTO REJOIN")
        print(f"{W} [6] Kiểm tra cập nhật")
        print(f"{W} [7] Thoát")
        
        c = input(f"{Y}Chọn: {W}")
        if c == '6': auto_update()
        elif c == '7': sys.exit()
        elif c == '3':
            # Chỗ này gọi hàm auto_loop như bản trước của bạn
            pass

if __name__ == "__main__":
    main_hub()