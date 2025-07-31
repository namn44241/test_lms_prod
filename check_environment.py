#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script kiểm tra môi trường cho test hiệu năng Selenium
"""

import sys
import subprocess
import pkg_resources
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def check_python():
    """Kiểm tra phiên bản Python"""
    print("="*50)
    print("KIỂM TRA PYTHON")
    print("="*50)
    print(f"Phiên bản Python: {sys.version}")
    print(f"Đường dẫn Python: {sys.executable}")
    
    # Kiểm tra phiên bản tối thiểu
    if sys.version_info >= (3, 6):
        print("✅ Python phiên bản phù hợp")
        return True
    else:
        print("❌ Python cần phiên bản 3.6 trở lên")
        return False

def check_packages():
    """Kiểm tra các packages Python cần thiết"""
    print("\n" + "="*50)
    print("KIỂM TRA PACKAGES PYTHON")
    print("="*50)
    
    required_packages = {
        'selenium': '4.0.0',
        'webdriver-manager': '3.0.0'
    }
    
    all_ok = True
    
    for package, min_version in required_packages.items():
        try:
            installed_version = pkg_resources.get_distribution(package).version
            print(f"✅ {package}: {installed_version}")
        except pkg_resources.DistributionNotFound:
            print(f"❌ {package}: Chưa được cài đặt")
            print(f"   Cài đặt bằng: pip3 install {package}")
            all_ok = False
    
    return all_ok

# def check_browser():
#     """Kiểm tra browser (Chrome/Chromium)"""
#     print("\n" + "="*50)
#     print("KIỂM TRA BROWSER")
#     print("="*50)
    
#     browsers = [
#         ("/usr/bin/chromium-browser", "Chromium Browser"),
#         ("/usr/bin/google-chrome", "Google Chrome"),
#         ("/usr/bin/chrome", "Chrome"),
#         ("/snap/bin/chromium", "Chromium Snap")
#     ]
    
#     found_browser = None
#     for browser_path, browser_name in browsers:
#         try:
#             result = subprocess.run([browser_path, "--version"], 
#                                   capture_output=True, text=True, timeout=10)
#             if result.returncode == 0:
#                 print(f"✅ {browser_name}: {result.stdout.strip()}")
#                 print(f"   Đường dẫn: {browser_path}")
#                 found_browser = browser_path
#                 break
#         except (subprocess.TimeoutExpired, FileNotFoundError):
#             continue
    
#     if not found_browser:
#         print("❌ Không tìm thấy Chrome hoặc Chromium")
#         print("   Cài đặt bằng: sudo apt install chromium-browser")
#         return False, None
    
#     return True, found_browser

def check_chromedriver():
    """Kiểm tra ChromeDriver"""
    print("\n" + "="*50)
    print("KIỂM TRA CHROMEDRIVER")
    print("="*50)
    
    drivers = [
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver",
        "./chromedriver"
    ]
    
    found_driver = None
    for driver_path in drivers:
        try:
            result = subprocess.run([driver_path, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ ChromeDriver: {result.stdout.strip()}")
                print(f"   Đường dẫn: {driver_path}")
                found_driver = driver_path
                break
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue
    
    if not found_driver:
        print("❌ Không tìm thấy ChromeDriver")
        print("   Cài đặt bằng: sudo apt install chromium-chromedriver")
        return False, None
    
    return True, found_driver

def test_selenium_connection(browser_path, driver_path):
    """Test kết nối Selenium với browser"""
    print("\n" + "="*50)
    print("TEST KẾT NỐI SELENIUM")
    print("="*50)
    
    try:
        # Cấu hình Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.binary_location = browser_path
        
        # Khởi tạo service
        service = Service(driver_path)
        
        print("Đang khởi tạo WebDriver...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("Đang test truy cập trang web...")
        driver.get("https://www.google.com")
        
        title = driver.title
        print(f"✅ Truy cập thành công! Tiêu đề trang: {title}")
        
        driver.quit()
        print("✅ WebDriver đã được đóng thành công")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi kết nối Selenium: {e}")
        return False

def test_odoo_connection():
    """Test kết nối đến server Odoo"""
    print("\n" + "="*50)
    print("TEST KẾT NỐI ODOO SERVER")
    print("="*50)
    
    try:
        import urllib.request
        import urllib.error
        
        url = "http://192.168.30.170:7300/web/login"
        print(f"Đang kiểm tra kết nối đến: {url}")
        
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.getcode() == 200:
                print("✅ Kết nối Odoo server thành công!")
                return True
            else:
                print(f"❌ Server trả về mã lỗi: {response.getcode()}")
                return False
                
    except urllib.error.URLError as e:
        print(f"❌ Không thể kết nối đến server Odoo: {e}")
        return False
    except Exception as e:
        print(f"❌ Lỗi không xác định: {e}")
        return False

def main():
    """Hàm main kiểm tra toàn bộ môi trường"""
    print("KIỂM TRA MÔI TRƯỜNG CHO TEST HIỆU NĂNG SELENIUM")
    print("Kiểm tra tất cả dependencies cần thiết...")
    
    all_checks = []
    
    # Kiểm tra Python
    all_checks.append(check_python())
    
    # Kiểm tra packages
    all_checks.append(check_packages())
    
    # # Kiểm tra browser
    # browser_ok, browser_path = check_browser()
    # all_checks.append(browser_ok)
    
    # Kiểm tra ChromeDriver
    driver_ok, driver_path = check_chromedriver()
    all_checks.append(driver_ok)
    
    # Test Selenium nếu browser và driver OK
    # if browser_ok and driver_ok:
    #     all_checks.append(test_selenium_connection(browser_path, driver_path))
    
    # Test kết nối Odoo
    all_checks.append(test_odoo_connection())
    
    # Tổng kết
    print("\n" + "="*50)
    print("TỔNG KẾT")
    print("="*50)
    
    if all(all_checks):
        print("🎉 TẤT CẢ KIỂM TRA THÀNH CÔNG!")
        print("Bạn có thể chạy test hiệu năng bằng lệnh:")
        print("python3 performance_test.py")
        return 0
    else:
        print("❌ MỘT SỐ KIỂM TRA THẤT BẠI")
        print("Vui lòng sửa các vấn đề trên trước khi chạy test.")
        return 1

if __name__ == "__main__":
    exit(main()) 