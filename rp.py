from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, SessionNotCreatedException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import threading
import time
import random
import os
import signal
import sys
import json
from queue import Queue

class FacebookReportBot:
    def __init__(self, cookie, links, driver_id):
        self.cookie = cookie
        self.links = links
        self.driver_id = driver_id
        self.driver = None
        self.running = True
        self.service = None
        
    def setup_driver(self):
        """Khởi tạo driver với webdriver_manager tự động tải đúng phiên bản"""
        try:
            print(f"[Driver {self.driver_id}] Đang cài đặt ChromeDriver phù hợp...")
            
            # Cấu hình Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_argument('--disable-features=TranslateUI')
            chrome_options.add_argument('--remote-debugging-port=0')
            
            # Thêm user-agent
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Tự động tải ChromeDriver phù hợp với phiên bản Chrome hiện tại
            try:
                # Thử với ChromeDriverManager
                chrome_driver_path = ChromeDriverManager().install()
                self.service = Service(chrome_driver_path)
                print(f"[Driver {self.driver_id}] Đã tải ChromeDriver tại: {chrome_driver_path}")
            except Exception as e:
                print(f"[Driver {self.driver_id}] Lỗi tải ChromeDriver, thử phương pháp khác: {str(e)}")
                # Fallback: để Selenium tự tìm
                self.service = None
            
            # Khởi tạo driver
            if self.service:
                self.driver = webdriver.Chrome(service=self.service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
            
            # Ẩn dấu hiệu automation
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print(f"[Driver {self.driver_id}] Khởi tạo thành công")
            return True
            
        except SessionNotCreatedException as e:
            print(f"[Driver {self.driver_id}] Lỗi phiên bản ChromeDriver, đang thử phương pháp khác...")
            return self.setup_driver_fallback()
        except Exception as e:
            print(f"[Driver {self.driver_id}] Lỗi khởi tạo: {str(e)}")
            return self.setup_driver_fallback()
    
    def setup_driver_fallback(self):
        """Phương pháp dự phòng nếu webdriver_manager không hoạt động"""
        try:
            print(f"[Driver {self.driver_id}] Đang thử phương pháp dự phòng...")
            
            chrome_options = Options()
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Thử với phiên bản mặc định
            self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print(f"[Driver {self.driver_id}] Khởi tạo thành công với phương pháp dự phòng")
            return True
        except Exception as e:
            print(f"[Driver {self.driver_id}] Lỗi khởi tạo dự phòng: {str(e)}")
            return False
    
    def add_cookie(self):
        """Thêm cookie vào driver"""
        try:
            if not self.cookie:
                print(f"[Driver {self.driver_id}] Không có cookie, bỏ qua")
                return True
                
            # Đợi trang load
            time.sleep(5)
            
            # Parse cookie từ string
            cookie_parts = self.cookie.split(';')
            for part in cookie_parts:
                if '=' in part:
                    name, value = part.strip().split('=', 1)
                    cookie_dict = {
                        'name': name,
                        'value': value,
                        'domain': '.facebook.com',
                        'path': '/',
                    }
                    try:
                        self.driver.add_cookie(cookie_dict)
                    except:
                        continue
            
            print(f"[Driver {self.driver_id}] Đã thêm cookie")
            return True
        except Exception as e:
            print(f"[Driver {self.driver_id}] Lỗi thêm cookie: {str(e)}")
            return False
    
    def quick_click(self, by, value, timeout=3, description=""):
        """Click nhanh, không chờ lâu, tự động bỏ qua nếu không tìm thấy"""
        try:
            # Chỉ chờ trong thời gian ngắn
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            
            # Scroll nhanh
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.3)
            
            # Click
            try:
                element.click()
            except:
                self.driver.execute_script("arguments[0].click();", element)
            
            print(f"[Driver {self.driver_id}] Đã click: {description}")
            return True
        except:
            # Không in log cho optional elements để tránh rác
            return False
    
    def safe_click(self, by, value, timeout=10, description="", required=True):
        """Click an toàn, required=True thì mới chờ lâu và retry"""
        if not required:
            # Nếu không bắt buộc, click nhanh và bỏ qua nếu không có
            return self.quick_click(by, value, timeout=2, description=description)
        
        # Nếu bắt buộc, mới chờ lâu và retry
        for attempt in range(2):  # Chỉ retry 2 lần cho required
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((by, value))
                )
                
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.5)
                
                try:
                    element.click()
                except:
                    self.driver.execute_script("arguments[0].click();", element)
                
                time.sleep(1)
                print(f"[Driver {self.driver_id}] Đã click: {description}")
                return True
                
            except TimeoutException:
                if attempt == 0:
                    print(f"[Driver {self.driver_id}] Chờ {description}...")
                    time.sleep(2)
                else:
                    print(f"[Driver {self.driver_id}] Không tìm thấy {description}")
            except Exception as e:
                if attempt == 0:
                    print(f"[Driver {self.driver_id}] Lỗi click {description}: {str(e)}")
                    time.sleep(2)
        
        return False
    
    def quick_send_keys(self, by, value, text, timeout=2, description=""):
        """Nhập text nhanh, tự động bỏ qua nếu không tìm thấy"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            element.clear()
            element.send_keys(text)
            time.sleep(0.5)
            print(f"[Driver {self.driver_id}] Đã nhập: {description}")
            return True
        except:
            return False
    
    def click_if_exists(self, by_value_pairs):
        """Click nhiều element theo thứ tự, chỉ dừng khi click được element đầu tiên"""
        for by, value, description in by_value_pairs:
            if self.quick_click(by, value, timeout=1, description=description):
                return True
        return False
    
    def click_input_container_and_type(self, text, description=""):
        """
        Click vào container DIV chứa label và input để kích hoạt form,
        sau đó nhập text vào input bằng nativeInputValueSetter (hiệu quả nhất cho Facebook)
        """
        try:
            # Các selector cho container DIV
            container_selectors = [
                # Container chính có chứa label và input
                (By.CSS_SELECTOR, "div.x11lwdb5.xfxe0gy.x1szzd0g.xh2argp"),
                (By.CSS_SELECTOR, "div.x78zum5.xdt5ytf.x6ikm8r.x10wlt62"),
                (By.XPATH, "//div[contains(@class, 'x11lwdb5') and contains(@class, 'xfxe0gy')]"),
                (By.XPATH, "//div[.//span[contains(text(),'Facebook Page')]]"),
                (By.XPATH, "//div[.//span[contains(text(),'Page name')]]"),
                (By.XPATH, "//div[.//label]//span[contains(text(),'Facebook')]/ancestor::div[contains(@class, 'x11lwdb5')]")
            ]
            
            clicked = False
            container_element = None
            
            # Thử click vào container
            for by, value in container_selectors:
                try:
                    elements = self.driver.find_elements(by, value)
                    for element in elements:
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(0.3)
                            element.click()
                            print(f"[Driver {self.driver_id}] Đã click vào container input")
                            clicked = True
                            container_element = element
                            break
                        except:
                            continue
                    if clicked:
                        break
                except:
                    continue
            
            if not clicked:
                # Thử click vào span
                span_selectors = [
                    (By.XPATH, "//span[contains(text(),'Facebook Page name or URL')]"),
                    (By.XPATH, "//span[contains(text(),'Page name or URL')]"),
                    (By.CSS_SELECTOR, "span.x1jchvi3.x1fcty0u.x132q4wb")
                ]
                for by, value in span_selectors:
                    if self.quick_click(by, value, timeout=2, description="Click span"):
                        clicked = True
                        break
            
            if not clicked:
                # Thử click vào label
                try:
                    label = self.driver.find_element(By.CSS_SELECTOR, "label.x78zum5.xh8yej3")
                    label.click()
                    clicked = True
                except:
                    pass
            
            time.sleep(1.5)  # Đợi input hiện ra và kích hoạt
            
            # NHẬP TEXT BẰNG NATIVEINPUTVALUESETTER - PHƯƠNG PHÁP TỐI ƯU CHO FACEBOOK
            js_code = f"""
            // Tìm input theo nhiều cách
            var input = null;
            
            // Cách 1: Theo aria-label
            input = document.querySelector('input[aria-label="Facebook Page name or URL"]');
            if (!input) {{
                // Cách 2: Theo role combobox
                input = document.querySelector('input[role="combobox"]');
            }}
            if (!input) {{
                // Cách 3: Theo type search
                input = document.querySelector('input[type="search"]');
            }}
            if (!input) {{
                // Cách 4: Theo class
                input = document.querySelector('input.x1i10hfl.xggy1nq');
            }}
            if (!input) {{
                // Cách 5: Tìm tất cả input và lấy cái đầu tiên
                var inputs = document.querySelectorAll('input');
                for(var i=0; i<inputs.length; i++) {{
                    if(inputs[i].offsetParent !== null) {{ // Chỉ lấy input đang hiển thị
                        input = inputs[i];
                        break;
                    }}
                }}
            }}
            
            if (input) {{
                // Focus vào input
                input.focus();
                input.click();
                
                // Sử dụng nativeInputValueSetter để set value (hiệu quả nhất)
                var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype,
                    "value"
                ).set;
                
                nativeInputValueSetter.call(input, "{text}");
                
                // Dispatch events để Facebook nhận biết
                input.dispatchEvent(new Event("input", {{ bubbles: true }}));
                input.dispatchEvent(new Event("change", {{ bubbles: true }}));
                input.dispatchEvent(new Event("blur", {{ bubbles: true }}));
                
                return true;
            }}
            return false;
            """
            
            result = self.driver.execute_script(js_code)
            
            if result:
                print(f"[Driver {self.driver_id}] Đã nhập bằng nativeInputValueSetter: {description}")
                time.sleep(1)
                return True
            else:
                print(f"[Driver {self.driver_id}] Không tìm thấy input để nhập")
                return False
            
        except Exception as e:
            print(f"[Driver {self.driver_id}] Lỗi click container và nhập: {str(e)}")
            return False
    
    def execute_report_sequence(self, sequence_num):
        """Thực hiện sequence báo cáo với xử lý siêu linh hoạt và nhanh"""
        
        # Click vào nút settings (bắt buộc)
        if not self.safe_click(By.CSS_SELECTOR, '[aria-label="Profile settings see more options"]', 
                               timeout=8, description="Profile settings", required=True):
            return False
        
        time.sleep(0.5)
        
        # Click Report profile (bắt buộc)
        if not self.safe_click(By.XPATH, "//span[text()='Report profile']", 
                               timeout=8, description="Report profile", required=True):
            return False
        
        time.sleep(0.5)
        
        # Click "Something about this profile" (không bắt buộc) - thử cả text và class
        self.click_if_exists([
            (By.XPATH, "//span[text()='Something about this profile']", "Something about this profile"),
            (By.CSS_SELECTOR, "span.x193iq5w.xeuugli.x13faqbe.x1vvkbs", "Something about this profile (class)")
        ])
        
        time.sleep(0.5)
        
        # Hàm click tất cả các nút submit/next/done theo thứ tự
        def click_all_buttons():
            """Click tất cả các nút theo thứ tự: Submit -> Next -> Done"""
            # Thử click Submit
            if self.quick_click(By.XPATH, "//span[contains(text(),'Submit')]", timeout=2, description="Submit"):
                time.sleep(0.5)
            
            # Thử click Next
            if self.quick_click(By.XPATH, "//span[contains(text(),'Next')]", timeout=2, description="Next"):
                time.sleep(0.5)
            
            # Thử click Done
            if self.quick_click(By.XPATH, "//span[contains(text(),'Done')]", timeout=2, description="Done"):
                time.sleep(0.5)
            
            # Thử các selector dự phòng cho Submit
            if self.quick_click(By.XPATH, "//div[@role='button']//span[contains(text(),'Submit')]", timeout=1, description="Submit (div)"):
                time.sleep(0.5)
            
            # Thử các selector dự phòng cho Next
            if self.quick_click(By.XPATH, "//div[@role='button']//span[contains(text(),'Next')]", timeout=1, description="Next (div)"):
                time.sleep(0.5)
            
            # Thử các selector dự phòng cho Done
            if self.quick_click(By.XPATH, "//div[@role='button']//span[contains(text(),'Done')]", timeout=1, description="Done (div)"):
                time.sleep(0.5)
        
        # Hàm click cho sequence 11 và 13: Next -> Submit -> Next -> Done
        def click_sequence_11_13():
            """Click theo thứ tự: Next -> Submit -> Next -> Done"""
            # Next lần 1
            if self.quick_click(By.XPATH, "//span[contains(text(),'Next')]", timeout=2, description="Next 1"):
                time.sleep(0.5)
            
            # Submit
            if self.quick_click(By.XPATH, "//span[contains(text(),'Submit')]", timeout=2, description="Submit"):
                time.sleep(0.5)
            elif self.quick_click(By.XPATH, "//div[@role='button']//span[contains(text(),'Submit')]", timeout=1, description="Submit (div)"):
                time.sleep(0.5)
            
            # Next lần 2
            if self.quick_click(By.XPATH, "//span[contains(text(),'Next')]", timeout=2, description="Next 2"):
                time.sleep(0.5)
            elif self.quick_click(By.XPATH, "//div[@role='button']//span[contains(text(),'Next')]", timeout=1, description="Next 2 (div)"):
                time.sleep(0.5)
            
            # Done
            if self.quick_click(By.XPATH, "//span[contains(text(),'Done')]", timeout=2, description="Done"):
                time.sleep(0.5)
            elif self.quick_click(By.XPATH, "//div[@role='button']//span[contains(text(),'Done')]", timeout=1, description="Done (div)"):
                time.sleep(0.5)
        
        # Các sequence khác nhau
        if sequence_num == 1:  # Fake profile - Me
            if not self.safe_click(By.XPATH, "//span[text()='Fake profile']", 
                                   timeout=5, description="Fake profile", required=True):
                return False
            time.sleep(0.5)
            
            self.safe_click(By.XPATH, "//span[text()='Me']", 
                           timeout=5, description="Me", required=True)
            time.sleep(0.5)
            
            # Click tất cả các nút
            click_all_buttons()
                
        elif sequence_num == 2:  # Fake profile - They're not a real person
            if not self.safe_click(By.XPATH, "//span[text()='Fake profile']", 
                                   timeout=5, description="Fake profile", required=True):
                return False
            time.sleep(0.5)
            
            self.safe_click(By.XPATH, "//span[text()='They’re not a real person']", 
                           timeout=5, description="They're not a real person", required=True)
            time.sleep(0.5)
            
            # Click tất cả các nút
            click_all_buttons()
                
        elif sequence_num == 3:  # Scam, fraud - Fraud or scam
            if not self.safe_click(By.XPATH, "//span[text()='Scam, fraud or false information']", 
                                   timeout=5, description="Scam, fraud", required=True):
                return False
            time.sleep(0.5)
            
            self.safe_click(By.XPATH, "//span[text()='Fraud or scam']", 
                           timeout=5, description="Fraud or scam", required=True)
            time.sleep(0.5)
            
            # Click tất cả các nút
            click_all_buttons()
                
        elif sequence_num == 4:  # Scam, fraud - Spam
            if not self.safe_click(By.XPATH, "//span[text()='Scam, fraud or false information']", 
                                   timeout=5, description="Scam, fraud", required=True):
                return False
            time.sleep(0.5)
            
            self.safe_click(By.XPATH, "//span[text()='Spam']", 
                           timeout=5, description="Spam", required=True)
            time.sleep(0.5)
            
            # Click tất cả các nút
            click_all_buttons()
                
        elif sequence_num == 5:  # Scam, fraud - Sharing false information
            if not self.safe_click(By.XPATH, "//span[text()='Scam, fraud or false information']", 
                                   timeout=5, description="Scam, fraud", required=True):
                return False
            time.sleep(0.5)
            
            self.safe_click(By.XPATH, "//span[text()='Sharing false information']", 
                           timeout=5, description="Sharing false information", required=True)
            time.sleep(0.5)
            
            # Click tất cả các nút
            click_all_buttons()
                
        elif sequence_num == 6:  # Something else
            if not self.safe_click(By.XPATH, "//span[text()='Something else']", 
                                   timeout=5, description="Something else", required=True):
                return False
            time.sleep(0.5)
            
            # Something else có thể chỉ có Done
            click_all_buttons()
                
        elif sequence_num == 7:  # Under 18 - Physical abuse
            if not self.safe_click(By.XPATH, "//span[text()='Problem involving someone under 18']", 
                                   timeout=5, description="Under 18", required=True):
                return False
            time.sleep(0.5)
            
            self.safe_click(By.XPATH, "//span[text()='Physical abuse']", 
                           timeout=5, description="Physical abuse", required=True)
            time.sleep(0.5)
            
            # Click tất cả các nút
            click_all_buttons()
                
        elif sequence_num == 8:  # Violent - Credible threat
            if not self.safe_click(By.XPATH, "//span[text()='Violent, hateful or disturbing content']", 
                                   timeout=5, description="Violent content", required=True):
                return False
            time.sleep(0.5)
            
            self.safe_click(By.XPATH, "//span[text()='Credible threat to safety']", 
                           timeout=5, description="Credible threat", required=True)
            time.sleep(0.5)
            
            # Click tất cả các nút
            click_all_buttons()
                
        elif sequence_num == 9:  # Violent - Terrorism
            if not self.safe_click(By.XPATH, "//span[text()='Violent, hateful or disturbing content']", 
                                   timeout=5, description="Violent content", required=True):
                return False
            time.sleep(0.5)
            
            self.safe_click(By.XPATH, "//span[text()='Seems like terrorism']", 
                           timeout=5, description="Terrorism", required=True)
            time.sleep(0.5)
            
            # Click tất cả các nút
            click_all_buttons()
                
        elif sequence_num == 10:  # Violent - Calling for violence
            if not self.safe_click(By.XPATH, "//span[text()='Violent, hateful or disturbing content']", 
                                   timeout=5, description="Violent content", required=True):
                return False
            time.sleep(0.5)
            
            self.safe_click(By.XPATH, "//span[text()='Calling for violence']", 
                           timeout=5, description="Calling for violence", required=True)
            time.sleep(0.5)
            
            # Click tất cả các nút
            click_all_buttons()
                
        elif sequence_num == 11:  # Fake profile - A celebrity - nhập text
            if not self.safe_click(By.XPATH, "//span[text()='Fake profile']", 
                                   timeout=5, description="Fake profile", required=True):
                return False
            time.sleep(0.5)
            
            self.safe_click(By.XPATH, "//span[text()='A celebrity or public figure']", 
                           timeout=5, description="A celebrity", required=True)
            time.sleep(0.5)
            
            # Click vào container DIV để kích hoạt form và nhập text
            self.click_input_container_and_type("Mark Zuckerberg", description="Nhập Mark Zuckerberg")
            
            time.sleep(2)
            
            # Click vào kết quả nếu có
            self.click_if_exists([
                (By.XPATH, "//span[contains(text(),'Mark Zuckerberg')]", "Chọn Mark Zuckerberg"),
                (By.XPATH, "//div[contains(text(),'Mark Zuckerberg')]", "Chọn Mark Zuckerberg (div)")
            ])
            
            time.sleep(0.5)
            
            # Click theo thứ tự đặc biệt cho sequence 11
            click_sequence_11_13()
            
            # Thử click submit lần 2 nếu còn
            self.quick_click(By.XPATH, "//span[contains(text(),'Submit')]", 
                           timeout=1, description="Submit 2")
                
        elif sequence_num == 12:  # Fake profile - Me (10 lần)
            if not self.safe_click(By.XPATH, "//span[text()='Fake profile']", 
                                   timeout=5, description="Fake profile", required=True):
                return False
            time.sleep(0.5)
            
            self.safe_click(By.XPATH, "//span[text()='Me']", 
                           timeout=5, description="Me", required=True)
            time.sleep(0.5)
            
            # Click tất cả các nút
            click_all_buttons()
                
        elif sequence_num == 13:  # Fake profile - A business - nhập text
            if not self.safe_click(By.XPATH, "//span[text()='Fake profile']", 
                                   timeout=5, description="Fake profile", required=True):
                return False
            time.sleep(0.5)
            
            self.safe_click(By.XPATH, "//span[text()='A business']", 
                           timeout=5, description="A business", required=True)
            time.sleep(0.5)
            
            # Click vào container DIV để kích hoạt form và nhập text
            self.click_input_container_and_type("Meta for Business", description="Nhập Meta for Business")
            
            time.sleep(2)
            
            # Click vào kết quả nếu có
            self.click_if_exists([
                (By.XPATH, "//span[contains(text(),'Meta for Business')]", "Chọn Meta for Business"),
                (By.XPATH, "//div[contains(text(),'Meta for Business')]", "Chọn Meta for Business (div)")
            ])
            
            time.sleep(0.5)
            
            # Click theo thứ tự đặc biệt cho sequence 13
            click_sequence_11_13()
            
            # Thử click submit lần 2 nếu còn
            self.quick_click(By.XPATH, "//span[contains(text(),'Submit')]", 
                           timeout=1, description="Submit 2")
                
        elif sequence_num == 14:  # Adult content - Threatening to share nude images
            if not self.safe_click(By.XPATH, "//span[text()='Adult content']", 
                                   timeout=5, description="Adult content", required=True):
                return False
            time.sleep(0.5)
            
            self.safe_click(By.XPATH, "//span[text()='Threatening to share my nude images']", 
                           timeout=5, description="Threatening to share nude", required=True)
            time.sleep(0.5)
            
            # Click tất cả các nút
            click_all_buttons()
                
        elif sequence_num == 15:  # Adult content - Nudity or sexual activity
            if not self.safe_click(By.XPATH, "//span[text()='Adult content']", 
                                   timeout=5, description="Adult content", required=True):
                return False
            time.sleep(0.5)
            
            self.safe_click(By.XPATH, "//span[text()='Nudity or sexual activity']", 
                           timeout=5, description="Nudity or sexual activity", required=True)
            time.sleep(0.5)
            
            # Click tất cả các nút
            click_all_buttons()
                
        elif sequence_num == 16:  # Selling animals
            if not self.safe_click(By.XPATH, "//span[text()='Selling or promoting restricted items']", 
                                   timeout=5, description="Selling restricted items", required=True):
                return False
            time.sleep(0.5)
            
            self.safe_click(By.XPATH, "//span[text()='Animals']", 
                           timeout=5, description="Animals", required=True)
            time.sleep(0.5)
            
            # Click tất cả các nút
            click_all_buttons()
        
        return True
    
    def run(self):
        """Chạy bot chính"""
        max_retries = 2
        retry_count = 0
        
        while retry_count < max_retries and self.running:
            try:
                if not self.setup_driver():
                    retry_count += 1
                    print(f"[Driver {self.driver_id}] Thử lại lần {retry_count}/{max_retries}")
                    time.sleep(3)
                    continue
                
                # Mở facebook
                print(f"[Driver {self.driver_id}] Đang mở Facebook...")
                self.driver.get("https://facebook.com")
                time.sleep(5)
                
                # Thêm cookie nếu có
                if self.cookie:
                    self.add_cookie()
                    self.driver.refresh()
                    time.sleep(4)
                
                # Danh sách sequence và số lần lặp
                sequences = [
                    (1, 5), (2, 5), (3, 5), (4, 5), (5, 5),
                    (6, 5), (7, 5), (8, 5), (9, 5), (10, 5),
                    (11, 5), (12, 10), (13, 5), (14, 5), (15, 5), (16, 8)
                ]
                
                cycle_count = 0
                
                while self.running:
                    cycle_count += 1
                    print(f"\n[Driver {self.driver_id}] === BẮT ĐẦU CYCLE {cycle_count} ===")
                    
                    for link_idx, link in enumerate(self.links):
                        print(f"[Driver {self.driver_id}] Mở link {link_idx+1}/{len(self.links)}")
                        
                        # Mở tab mới
                        self.driver.execute_script("window.open('');")
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        self.driver.get(link)
                        time.sleep(5)
                        
                        # Thực hiện các sequence
                        for seq_num, repeat_count in sequences:
                            for i in range(repeat_count):
                                if not self.running:
                                    break
                                    
                                print(f"[Driver {self.driver_id}] Seq {seq_num} lần {i+1}/{repeat_count}")
                                self.execute_report_sequence(seq_num)
                                time.sleep(random.uniform(2, 3))
                            
                            if not self.running:
                                break
                        
                        # Đóng tab
                        if len(self.driver.window_handles) > 1:
                            self.driver.close()
                            self.driver.switch_to.window(self.driver.window_handles[0])
                        time.sleep(3)
                    
                    print(f"[Driver {self.driver_id}] Cycle {cycle_count} xong")
                    time.sleep(5)
                
                break
                
            except Exception as e:
                retry_count += 1
                print(f"[Driver {self.driver_id}] Lỗi: {str(e)}")
                time.sleep(5)
                
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.driver = None
    
    def stop(self):
        self.running = False
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

def distribute_resources(cookies, links, num_drivers):
    """Phân phối cookie và link cho các driver"""
    driver_assignments = []
    
    if not cookies:
        cookies = [None]
    
    # Phân phối cookie
    cookie_assignments = []
    for i in range(num_drivers):
        cookie_idx = i % len(cookies)
        cookie_assignments.append(cookies[cookie_idx])
    
    # Phân phối link
    link_assignments = []
    if len(links) == 1:
        link_assignments = [links] * num_drivers
    else:
        for i in range(num_drivers):
            per_driver = len(links) // num_drivers
            remainder = len(links) % num_drivers
            start_idx = i * per_driver + min(i, remainder)
            end_idx = start_idx + per_driver + (1 if i < remainder else 0)
            
            if start_idx < len(links):
                link_assignments.append(links[start_idx:end_idx])
            else:
                link_assignments.append(links[:1])
    
    # Tạo assignments
    for i in range(num_drivers):
        driver_assignments.append({
            'cookie': cookie_assignments[i],
            'links': link_assignments[i] if i < len(link_assignments) else links[:1],
            'driver_id': i + 1
        })
    
    return driver_assignments

def signal_handler(signum, frame):
    print("\n\nĐang dừng tất cả driver...")
    for bot in bots:
        bot.stop()
    print("Đã dừng!")
    sys.exit(0)

bots = []

def main():
    global bots
    
    print("=" * 60)
    print("FACEBOOK REPORT BOT - SIÊU TỐC ĐỘ")
    print("=" * 60)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Nhập cookies
    cookies = []
    print("\nNHẬP COOKIE (enter trống để bỏ qua):")
    print("Định dạng: name=value; name2=value2; ...")
    while True:
        cookie = input(f"Cookie {len(cookies)+1}: ").strip()
        if not cookie:
            break
        cookies.append(cookie)
    
    # Nhập links
    links = []
    print("\nNHẬP LINK FACEBOOK:")
    print("Ví dụ: https://www.facebook.com/username")
    while True:
        link = input(f"Link {len(links)+1}: ").strip()
        if not link and len(links) >= 1:
            break
        if link:
            links.append(link)
        else:
            if len(links) == 0:
                print("Vui lòng nhập ít nhất 1 link")
                continue
            break
    
    # Nhập số driver
    while True:
        try:
            num_drivers = int(input("\nSố driver muốn mở: "))
            if num_drivers > 0:
                break
        except:
            print("Nhập số hợp lệ")
    
    print(f"\nĐã nhập: {len(cookies)} cookie, {len(links)} link, {num_drivers} driver")
    
    # Phân phối
    assignments = distribute_resources(cookies, links, num_drivers)
    
    print("\n=== PHÂN PHỐI TÀI NGUYÊN ===")
    for assign in assignments:
        cookie_info = f"Cookie {cookies.index(assign['cookie'])+1}" if assign['cookie'] and assign['cookie'] in cookies else "Không cookie"
        print(f"Driver {assign['driver_id']}: {cookie_info} - {len(assign['links'])} link")
        for i, link in enumerate(assign['links']):
            print(f"  ├─ Link {i+1}: {link[:50]}..." if len(link) > 50 else f"  ├─ Link {i+1}: {link}")
    
    # Khởi động
    bots = []
    threads = []
    
    for assign in assignments:
        print(f"\nKhởi động Driver {assign['driver_id']}...")
        bot = FacebookReportBot(assign['cookie'], assign['links'], assign['driver_id'])
        bots.append(bot)
        thread = threading.Thread(target=bot.run)
        thread.daemon = True
        threads.append(thread)
        thread.start()
        time.sleep(3)
    
    print("\n" + "=" * 60)
    print("✅ TẤT CẢ DRIVER ĐÃ KHỞI ĐỘNG - CHẠY VÔ HẠN")
    print("✅ ĐÃ SỬA LỖI NHẬP TEXT BẰNG NATIVEINPUTVALUESETTER")
    print("✅ Click vào container DIV chứa label để kích hoạt input")
    print("✅ ĐÃ FIX: Click tuần tự Submit → Next → Done cho các sequence thường")
    print("✅ ĐÃ FIX: Sequence 11 và 13: Next → Submit → Next → Done")
    print("✅ Giữ nguyên 'Something about this profile'")
    print("✅ Tự động bỏ qua element không tồn tại")
    print("✅ Không timeout làm chậm")
    print("✅ Nhấn Ctrl+C để dừng")
    print("=" * 60)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)

def install_requirements():
    """Cài đặt thư viện"""
    print("Đang kiểm tra thư viện...")
    try:
        import webdriver_manager
        print("✅ webdriver_manager đã cài")
    except:
        print("Đang cài webdriver_manager...")
        os.system("pip install webdriver-manager")
    
    try:
        import selenium
        print("✅ selenium đã cài")
    except:
        print("Đang cài selenium...")
        os.system("pip install selenium")

if __name__ == "__main__":
    install_requirements()
    main()