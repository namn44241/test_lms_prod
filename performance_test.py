#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script test hiệu năng cho Odoo LMS
Quy trình:
1. Đăng nhập vào hệ thống
2. Test hiệu năng trang slides chính
3. Test hiệu năng trang khóa học cụ thể
4. Test hiệu năng học liệu cụ thể
"""

import time
import json
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import threading
import concurrent.futures
import pandas as pd
from selenium.webdriver.chrome.service import Service as ChromeService
from tempfile import mkdtemp
import psutil
import matplotlib.pyplot as plt
import io
import os
import sys
import platform
import signal

# =============================================================================
# CẤU HÌNH TEST - SỬA TẠI ĐÂY
# =============================================================================
concurrent_users = 3

# Base URL của hệ thống
BASE_URL = "http://192.168.30.176:8017"

# URLs test - chia thành 3 mảng riêng biệt
SLIDES_MAIN = [
    "/slides"
]

COURSE_URLS = [
    "/slides/test-lms-30",
    # Thêm các khóa học khác tại đây
]

VIDEO_URLS = [
    "/slides/slide/ong-ho-em-nguoc-danh-cho-ai-lam-video-10s-197?fullscreen=1",
    "/slides/slide/10-seconds-countdown-ong-ho-em-nguoc-10-giay-198?fullscreen=1", 
    "/slides/slide/stunning-sunset-seen-from-the-sea-time-lapse-10-seconds-video-nature-blogs-199?fullscreen=1#",
    # Thêm các video khác tại đây
]

# File chứa danh sách tài khoản
ACCOUNTS_FILE = "Người dùng (res.users) (1).xlsx"

# =============================================================================

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SingleUserTest:
    """Class để test một user đơn lẻ"""
    def __init__(self, base_url, username, password, user_id=1):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.user_id = user_id
        self.driver = None
        self.results = []

    def setup_driver(self):
        """Khởi tạo Chrome driver cho single user"""
        chrome_options = Options()
        prefs = {
            # "download.default_directory": DOWNLOAD_DIR,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True,
            "safebrowsing.enabled": True,
        }
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        chrome_options.add_argument("--single-process") 
        
        import random
        remote_debugging_port = 9222 + self.user_id
        chrome_options.add_argument(f"--remote-debugging-port={remote_debugging_port}")
        
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Tạo unique user data directory cho mỗi user
        import tempfile
        import uuid
        temp_dir = tempfile.mkdtemp(prefix=f"chrome_user_{self.user_id}_{uuid.uuid4().hex[:8]}_")
        chrome_options.add_argument(f"--user-data-dir={temp_dir}")
        
        # chrome_options.binary_location = "/usr/bin/chromium-browser"
        
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            chromedriver_path = os.path.join(current_dir, "chromedriver")
            service = ChromeService(executable_path=chromedriver_path)

            service = ChromeService()
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info(f"User {self.user_id} ({self.username}): Driver khởi tạo thành công")
        except Exception as e:
            logger.error(f"User {self.user_id} ({self.username}): Lỗi khởi tạo driver: {e}")
            raise

    def login(self):
        """Đăng nhập cho single user"""
        try:
            login_url = f"{self.base_url}/web/login"
            logger.info(f"User {self.user_id} ({self.username}): Truy cập trang đăng nhập")
            
            start_time = time.time()
            self.driver.get(login_url)
            
            WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.ID, "login"))
            )
            login_load_time = time.time() - start_time
            
            time.sleep(1)
            
            username_field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "login"))
            )
            password_field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "password"))
            )
            
            username_field.clear()
            username_field.send_keys(self.username)
            
            password_field.clear()
            password_field.send_keys(self.password)
            
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and contains(text(), 'Đăng nhập')]"))
            )
            
            self.driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
            time.sleep(0.5)
            
            start_time = time.time()
            
            try:
                login_button.click()
            except:
                self.driver.execute_script("arguments[0].click();", login_button)
            
            try:
                WebDriverWait(self.driver, 20).until(
                    lambda driver: (
                        "/web#" in driver.current_url or 
                        "/web/session/authenticate" not in driver.current_url or
                        "/slides" in driver.current_url or
                        "action=" in driver.current_url
                    )
                )
            except:
                pass
            
            login_process_time = time.time() - start_time
            current_url = self.driver.current_url
            
            logger.info(f"User {self.user_id} ({self.username}): Đăng nhập hoàn tất! Thời gian: {login_process_time:.2f}s")
            
            if "/web/login" in current_url and "error" in self.driver.page_source.lower():
                raise Exception(f"User {self.user_id}: Đăng nhập thất bại")
            
            return {
                "login_load_time": login_load_time,
                "login_process_time": login_process_time
            }
            
        except Exception as e:
            logger.error(f"User {self.user_id} ({self.username}): Lỗi đăng nhập: {e}")
            raise

    def test_slides_main_page(self):
        """Test hiệu năng trang slides chính"""
        try:
            slides_url = f"{self.base_url}{SLIDES_MAIN[0]}"
            logger.info(f"User {self.user_id} ({self.username}): Test trang slides chính")
            
            start_time = time.time()
            self.driver.get(slides_url)
            
            WebDriverWait(self.driver, 15).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CLASS_NAME, "o_wslides_slides_list_slide")),
                    EC.presence_of_element_located((By.CLASS_NAME, "o_wslides_channel_card")),
                    EC.presence_of_element_located((By.ID, "wrap"))
                )
            )
            
            page_load_time = time.time() - start_time
            
            dom_ready_time = self.driver.execute_script(
                "return performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart"
            ) / 1000.0
            
            full_load_time = self.driver.execute_script(
                "return performance.timing.loadEventEnd - performance.timing.navigationStart"
            ) / 1000.0
            
            logger.info(f"User {self.user_id} ({self.username}): Slides chính - {page_load_time:.2f}s")
            
            return {
                "user_id": self.user_id,
                "username": self.username,
                "page": "slides_main",
                "url": slides_url,
                "selenium_load_time": page_load_time,
                "dom_ready_time": dom_ready_time,
                "full_load_time": full_load_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"User {self.user_id} ({self.username}): Lỗi test slides chính: {e}")
            raise

    def test_specific_course(self):
        """Test hiệu năng tất cả trang khóa học trong danh sách"""
        results = []
        
        for i, course_path in enumerate(COURSE_URLS):
            course_url = f"{self.base_url}{course_path}"
            logger.info(f"User {self.user_id} ({self.username}): Test khóa học {i+1}/{len(COURSE_URLS)}: {course_url}")
            
            start_time = time.time()
            self.driver.get(course_url)
            
            WebDriverWait(self.driver, 15).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CLASS_NAME, "o_wslides_slides_list_slide")),
                    EC.presence_of_element_located((By.CLASS_NAME, "o_wslides_channel_completion")),
                    EC.presence_of_element_located((By.ID, "wrap"))
                )
            )
            
            page_load_time = time.time() - start_time
            
            dom_ready_time = self.driver.execute_script(
                "return performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart"
            ) / 1000.0
            
            full_load_time = self.driver.execute_script(
                "return performance.timing.loadEventEnd - performance.timing.navigationStart"
            ) / 1000.0
            
            logger.info(f"User {self.user_id} ({self.username}): Khóa học {i+1} - {page_load_time:.2f}s")
            
            result = {
                "user_id": self.user_id,
                "username": self.username,
                "page": f"specific_course_{i+1}",
                "url": course_url,
                "selenium_load_time": page_load_time,
                "dom_ready_time": dom_ready_time,
                "full_load_time": full_load_time,
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)
            
            # Nghỉ giữa các course
            if i < len(COURSE_URLS) - 1:
                time.sleep(2)
                
        return results
            
    def test_specific_slide(self):
        """Test hiệu năng tất cả học liệu video trong danh sách"""
        results = []
        
        for i, video_path in enumerate(VIDEO_URLS):
            try:
                slide_url = f"{self.base_url}{video_path}"
                # Extract slide ID từ URL để dùng trong video detection
                import re
                slide_id_match = re.search(r'-(\d+)\?', video_path)
                self.slide_id = slide_id_match.group(1) if slide_id_match else "45"
                
                logger.info(f"User {self.user_id} ({self.username}): Test video {i+1}/{len(VIDEO_URLS)}: {slide_url}")
                
                start_time = time.time()
                self.driver.get(slide_url)
                
                WebDriverWait(self.driver, 20).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CLASS_NAME, "o_wslides_fs_sidebar")),
                        EC.presence_of_element_located((By.ID, "wrapwrap")),
                        EC.presence_of_element_located((By.TAG_NAME, "video")),
                        EC.presence_of_element_located((By.TAG_NAME, "iframe"))
                    )
                )
                
                # Detect loại video và xử lý theo logic từ JS
                try:
                    logger.info(f"User {self.user_id} ({self.username}): Bắt đầu phân tích video {i+1}...")
                    
                    # Detect loại video dựa trên JS logic
                    video_type = None
                    
                    # Kiểm tra internal video
                    try:
                        internal_video = self.driver.find_element(By.XPATH, f"//video[@id='internal-video{self.slide_id}']")
                        video_type = "internal"
                        logger.info(f"User {self.user_id} ({self.username}): Phát hiện Internal Video")
                    except:
                        pass
                    
                    # Kiểm tra YouTube video
                    if not video_type:
                        try:
                            youtube_player = self.driver.find_element(By.XPATH, f"//div[@id='youtube-player{self.slide_id}']")
                            video_type = "youtube"
                            logger.info(f"User {self.user_id} ({self.username}): Phát hiện YouTube Video")
                        except:
                            pass
                    
                    # Kiểm tra H5P
                    if not video_type:
                        try:
                            h5p_container = self.driver.find_element(By.CSS_SELECTOR, f".h5p-container{self.slide_id}")
                            video_type = "h5p"
                            logger.info(f"User {self.user_id} ({self.username}): Phát hiện H5P Content")
                        except:
                            pass
                    
                    # Kiểm tra embed link
                    if not video_type:
                        try:
                            embed_iframe = self.driver.find_element(By.XPATH, "//iframe[contains(@src, 'youtube')]")
                            video_type = "embed"
                            logger.info(f"User {self.user_id} ({self.username}): Phát hiện Embed Video")
                        except:
                            pass
                    
                    if not video_type:
                        logger.info(f"User {self.user_id} ({self.username}): Không xác định được loại video, thử click vào vùng video")
                        video_type = "unknown"
                    
                    # Xử lý theo từng loại video
                    if video_type == "internal":
                        logger.info(f"User {self.user_id} ({self.username}): Xử lý Internal Video")
                        # Click vào video để play
                        try:
                            video_element = self.driver.find_element(By.XPATH, f"//video[@id='internal-video{self.slide_id}']")
                            video_element.click()
                            logger.info(f"User {self.user_id} ({self.username}): Đã click vào internal video")
                        except Exception as e:
                            logger.warning(f"User {self.user_id} ({self.username}): Không thể click internal video: {e}")
                    
                    elif video_type == "youtube":
                        logger.info(f"User {self.user_id} ({self.username}): Xử lý YouTube Video")
                        # Click vào YouTube player
                        try:
                            youtube_element = self.driver.find_element(By.XPATH, f"//div[@id='youtube-player{self.slide_id}']")
                            # Click vào giữa player
                            self.driver.execute_script("arguments[0].click();", youtube_element)
                            logger.info(f"User {self.user_id} ({self.username}): Đã click vào YouTube player")
                        except Exception as e:
                            logger.warning(f"User {self.user_id} ({self.username}): Không thể click YouTube player: {e}")
                    
                    elif video_type == "embed":
                        logger.info(f"User {self.user_id} ({self.username}): Xử lý Embed Video")
                        # Click vào iframe
                        try:
                            iframe = self.driver.find_element(By.XPATH, "//iframe")
                            self.driver.execute_script("arguments[0].click();", iframe)
                            logger.info(f"User {self.user_id} ({self.username}): Đã click vào embed iframe")
                        except Exception as e:
                            logger.warning(f"User {self.user_id} ({self.username}): Không thể click embed iframe: {e}")
                    
                    else:
                        # Thử click vào vùng video (bên phải màn hình như bạn gợi ý)
                        logger.info(f"User {self.user_id} ({self.username}): Thử click vào vùng video")
                        try:
                            # Tìm vùng player
                            player_area = None
                            player_selectors = [
                                ".o_wslides_fs_content",
                                ".player",
                                ".embed-responsive-item",
                                ".ratio"
                            ]
                            
                            for selector in player_selectors:
                                try:
                                    player_area = self.driver.find_element(By.CSS_SELECTOR, selector)
                                    logger.info(f"User {self.user_id} ({self.username}): Tìm thấy player area: {selector}")
                                    break
                                except:
                                    continue
                            
                            if player_area:
                                # Click vào giữa player area
                                self.driver.execute_script("arguments[0].click();", player_area)
                                logger.info(f"User {self.user_id} ({self.username}): Đã click vào player area")
                            else:
                                # Click vào vị trí giữa bên phải màn hình
                                self.driver.execute_script("window.dispatchEvent(new MouseEvent('click', {clientX: window.innerWidth * 0.7, clientY: window.innerHeight * 0.5, bubbles: true}));")
                                logger.info(f"User {self.user_id} ({self.username}): Đã click vào vị trí giữa bên phải màn hình")
                        except Exception as e:
                            logger.warning(f"User {self.user_id} ({self.username}): Không thể click vào vùng video: {e}")
                    
                    # Đợi video phát hoàn thành (11s + buffer)
                    logger.info(f"User {self.user_id} ({self.username}): Đợi video {i+1} phát hoàn thành...")
                    time.sleep(12)
                    logger.info(f"User {self.user_id} ({self.username}): Hoàn thành xem video {i+1}")
                        
                except Exception as e:
                    logger.warning(f"User {self.user_id} ({self.username}): Lỗi xử lý video {i+1}: {e}")
                    time.sleep(12)
                
                # Tính tổng thời gian từ load trang đến hoàn thành xem video
                total_time = time.time() - start_time
                
                try:
                    dom_ready_time = self.driver.execute_script(
                        "return performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart"
                    ) / 1000.0
                    
                    full_load_time = self.driver.execute_script(
                        "return performance.timing.loadEventEnd - performance.timing.navigationStart"
                    ) / 1000.0
                except:
                    dom_ready_time = total_time
                    full_load_time = total_time
                
                logger.info(f"User {self.user_id} ({self.username}): Video {i+1} (bao gồm xem video) - {total_time:.2f}s")
                
                result = {
                    "user_id": self.user_id,
                    "username": self.username,
                    "page": f"specific_slide_with_video_{i+1}",
                    "url": slide_url,
                    "selenium_load_time": total_time,
                    "dom_ready_time": dom_ready_time,
                    "full_load_time": total_time,
                    "video_watched": True,
                    "timestamp": datetime.now().isoformat()
                }
                results.append(result)
                
                # Nghỉ giữa các video
                if i < len(VIDEO_URLS) - 1:
                    logger.info(f"User {self.user_id} ({self.username}): Nghỉ 3 giây trước video tiếp theo...")
                    time.sleep(3)
                
            except Exception as e:
                logger.error(f"User {self.user_id} ({self.username}): Lỗi test video {i+1}: {e}")
                # Thêm result lỗi để không bỏ sót
                error_result = {
                    "user_id": self.user_id,
                    "username": self.username,
                    "page": f"specific_slide_with_video_{i+1}",
                    "url": f"{self.base_url}{video_path}",
                    "selenium_load_time": 0,
                    "dom_ready_time": 0,
                    "full_load_time": 0,
                    "video_watched": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                results.append(error_result)
                
        return results

    def run_single_user_test(self):
        """Chạy test cho 1 user"""
        temp_dir = None
        try:
            self.setup_driver()
            
            # Đăng nhập
            login_result = self.login()
            
            # Test các trang
            slides_result = self.test_slides_main_page()
            self.results.append(slides_result)
            time.sleep(2)
            
            course_results = self.test_specific_course()
            self.results.extend(course_results)  # extend vì trả về mảng
            time.sleep(2)
            
            slide_results = self.test_specific_slide()
            self.results.extend(slide_results)  # extend vì trả về mảng
            
            return self.results
            
        except Exception as e:
            logger.error(f"User {self.user_id} ({self.username}): Lỗi trong test: {e}")
            raise
        finally:
            if hasattr(self, 'driver') and self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            try:
                import tempfile
                import glob
                import shutil
                temp_dirs = glob.glob(f"{tempfile.gettempdir()}/chrome_user_{self.user_id}_*")
                for temp_dir in temp_dirs:
                    try:
                        shutil.rmtree(temp_dir, ignore_errors=True)
                    except:
                        pass
            except:
                pass

class OdooPerformanceTest:
    def __init__(self):
        self.base_url = BASE_URL
        
        # Mảng tài khoản để test với nhiều người dùng
        # Tự động tạo 300 accounts hv12 đến hv311 - mk giống tài khoản
        self.accounts = []
        df = pd.read_excel(ACCOUNTS_FILE, engine='openpyxl')
        # Giả sử bạn muốn lấy cột tên là "Tên"
        danh_sach = df["login"].tolist()
        # for i in range(1, 364):  # hv12 đến hv311 = 300 users
        #     self.accounts.append([f"hv{i}", f"hv{i}"])
        self.accounts = [[ds,ds] for ds in danh_sach]
        # CẤU HÌNH TEST - SỬA TẠI ĐÂY
        self.concurrent_users = concurrent_users  # Số người học cùng lúc: 50 người đồng thời
        self.num_iterations = 1     # Số lần lặp test
        
        # Thông tin cho single user test (backward compatibility)
        self.username = "hv"  # Dùng cho single user mode
        self.password = "hv"
        self.driver = None
        self.results = []
        
    def cleanup_chrome_processes(self):
        """Dọn dẹp các process Chrome cũ để tránh xung đột"""
        import subprocess
        import psutil
        
        try:
            # Dừng tất cả process Chrome/Chromium
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and any(name in proc.info['name'].lower() for name in ['chrome', 'chromium']):
                    try:
                        proc.kill()
                        logger.info(f"Đã dừng process Chrome: {proc.info['pid']}")
                    except:
                        pass
            
            # Dọn dẹp các temp directory cũ
            import tempfile
            import glob
            temp_dirs = glob.glob(f"{tempfile.gettempdir()}/chrome_user_*")
            for temp_dir in temp_dirs:
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                    logger.info(f"Đã xóa temp dir: {temp_dir}")
                except:
                    pass
                    
            logger.info("Hoàn thành cleanup Chrome processes")
        except Exception as e:
            logger.warning(f"Lỗi trong cleanup: {e}")
        
    def setup_driver(self):
        """Khởi tạo Chrome driver với các tùy chọn tối ưu"""
        chrome_options = Options()
        prefs = {
            # "download.default_directory": DOWNLOAD_DIR,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True,
            "safebrowsing.enabled": True,
        }
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        chrome_options.add_argument("--remote-debugging-port=9222")
        
        chrome_options.add_experimental_option("prefs", prefs)
        # Sử dụng Chromium thay vì Chrome
        # chrome_options.binary_location = "/usr/bin/chromium-browser"
        
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            chromedriver_path = os.path.join(current_dir, "chromedriver")
            service = ChromeService(executable_path=chromedriver_path)
            # service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Driver khởi tạo thành công với headless mode")
        except Exception as e:
            logger.error(f"Lỗi khởi tạo driver: {e}")
            raise
            
    def login(self):
        """Đăng nhập vào hệ thống Odoo"""
        try:
            login_url = f"{self.base_url}/web/login"
            logger.info(f"Truy cập trang đăng nhập: {login_url}")
            
            start_time = time.time()
            self.driver.get(login_url)
            
            # Đợi trang tải xong và element có thể tương tác
            WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.NAME, "login"))
            )
            login_load_time = time.time() - start_time
            logger.info(f"Thời gian tải trang đăng nhập: {login_load_time:.2f}s")
            
            # Chờ thêm một chút để đảm bảo page hoàn toàn sẵn sàng
            time.sleep(1)
            
            # Tìm email field theo HTML cung cấp
            username_field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "login"))
            )
            logger.info("Tìm thấy email field")
            
            # Tìm password field theo HTML cung cấp  
            password_field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "password"))
            )
            logger.info("Tìm thấy password field")
            
            # Clear field trước khi nhập
            username_field.clear()
            username_field.send_keys(self.username)
            logger.info("Đã nhập username: hv")
            
            password_field.clear()
            password_field.send_keys(self.password)
            logger.info("Đã nhập password: hv")
            
            # Tìm nút đăng nhập theo HTML cung cấp
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and contains(text(), 'Đăng nhập')]"))
            )
            logger.info("Tìm thấy nút đăng nhập")
            
            # Scroll đến button nếu cần
            self.driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
            time.sleep(0.5)
            
            start_time = time.time()
            
            # Thử click bằng JavaScript nếu click thường không work
            try:
                login_button.click()
            except:
                logger.info("Click thường không work, thử bằng JavaScript")
                self.driver.execute_script("arguments[0].click();", login_button)
            
            logger.info("Đã click nút đăng nhập, đang chờ chuyển hướng...")
            
            # Đợi chuyển hướng sau đăng nhập với timeout dài hơn
            try:
                WebDriverWait(self.driver, 20).until(
                    lambda driver: (
                        "/web#" in driver.current_url or 
                        "/web/session/authenticate" not in driver.current_url or
                        "/slides" in driver.current_url or
                        "action=" in driver.current_url
                    )
                )
            except:
                # Nếu không thể đợi URL thay đổi, kiểm tra xem có element sau đăng nhập không
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.CLASS_NAME, "o_main_navbar")),
                            EC.presence_of_element_located((By.CLASS_NAME, "oe_topbar")),
                            EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'o_web_client')]"))
                        )
                    )
                except:
                    logger.warning("Không thể xác nhận đăng nhập thành công bằng URL hoặc element")
            
            login_process_time = time.time() - start_time
            
            current_url = self.driver.current_url
            logger.info(f"Đăng nhập hoàn tất! Thời gian xử lý: {login_process_time:.2f}s")
            logger.info(f"URL sau đăng nhập: {current_url}")
            
            # Kiểm tra xem có thực sự đăng nhập thành công không
            if "/web/login" in current_url and "error" in self.driver.page_source.lower():
                raise Exception("Đăng nhập thất bại - sai username/password hoặc lỗi khác")
            
            return {
                "login_load_time": login_load_time,
                "login_process_time": login_process_time
            }
            
        except Exception as e:
            # Lưu screenshot để debug
            try:
                self.driver.save_screenshot("login_error.png")
                logger.info("Đã lưu screenshot lỗi: login_error.png")
            except:
                pass
            logger.error(f"Lỗi đăng nhập: {e}")
            raise
            
    def test_slides_main_page(self):
        """Test hiệu năng trang slides chính"""
        try:
            slides_url = f"{self.base_url}{SLIDES_MAIN[0]}"
            logger.info(f"Test trang slides chính: {slides_url}")
            
            start_time = time.time()
            self.driver.get(slides_url)
            
            # Đợi nội dung chính tải xong
            WebDriverWait(self.driver, 15).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CLASS_NAME, "o_wslides_slides_list_slide")),
                    EC.presence_of_element_located((By.CLASS_NAME, "o_wslides_channel_card")),
                    EC.presence_of_element_located((By.ID, "wrap"))
                )
            )
            
            page_load_time = time.time() - start_time
            
            # Đo thời gian DOM ready
            dom_ready_time = self.driver.execute_script(
                "return performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart"
            ) / 1000.0
            
            # Đo thời gian tải hoàn toàn
            full_load_time = self.driver.execute_script(
                "return performance.timing.loadEventEnd - performance.timing.navigationStart"
            ) / 1000.0
            
            logger.info(f"Trang slides chính - Page load: {page_load_time:.2f}s, DOM ready: {dom_ready_time:.2f}s, Full load: {full_load_time:.2f}s")
            
            return {
                "page": "slides_main",
                "url": slides_url,
                "selenium_load_time": page_load_time,
                "dom_ready_time": dom_ready_time,
                "full_load_time": full_load_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Lỗi test trang slides chính: {e}")
            raise
            
    def test_specific_course(self):
        """Test hiệu năng tất cả trang khóa học trong danh sách"""
        results = []
        
        for i, course_path in enumerate(COURSE_URLS):
            try:
                course_url = f"{self.base_url}{course_path}"
                logger.info(f"Test khóa học {i+1}/{len(COURSE_URLS)}: {course_url}")
                
                start_time = time.time()
                self.driver.get(course_url)
                
                # Đợi nội dung khóa học tải xong
                WebDriverWait(self.driver, 15).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CLASS_NAME, "o_wslides_slides_list_slide")),
                        EC.presence_of_element_located((By.CLASS_NAME, "o_wslides_channel_completion")),
                        EC.presence_of_element_located((By.ID, "wrap"))
                    )
                )
                
                page_load_time = time.time() - start_time
                
                # Đo timing từ browser
                dom_ready_time = self.driver.execute_script(
                    "return performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart"
                ) / 1000.0
                
                full_load_time = self.driver.execute_script(
                    "return performance.timing.loadEventEnd - performance.timing.navigationStart"
                ) / 1000.0
                
                logger.info(f"Khóa học {i+1} - Page load: {page_load_time:.2f}s, DOM ready: {dom_ready_time:.2f}s, Full load: {full_load_time:.2f}s")
                
                result = {
                    "page": f"specific_course_{i+1}",
                    "url": course_url,
                    "selenium_load_time": page_load_time,
                    "dom_ready_time": dom_ready_time,
                    "full_load_time": full_load_time,
                    "timestamp": datetime.now().isoformat()
                }
                results.append(result)
                
                # Nghỉ giữa các course
                if i < len(COURSE_URLS) - 1:
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"Lỗi test khóa học {i+1}: {e}")
                # Thêm result lỗi
                error_result = {
                    "page": f"specific_course_{i+1}",
                    "url": f"{self.base_url}{course_path}",
                    "selenium_load_time": 0,
                    "dom_ready_time": 0,
                    "full_load_time": 0,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                results.append(error_result)
                
        return results
            
    def test_specific_slide(self):
        """Test hiệu năng tất cả học liệu video trong danh sách"""
        results = []
        
        for i, video_path in enumerate(VIDEO_URLS):
            try:
                slide_url = f"{self.base_url}{video_path}"
                logger.info(f"Test video {i+1}/{len(VIDEO_URLS)}: {slide_url}")
                
                start_time = time.time()
                self.driver.get(slide_url)
                
                # Đợi nội dung học liệu tải xong (có thể là video player hoặc nội dung khác)
                WebDriverWait(self.driver, 20).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CLASS_NAME, "o_wslides_fs_sidebar")),
                        EC.presence_of_element_located((By.ID, "wrapwrap")),
                        EC.presence_of_element_located((By.TAG_NAME, "video")),
                        EC.presence_of_element_located((By.TAG_NAME, "iframe"))
                    )
                )
                
                page_load_time = time.time() - start_time
                logger.info(f"Video {i+1} tải xong trong {page_load_time:.2f}s")
                
                # Tìm và click nút play video - cần switch vào iframe
                try:
                    logger.info(f"Đang tìm nút play video {i+1}...")
                    
                    play_button = None
                    
                    # Đầu tiên thử tìm iframe YouTube
                    try:
                        iframe = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//iframe[contains(@src, 'youtube') or contains(@src, 'ytimg')]"))
                        )
                        logger.info("Tìm thấy iframe YouTube")
                        
                        # Switch vào iframe
                        self.driver.switch_to.frame(iframe)
                        logger.info("Đã switch vào iframe")
                        
                        # Tìm nút play trong iframe
                        play_selectors_iframe = [
                            "//button[contains(@class, 'ytp-large-play-button')]",
                            "//button[@aria-label='Phát']",
                            "//button[@aria-label='Play']",
                            "//div[contains(@class, 'ytp-cued-thumbnail-overlay')]",
                            ".ytp-large-play-button"
                        ]
                        
                        for selector in play_selectors_iframe:
                            try:
                                if selector.startswith("."):
                                    play_button = WebDriverWait(self.driver, 3).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                    )
                                else:
                                    play_button = WebDriverWait(self.driver, 3).until(
                                        EC.element_to_be_clickable((By.XPATH, selector))
                                    )
                                logger.info(f"Tìm thấy play button trong iframe: {selector}")
                                break
                            except:
                                continue
                        
                    except Exception as e:
                        logger.info(f"Không tìm thấy iframe hoặc lỗi: {e}")
                        
                        # Nếu không có iframe, tìm trực tiếp trên trang
                        play_selectors_direct = [
                            "//button[contains(@class, 'ytp-large-play-button') and @aria-label='Phát']",
                            "//button[contains(@class, 'ytp-large-play-button')]",
                            "//div[contains(@class, 'ytp-cued-thumbnail-overlay')]",
                            "//button[@aria-label='Phát']",
                            "//button[@title='Phát']",
                            ".ytp-large-play-button"
                        ]
                        
                        for selector in play_selectors_direct:
                            try:
                                if selector.startswith("."):
                                    play_button = WebDriverWait(self.driver, 3).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                    )
                                else:
                                    play_button = WebDriverWait(self.driver, 3).until(
                                        EC.element_to_be_clickable((By.XPATH, selector))
                                    )
                                logger.info(f"Tìm thấy play button trực tiếp: {selector}")
                                break
                            except:
                                continue
                    
                    if play_button:
                        logger.info(f"Click nút play video {i+1}...")
                        
                        # Thử click bằng nhiều cách
                        try:
                            play_button.click()
                        except:
                            try:
                                self.driver.execute_script("arguments[0].click();", play_button)
                            except:
                                logger.warning("Không thể click nút play")
                        
                        # Đợi video bắt đầu phát và xem hết 11 giây
                        logger.info(f"Đang xem video {i+1} - 11 giây...")
                        time.sleep(12)  # Chờ hơn 11s để đảm bảo video xem hết
                        logger.info(f"Đã xem xong video {i+1}!")
                    else:
                        logger.warning(f"Không tìm thấy nút play video {i+1}, có thể video tự động phát")
                        time.sleep(12)
                    
                    # Switch về main content
                    try:
                        self.driver.switch_to.default_content()
                    except:
                        pass
                        
                except Exception as e:
                    logger.warning(f"Lỗi khi thao tác với video {i+1}: {e}")
                    # Switch về main content nếu có lỗi
                    try:
                        self.driver.switch_to.default_content()
                    except:
                        pass
                    time.sleep(12)
                
                # Đo timing từ browser
                try:
                    dom_ready_time = self.driver.execute_script(
                        "return performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart"
                    ) / 1000.0
                    
                    full_load_time = self.driver.execute_script(
                        "return performance.timing.loadEventEnd - performance.timing.navigationStart"
                    ) / 1000.0
                except:
                    dom_ready_time = page_load_time
                    full_load_time = page_load_time
                
                logger.info(f"Video {i+1} - Page load: {page_load_time:.2f}s, DOM ready: {dom_ready_time:.2f}s, Full load: {full_load_time:.2f}s")
                
                result = {
                    "page": f"specific_slide_with_video_{i+1}",
                    "url": slide_url,
                    "selenium_load_time": page_load_time,
                    "dom_ready_time": dom_ready_time,
                    "full_load_time": full_load_time,
                    "video_watched": True,
                    "timestamp": datetime.now().isoformat()
                }
                results.append(result)
                
                # Nghỉ giữa các video
                if i < len(VIDEO_URLS) - 1:
                    logger.info(f"Nghỉ 3 giây trước video tiếp theo...")
                    time.sleep(3)
                
            except Exception as e:
                logger.error(f"Lỗi test video {i+1}: {e}")
                # Thêm result lỗi
                error_result = {
                    "page": f"specific_slide_with_video_{i+1}",
                    "url": f"{self.base_url}{video_path}",
                    "selenium_load_time": 0,
                    "dom_ready_time": 0,
                    "full_load_time": 0,
                    "video_watched": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                results.append(error_result)
                
        return results
            
    def run_performance_test(self, num_iterations=1):
        """Chạy test hiệu năng với số lần lặp nhất định (single user)"""
        try:
            self.setup_driver()
            
            # Đăng nhập một lần
            login_result = self.login()
            
            for i in range(num_iterations):
                logger.info(f"--- Lần chạy thứ {i+1}/{num_iterations} ---")
                
                # Test trang slides chính
                slides_result = self.test_slides_main_page()
                slides_result["iteration"] = i + 1
                self.results.append(slides_result)
                
                time.sleep(2)  # Nghỉ giữa các test
                
                # Test trang khóa học cụ thể
                course_results = self.test_specific_course()
                for result in course_results:
                    result["iteration"] = i + 1
                self.results.extend(course_results)
                
                time.sleep(2)
                
                # Test học liệu cụ thể
                slide_results = self.test_specific_slide()
                for result in slide_results:
                    result["iteration"] = i + 1
                self.results.extend(slide_results)
                
                time.sleep(3)  # Nghỉ giữa các lần lặp
                
        except Exception as e:
            logger.error(f"Lỗi trong quá trình test: {e}")
            raise
        finally:
            if self.driver:
                self.driver.quit()

    def run_multiple_users_test(self):
        """Chạy test với nhiều người dùng theo logic mới"""
        global completed_users, global_tester
        
        if self.concurrent_users == 1:
            # Chế độ lần lượt từng người
            logger.info("Chế độ LẦN LƯỢT TỪNG NGƯỜI")
            logger.info(f"Sẽ test lần lượt {len(self.accounts)} người dùng")
            
            all_results = []
            for i, (username, password) in enumerate(self.accounts):
                logger.info(f"=== TEST NGƯỜI {i+1}/{len(self.accounts)}: {username} ===")
                
                user_test = SingleUserTest(self.base_url, username, password, i+1)
                user_results = user_test.run_single_user_test()
                all_results.extend(user_results)
                # Cập nhật results ngay lập tức để có thể dùng khi Ctrl+C
                self.results = all_results
                global_tester.results = all_results
                logger.info(f"User {i+1} ({username}): Hoàn thành test")
                # Track completion
                completed_users += 1
                # Nghỉ giữa các user
                if i < len(self.accounts) - 1:
                    logger.info("Nghỉ 3 giây trước user tiếp theo...")
                    time.sleep(3)
            
            self.results = all_results
            
        else:
            # Chế độ nhiều người cùng lúc
            logger.info(f"Chế độ ĐỒNG THỜI - {self.concurrent_users} người cùng lúc")
            
            all_results = []
            total_accounts = len(self.accounts)
            
            # Chia nhóm theo concurrent_users
            for batch_start in range(0, total_accounts, self.concurrent_users):
                batch_end = min(batch_start + self.concurrent_users, total_accounts)
                batch_accounts = self.accounts[batch_start:batch_end]
                
                logger.info(f"=== NHÓM {batch_start//self.concurrent_users + 1}: {[acc[0] for acc in batch_accounts]} ===")
                
                # Chạy đồng thời nhóm này
                with concurrent.futures.ThreadPoolExecutor(max_workers=len(batch_accounts)) as executor:
                    future_to_user = {}
                    
                    for i, (username, password) in enumerate(batch_accounts):
                        user_id = batch_start + i + 1
                        user_test = SingleUserTest(self.base_url, username, password, i+1)
                        future = executor.submit(user_test.run_single_user_test)
                        future_to_user[future] = (username, user_id)
                    
                    # Chờ tất cả user trong nhóm hoàn thành
                    for future in concurrent.futures.as_completed(future_to_user):
                        username, user_id = future_to_user[future]
                        try:
                            user_results = future.result()
                            all_results.extend(user_results)
                            # Cập nhật results ngay lập tức để có thể dùng khi Ctrl+C
                            self.results = all_results
                            global_tester.results = all_results
                            logger.info(f"User {user_id} ({username}): Hoàn thành test")
                            # Track completion
                            completed_users += 1
                        except Exception as e:
                            logger.error(f"User {user_id} ({username}): Lỗi: {e}")
                
                # Nghỉ giữa các nhóm
                if batch_end < total_accounts:
                    logger.info("Nghỉ 5 giây trước nhóm tiếp theo...")
                    time.sleep(5)
            
            self.results = all_results
        
        logger.info(f"Hoàn thành tất cả test. Tổng cộng: {len(self.results)} kết quả")
                
    def save_results(self, filename="performance_results.json"):
        """Lưu kết quả test vào file JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "test_info": {
                        "base_url": self.base_url,
                        "username": self.username,
                        "test_time": datetime.now().isoformat(),
                        "total_results": len(self.results)
                    },
                    "results": self.results
                }, f, indent=2, ensure_ascii=False)
            logger.info(f"Kết quả đã được lưu vào {filename}")
        except Exception as e:
            logger.error(f"Lỗi lưu kết quả: {e}")
            
    def print_summary(self):
        """In tóm tắt kết quả"""
        if not self.results:
            logger.warning("Không có kết quả để hiển thị")
            return
            
        print("\n" + "="*70)
        print("TÓM TẮT KẾT QUẢ TEST HIỆU NĂNG")
        print("="*70)
        
        # Hiển thị thông tin tổng quan
        unique_users = set()
        for result in self.results:
            if 'username' in result:
                unique_users.add(result['username'])
        
        print(f"Số người dùng tham gia test: {len(unique_users)}")
        print(f"Tổng số kết quả: {len(self.results)}")
        if unique_users:
            print(f"Danh sách users: {', '.join(sorted(unique_users))}")
        
        # Nhóm kết quả theo trang
        pages = {}
        for result in self.results:
            page = result["page"]
            if page not in pages:
                pages[page] = []
            pages[page].append(result)
            
        for page_name, page_results in pages.items():
            print(f"\n{page_name.upper()}:")
            print(f"URL: {page_results[0]['url']}")
            print(f"Số lần test: {len(page_results)}")
            
            selenium_times = [r["selenium_load_time"] for r in page_results]
            dom_times = [r["dom_ready_time"] for r in page_results]
            full_times = [r["full_load_time"] for r in page_results]
            
            print(f"Selenium Load Time - Trung bình: {sum(selenium_times)/len(selenium_times):.2f}s, Min: {min(selenium_times):.2f}s, Max: {max(selenium_times):.2f}s")
            print(f"DOM Ready Time - Trung bình: {sum(dom_times)/len(dom_times):.2f}s, Min: {min(dom_times):.2f}s, Max: {max(dom_times):.2f}s")
            print(f"Full Load Time - Trung bình: {sum(full_times)/len(full_times):.2f}s, Min: {min(full_times):.2f}s, Max: {max(full_times):.2f}s")
            
            # Hiển thị chi tiết theo user nếu có nhiều users
            if len(unique_users) > 1:
                print("  Chi tiết theo user:")
                user_results = {}
                for result in page_results:
                    if 'username' in result:
                        username = result['username']
                        if username not in user_results:
                            user_results[username] = []
                        user_results[username].append(result['selenium_load_time'])
                
                for username, times in user_results.items():
                    avg_time = sum(times) / len(times)
                    print(f"    {username}: {avg_time:.2f}s (trung bình từ {len(times)} lần)")

    def create_performance_report(self, base_filename="performance_report"):
        """Tạo báo cáo hiệu năng chi tiết với Excel và text summary"""
        try:
            if not self.results:
                logger.warning("Không có kết quả để tạo báo cáo")
                return
            
            # Chuẩn bị test config cho reporter
            test_config = {
                'concurrent_users': self.concurrent_users,
                'num_iterations': self.num_iterations,
                'base_url': self.base_url,
                'test_time': datetime.now().isoformat(),
                'total_accounts': len(self.accounts)
            }
            
            # Placeholder cho PerformanceReporter class
            # Người dùng sẽ copy-paste class PerformanceReporter vào đây
            try:
                # Kiểm tra xem class PerformanceReporter đã được định nghĩa chưa
                if 'PerformanceReporter' in globals():
                    logger.info("Tạo báo cáo Excel chi tiết...")
                    reporter = PerformanceReporter(self.results, test_config)
                    
                    # Tạo báo cáo Excel
                    excel_filename = f"{base_filename}.xlsx"
                    reporter.create_excel_report(excel_filename)
                    
                    # Tạo báo cáo text chi tiết
                    text_summary = reporter.generate_summary_text()
                    text_filename = f"{base_filename}_summary.txt"
                    
                    with open(text_filename, 'w', encoding='utf-8') as f:
                        f.write(text_summary)
                    
                    logger.info(f"Báo cáo chi tiết đã được tạo:")
                    logger.info(f"  - Excel: {excel_filename}")
                    logger.info(f"  - Text: {text_filename}")
                    
                    # In summary ra console
                    print("\n" + text_summary)
                    
                else:
                    logger.warning("Class PerformanceReporter chưa được định nghĩa")
                    logger.info("Hãy copy-paste class PerformanceReporter vào file này để tạo báo cáo Excel")
                    
            except Exception as e:
                logger.error(f"Lỗi tạo báo cáo chi tiết: {e}")
                logger.info("Sử dụng báo cáo đơn giản thay thế...")
                self._create_simple_report(base_filename, test_config)
                
        except Exception as e:
            logger.error(f"Lỗi tạo báo cáo: {e}")
            
    def _create_simple_report(self, base_filename, test_config):
        """Tạo báo cáo đơn giản khi không có PerformanceReporter"""
        try:
            # Tạo DataFrame đơn giản
            df = pd.DataFrame(self.results)
            
            # Lưu raw data
            raw_filename = f"{base_filename}_raw_data.xlsx"
            df.to_excel(raw_filename, index=False)
            
            # Tạo summary text đơn giản
            summary_lines = []
            summary_lines.append("="*50)
            summary_lines.append("BÁO CÁO HIỆU NĂNG ODOO LMS")
            summary_lines.append("="*50)
            summary_lines.append(f"Thời gian test: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            summary_lines.append(f"Tổng số test: {len(self.results)}")
            summary_lines.append(f"Concurrent users: {test_config['concurrent_users']}")
            summary_lines.append("")
            
            # Thống kê theo trang
            pages = df['page'].unique()
            for page in pages:
                page_data = df[df['page'] == page]['selenium_load_time']
                summary_lines.append(f"{page.upper()}:")
                summary_lines.append(f"  Trung bình: {page_data.mean():.2f}s")
                summary_lines.append(f"  Min/Max: {page_data.min():.2f}s / {page_data.max():.2f}s")
                summary_lines.append("")
            
            # Lưu summary
            summary_filename = f"{base_filename}_simple_summary.txt"
            with open(summary_filename, 'w', encoding='utf-8') as f:
                f.write("\n".join(summary_lines))
            
            logger.info(f"Báo cáo đơn giản đã được tạo:")
            logger.info(f"  - Raw data: {raw_filename}")
            logger.info(f"  - Summary: {summary_filename}")
            
        except Exception as e:
            logger.error(f"Lỗi tạo báo cáo đơn giản: {e}")

class PerformanceReporter:
    """Class tạo báo cáo Excel nâng cao với biểu đồ và thống kê"""
    
    def __init__(self, results, test_config):
        self.results = results
        self.test_config = test_config
        self.df = pd.DataFrame(results)
        
        # Cấu hình matplotlib cho font và style
        plt.style.use('seaborn-v0_8')
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
        
    def create_excel_report(self, filename="performance_report.xlsx"):
        """Tạo báo cáo Excel chi tiết với biểu đồ"""
        try:
            # Tạo writer object
            with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
                workbook = writer.book
                
                # Định nghĩa formats
                title_format = workbook.add_format({
                    'bold': True, 'font_size': 16, 'align': 'center',
                    'bg_color': '#4472C4', 'font_color': 'white'
                })
                header_format = workbook.add_format({
                    'bold': True, 'font_size': 12, 'align': 'center',
                    'bg_color': '#D9E2F3', 'border': 1
                })
                data_format = workbook.add_format({'align': 'center', 'border': 1})
                number_format = workbook.add_format({'num_format': '0.00', 'align': 'center', 'border': 1})
                
                # 1. Trang tổng quan
                self._create_overview_sheet(writer, title_format, header_format, data_format, number_format)
                
                # 2. Trang dữ liệu raw
                self._create_raw_data_sheet(writer, header_format, data_format, number_format)
                
                # 3. Trang thống kê theo trang web
                self._create_page_statistics_sheet(writer, header_format, data_format, number_format)
                
                # 4. Trang thống kê theo user
                self._create_user_statistics_sheet(writer, header_format, data_format, number_format)
                
                # 5. Trang so sánh hiệu năng
                self._create_performance_comparison_sheet(writer, header_format, data_format, number_format)
                
                # 6. Trang biểu đồ
                self._create_charts_sheet(writer)
                
            logger.info(f"Báo cáo Excel đã được tạo: {filename}")
            
            # Tạo báo cáo bổ sung với openpyxl cho biểu đồ nâng cao
            self._enhance_excel_with_charts(filename)
            
        except Exception as e:
            logger.error(f"Lỗi tạo báo cáo Excel: {e}")
            raise
    
    def _create_overview_sheet(self, writer, title_format, header_format, data_format, number_format):
        """Tạo sheet tổng quan"""
        worksheet = writer.book.add_worksheet('Tổng quan')
        
        # Tiêu đề
        worksheet.merge_range('A1:H1', 'BÁO CÁO HIỆU NĂNG ODOO LMS', title_format)
        
        row = 3
        # Thông tin test
        worksheet.write(row, 0, 'Thông tin Test:', header_format)
        row += 1
        worksheet.write(row, 0, 'Thời gian test:', data_format)
        worksheet.write(row, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), data_format)
        row += 1
        worksheet.write(row, 0, 'Số người dùng:', data_format)
        worksheet.write(row, 1, len(self.df['username'].unique()) if 'username' in self.df.columns else 1, data_format)
        row += 1
        worksheet.write(row, 0, 'Tổng số test:', data_format)
        worksheet.write(row, 1, len(self.df), data_format)
        row += 1
        worksheet.write(row, 0, 'Concurrent users:', data_format)
        worksheet.write(row, 1, self.test_config.get('concurrent_users', 1), data_format)
        
        row += 3
        # Thống kê tổng quan
        worksheet.write(row, 0, 'Thống kê tổng quan:', header_format)
        row += 1
        
        # Tạo bảng thống kê
        pages = self.df['page'].unique()
        headers = ['Trang', 'Số test', 'Trung bình (s)', 'Min (s)', 'Max (s)', 'Std (s)']
        
        for i, header in enumerate(headers):
            worksheet.write(row, i, header, header_format)
        row += 1
        
        for page in pages:
            page_data = self.df[self.df['page'] == page]['selenium_load_time']
            worksheet.write(row, 0, page, data_format)
            worksheet.write(row, 1, len(page_data), data_format)
            worksheet.write(row, 2, page_data.mean(), number_format)
            worksheet.write(row, 3, page_data.min(), number_format)
            worksheet.write(row, 4, page_data.max(), number_format)
            worksheet.write(row, 5, page_data.std(), number_format)
            row += 1
        
        # Điều chỉnh độ rộng cột
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:H', 15)
    
    def _create_raw_data_sheet(self, writer, header_format, data_format, number_format):
        """Tạo sheet dữ liệu raw"""
        # Chuẩn bị dataframe
        display_df = self.df.copy()
        if 'timestamp' in display_df.columns:
            display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Ghi vào Excel
        display_df.to_excel(writer, sheet_name='Dữ liệu Raw', index=False, startrow=1)
        
        # Format headers
        worksheet = writer.sheets['Dữ liệu Raw']
        for col_num, header in enumerate(display_df.columns):
            worksheet.write(1, col_num, header, header_format)
    
    def _create_page_statistics_sheet(self, writer, header_format, data_format, number_format):
        """Tạo sheet thống kê theo trang"""
        page_stats = []
        
        for page in self.df['page'].unique():
            page_data = self.df[self.df['page'] == page]
            
            stats = {
                'Trang': page,
                'URL': page_data['url'].iloc[0] if 'url' in page_data.columns else '',
                'Số test': len(page_data),
                'Selenium Load Time (s)': {
                    'Trung bình': page_data['selenium_load_time'].mean(),
                    'Min': page_data['selenium_load_time'].min(),
                    'Max': page_data['selenium_load_time'].max(),
                    'Std': page_data['selenium_load_time'].std(),
                    'P50': page_data['selenium_load_time'].quantile(0.5),
                    'P90': page_data['selenium_load_time'].quantile(0.9),
                    'P95': page_data['selenium_load_time'].quantile(0.95),
                    'P99': page_data['selenium_load_time'].quantile(0.99)
                }
            }
            
            if 'dom_ready_time' in page_data.columns:
                stats['DOM Ready Time (s)'] = {
                    'Trung bình': page_data['dom_ready_time'].mean(),
                    'Min': page_data['dom_ready_time'].min(),
                    'Max': page_data['dom_ready_time'].max(),
                    'Std': page_data['dom_ready_time'].std()
                }
            
            page_stats.append(stats)
        
        # Tạo DataFrame từ stats
        rows = []
        for stat in page_stats:
            base_row = {
                'Trang': stat['Trang'],
                'URL': stat['URL'],
                'Số test': stat['Số test']
            }
            
            # Thêm Selenium stats
            sel_stats = stat['Selenium Load Time (s)']
            for key, value in sel_stats.items():
                base_row[f'Selenium_{key}'] = value
            
            # Thêm DOM stats nếu có
            if 'DOM Ready Time (s)' in stat:
                dom_stats = stat['DOM Ready Time (s)']
                for key, value in dom_stats.items():
                    base_row[f'DOM_{key}'] = value
            
            rows.append(base_row)
        
        stats_df = pd.DataFrame(rows)
        stats_df.to_excel(writer, sheet_name='Thống kê theo trang', index=False, startrow=1)
        
        # Format
        worksheet = writer.sheets['Thống kê theo trang']
        for col_num, header in enumerate(stats_df.columns):
            worksheet.write(1, col_num, header, header_format)
    
    def _create_user_statistics_sheet(self, writer, header_format, data_format, number_format):
        """Tạo sheet thống kê theo user"""
        if 'username' not in self.df.columns:
            return
        
        user_stats = []
        for username in self.df['username'].unique():
            user_data = self.df[self.df['username'] == username]
            
            stats = {
                'Username': username,
                'Tổng số test': len(user_data),
                'Thời gian trung bình': user_data['selenium_load_time'].mean(),
                'Thời gian min': user_data['selenium_load_time'].min(),
                'Thời gian max': user_data['selenium_load_time'].max(),
            }
            
            # Thống kê theo từng trang
            for page in user_data['page'].unique():
                page_data = user_data[user_data['page'] == page]
                stats[f'{page}_count'] = len(page_data)
                stats[f'{page}_avg'] = page_data['selenium_load_time'].mean()
            
            user_stats.append(stats)
        
        user_df = pd.DataFrame(user_stats)
        user_df.to_excel(writer, sheet_name='Thống kê theo User', index=False, startrow=1)
        
        # Format
        worksheet = writer.sheets['Thống kê theo User']
        for col_num, header in enumerate(user_df.columns):
            worksheet.write(1, col_num, header, header_format)
    
    def _create_performance_comparison_sheet(self, writer, header_format, data_format, number_format):
        """Tạo sheet so sánh hiệu năng"""
        worksheet = writer.book.add_worksheet('So sánh hiệu năng')
        
        row = 0
        worksheet.write(row, 0, 'PHÂN TÍCH SO SÁNH HIỆU NĂNG', header_format)
        row += 2
        
        # So sánh theo percentile
        worksheet.write(row, 0, 'Phân tích Percentile (giây):', header_format)
        row += 1
        
        percentiles = [50, 75, 90, 95, 99]
        headers = ['Trang'] + [f'P{p}' for p in percentiles]
        
        for i, header in enumerate(headers):
            worksheet.write(row, i, header, header_format)
        row += 1
        
        for page in self.df['page'].unique():
            page_data = self.df[self.df['page'] == page]['selenium_load_time']
            worksheet.write(row, 0, page, data_format)
            for i, p in enumerate(percentiles):
                worksheet.write(row, i+1, page_data.quantile(p/100), number_format)
            row += 1
        
        row += 2
        # Phân tích lỗi timeout (>30s)
        worksheet.write(row, 0, 'Phân tích Timeout (>30s):', header_format)
        row += 1
        
        timeout_headers = ['Trang', 'Tổng test', 'Timeout count', 'Timeout rate (%)']
        for i, header in enumerate(timeout_headers):
            worksheet.write(row, i, header, header_format)
        row += 1
        
        for page in self.df['page'].unique():
            page_data = self.df[self.df['page'] == page]
            total_tests = len(page_data)
            timeout_count = len(page_data[page_data['selenium_load_time'] > 30])
            timeout_rate = (timeout_count / total_tests * 100) if total_tests > 0 else 0
            
            worksheet.write(row, 0, page, data_format)
            worksheet.write(row, 1, total_tests, data_format)
            worksheet.write(row, 2, timeout_count, data_format)
            worksheet.write(row, 3, timeout_rate, number_format)
            row += 1
    
    def _create_charts_sheet(self, writer):
        """Tạo sheet chứa biểu đồ"""
        # Tạo biểu đồ bằng matplotlib và lưu vào Excel
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Biểu đồ 1: Box plot theo trang
        pages_data = [self.df[self.df['page'] == page]['selenium_load_time'].values for page in self.df['page'].unique()]
        ax1.boxplot(pages_data, labels=self.df['page'].unique())
        ax1.set_title('Phân bố thời gian load theo trang')
        ax1.set_ylabel('Thời gian (giây)')
        ax1.tick_params(axis='x', rotation=45)
        
        # Biểu đồ 2: Histogram tổng thể
        ax2.hist(self.df['selenium_load_time'], bins=50, alpha=0.7, edgecolor='black')
        ax2.set_title('Phân bố tần suất thời gian load')
        ax2.set_xlabel('Thời gian (giây)')
        ax2.set_ylabel('Tần suất')
        
        # Biểu đồ 3: Line chart theo thời gian (nếu có timestamp)
        if 'timestamp' in self.df.columns:
            df_sorted = self.df.sort_values('timestamp')
            ax3.plot(range(len(df_sorted)), df_sorted['selenium_load_time'], alpha=0.7)
            ax3.set_title('Thời gian load theo thứ tự test')
            ax3.set_xlabel('Thứ tự test')
            ax3.set_ylabel('Thời gian (giây)')
        
        # Biểu đồ 4: Comparison by page
        page_means = self.df.groupby('page')['selenium_load_time'].agg(['mean', 'std'])
        ax4.bar(page_means.index, page_means['mean'], yerr=page_means['std'], capsize=5)
        ax4.set_title('Thời gian trung bình theo trang (±std)')
        ax4.set_ylabel('Thời gian (giây)')
        ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Lưu biểu đồ vào buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        
        # Thêm vào Excel
        worksheet = writer.book.add_worksheet('Biểu đồ')
        worksheet.insert_image('A1', 'chart.png', {'image_data': img_buffer})
        
        plt.close()
    
    def _enhance_excel_with_charts(self, filename):
        """Thêm biểu đồ nâng cao bằng openpyxl"""
        try:
            # Code này sẽ được implement để thêm biểu đồ Excel native
            pass
        except Exception as e:
            logger.warning(f"Không thể thêm biểu đồ nâng cao: {e}")
    
    def generate_summary_text(self):
        """Tạo tóm tắt văn bản chi tiết"""
        summary = []
        summary.append("="*70)
        summary.append("BÁO CÁO HIỆU NĂNG ODOO LMS CHI TIẾT")
        summary.append("="*70)
        
        # Thông tin chung
        unique_users = self.df['username'].nunique() if 'username' in self.df.columns else 1
        summary.append(f"📊 Tổng quan:")
        summary.append(f"   • Số người dùng: {unique_users}")
        summary.append(f"   • Tổng số test: {len(self.df)}")
        summary.append(f"   • Concurrent users: {self.test_config.get('concurrent_users', 1)}")
        summary.append(f"   • Thời gian test: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append("")
        
        # Thống kê theo trang
        summary.append("📈 Thống kê theo trang:")
        for page in self.df['page'].unique():
            page_data = self.df[self.df['page'] == page]['selenium_load_time']
            summary.append(f"   🔸 {page.upper()}:")
            summary.append(f"      • Số test: {len(page_data)}")
            summary.append(f"      • Trung bình: {page_data.mean():.2f}s")
            summary.append(f"      • Min/Max: {page_data.min():.2f}s / {page_data.max():.2f}s")
            summary.append(f"      • P50/P90/P95: {page_data.quantile(0.5):.2f}s / {page_data.quantile(0.9):.2f}s / {page_data.quantile(0.95):.2f}s")
            
            # Phân tích timeout
            timeout_count = len(page_data[page_data > 30])
            if timeout_count > 0:
                summary.append(f"      ⚠️  Timeout (>30s): {timeout_count} test ({timeout_count/len(page_data)*100:.1f}%)")
            summary.append("")
        
        # Top users chậm nhất (nếu có)
        if 'username' in self.df.columns and unique_users > 1:
            summary.append("👥 Top 10 users chậm nhất (trung bình):")
            user_avg = self.df.groupby('username')['selenium_load_time'].mean().sort_values(ascending=False).head(10)
            for i, (username, avg_time) in enumerate(user_avg.items(), 1):
                summary.append(f"   {i:2d}. {username}: {avg_time:.2f}s")
            summary.append("")
        
        # Khuyến nghị
        summary.append("💡 Khuyến nghị:")
        overall_avg = self.df['selenium_load_time'].mean()
        if overall_avg > 10:
            summary.append("   ⚠️  Hiệu năng kém - thời gian load trung bình > 10s")
            summary.append("   📝 Cần tối ưu hóa server, database, hoặc giảm concurrent users")
        elif overall_avg > 5:
            summary.append("   ⚡ Hiệu năng trung bình - có thể cải thiện")
            summary.append("   📝 Xem xét tối ưu hóa caching và static files")
        else:
            summary.append("   ✅ Hiệu năng tốt!")
        
        summary.append("="*70)
        
        return "\n".join(summary)

# Biến global để lưu tester instance và track completed users
global_tester = None
completed_users = 0
is_interrupted = False

def signal_handler(signum, frame):
    """Xử lý tín hiệu Ctrl+C"""
    global global_tester, completed_users, is_interrupted
    
    logger.warning("\n🛑 Nhận tín hiệu dừng (Ctrl+C)...")
    is_interrupted = True
    
    if global_tester and completed_users > 0:
        logger.info(f"📊 Phát hiện {completed_users} người dùng đã hoàn thành test")
        logger.info("🔄 Đang tự động xuất báo cáo trước khi tắt...")
        
        try:
            # Lưu kết quả hiện tại
            if global_tester.concurrent_users == 1 and len(global_tester.accounts) > 1:
                filename = f"performance_results_sequential_{len(global_tester.accounts)}users_interrupted.json"
                report_name = f"performance_report_sequential_{len(global_tester.accounts)}users_interrupted"
            else:
                filename = f"performance_results_{global_tester.concurrent_users}users_interrupted.json"
                report_name = f"performance_report_{global_tester.concurrent_users}users_interrupted"
                
            global_tester.save_results(filename)
            logger.info(f"✅ Đã lưu kết quả: {filename}")
            
            # Tạo báo cáo
            global_tester.create_performance_report(report_name)
            logger.info(f"✅ Đã tạo báo cáo: {report_name}")
            
            # In tóm tắt
            global_tester.print_summary()
            
        except Exception as e:
            logger.error(f"❌ Lỗi khi xuất báo cáo: {e}")
    else:
        if not global_tester:
            logger.warning("⚠️  Chưa có dữ liệu test nào")
        else:
            logger.warning(f"⚠️  Chưa có người dùng nào hoàn thành test ({completed_users} users)")
        logger.info("🚫 Bỏ qua xuất báo cáo")
    
    logger.info("👋 Đang tắt chương trình...")
    sys.exit(0)

def main():
    """Hàm main để chạy test"""
    global global_tester, completed_users
    
    # Đăng ký signal handler cho Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("Bắt đầu test hiệu năng Odoo LMS")
    logger.info("💡 Nhấn Ctrl+C để dừng và tự động xuất báo cáo (nếu có user hoàn thành)")
    
    try:
        tester = OdooPerformanceTest()
        global_tester = tester  # Lưu reference cho signal handler
        completed_users = 0     # Reset counter
        
        logger.info("Dọn dẹp các process Chrome cũ...")
        tester.cleanup_chrome_processes()
        time.sleep(2) 
        
        # Hiển thị cấu hình hiện tại
        logger.info(f"Cấu hình: {tester.concurrent_users} người học cùng lúc")
        logger.info(f"Danh sách tài khoản: {[acc[0] for acc in tester.accounts]}")
        
        if len(tester.accounts) == 1 or tester.concurrent_users == 1:
            if len(tester.accounts) == 1:
                # Chỉ có 1 tài khoản -> dùng single user mode
                logger.info("Chế độ SINGLE USER (chỉ có 1 tài khoản)")
                tester.username, tester.password = tester.accounts[0]
                tester.run_performance_test(num_iterations=tester.num_iterations)
                completed_users = 1  # Single user hoàn thành
            else:
                # Có nhiều tài khoản nhưng concurrent_users = 1 -> test lần lượt
                logger.info("Chế độ LẦN LƯỢT TỪNG NGƯỜI")
                tester.run_multiple_users_test()
        else:
            # Chế độ nhiều người cùng lúc
            logger.info(f"Chế độ ĐỒNG THỜI - {tester.concurrent_users} người cùng lúc")
            tester.run_multiple_users_test()
        
        # Nếu chương trình chạy đến đây mà không bị interrupt
        if not is_interrupted:
            # Lưu kết quả
            if tester.concurrent_users == 1 and len(tester.accounts) > 1:
                filename = f"performance_results_sequential_{len(tester.accounts)}users.json"
            else:
                filename = f"performance_results_{tester.concurrent_users}users.json"
            tester.save_results(filename)
            
            # In tóm tắt
            tester.print_summary()
            
            # Tạo báo cáo chi tiết
            logger.info("Tạo báo cáo hiệu năng chi tiết...")
            if tester.concurrent_users == 1 and len(tester.accounts) > 1:
                report_name = f"performance_report_sequential_{len(tester.accounts)}users"
            else:
                report_name = f"performance_report_{tester.concurrent_users}users"
            
            tester.create_performance_report(report_name)
            
            logger.info("Test hoàn thành!")
        
    except KeyboardInterrupt:
        # Này sẽ được handle bởi signal_handler
        pass
    except Exception as e:
        logger.error(f"Lỗi không mong muốn: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main()) 