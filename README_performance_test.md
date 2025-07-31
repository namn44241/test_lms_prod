# Test Hiệu Năng Odoo LMS với Selenium

## Mô tả
Bộ script này dùng để test hiệu năng các trang web của Odoo LMS bằng Selenium WebDriver với hỗ trợ test đồng thời nhiều người dùng.

## Quy trình test
1. **Đăng nhập**: Tự động đăng nhập vào hệ thống với các tài khoản từ file Excel
2. **Test trang slides chính**: Đo hiệu năng trang `/slides`
3. **Test trang khóa học**: Đo hiệu năng trang khóa học cụ thể
4. **Test học liệu với video**: Đo hiệu năng trang học liệu và xem video hoàn chỉnh

## Hướng dẫn chạy (5 bước)

### Bước 1: Tạo và kích hoạt môi trường ảo
```bash
# Tạo môi trường ảo
python -m venv venv 
hoặc
python3 -m venv venv 

# Kích hoạt môi trường ảo (Linux/Mac - WSL)
source venv/bin/activate

# Kích hoạt môi trường ảo (Windows)
venv\Scripts\activate
```

### Bước 2: Cài đặt thư viện (chỉ cần chạy lần đầu)
```bash
pip install -r req.txt
```

### Bước 3: Kiểm tra môi trường
```bash
python check_environment.py
```
hoặc
```bash
python3 check_environment.py
```

### Bước 4: Chạy test hiệu năng

# window
```bash
python performance_test_win.py
```
hoặc
```bash
python3 performance_test_win.py
```

#linux - wsl
```bash
python performance_test.py
```
hoặc
```bash
python3 performance_test.py
```

### Bước 5: Xem kết quả
Sau khi test hoàn thành, các file kết quả sẽ được tạo:
- `performance_results_50users.json`: Kết quả chi tiết dạng JSON
- `performance_report_50users.xlsx`: Báo cáo Excel với biểu đồ và thống kê
- `performance_report_50users_summary.txt`: Tóm tắt kết quả dạng văn bản
- `performance_test.log`: Log chi tiết quá trình test

## Cấu hình

### Thay đổi số người dùng đồng thời
Sửa file `performance_test.py`, dòng 31:
```python
concurrent_users = 50  # Thay đổi số này, nên chọn từ 5->!5
```

### Thay đổi URL server
Sửa file `performance_test.py`, dòng 479:
```python
self.base_url = "http://192.168.30.176:8017"  # Thay đổi URL này
```

### Thay đổi file danh sách tài khoản
Sửa file `performance_test.py`, dòng 484:
```python
df = pd.read_excel("Người dùng (res.users) (1).xlsx", engine='openpyxl')
```

## Kết quả đo

Script đo các loại thời gian:
1. **Selenium Load Time**: Thời gian từ khi bắt đầu tải trang đến khi element xuất hiện
2. **DOM Ready Time**: Thời gian DOM sẵn sàng
3. **Full Load Time**: Thời gian tải hoàn toàn
4. **Video Watch Time**: Thời gian xem video (cho trang học liệu)

## Chế độ chạy

### Chế độ đồng thời (mặc định)
- Nhiều người dùng test cùng lúc
- Số lượng được cấu hình bởi `concurrent_users`

### Chế độ lần lượt
- Đặt `concurrent_users = 1`
- Test từng người một cách tuần tự

## Troubleshooting

### Lỗi "Driver not found"
- Đảm bảo file `chromedriver` có trong thư mục
- Kiểm tra quyền thực thi: `chmod +x chromedriver`

### Lỗi kết nối server
- Kiểm tra server có đang chạy không
- Kiểm tra URL và port có đúng không
- Kiểm tra firewall/network

### Lỗi file Excel
- Đảm bảo file `Người dùng (res.users) (1).xlsx` tồn tại
- Kiểm tra cột `login` có trong file Excel

### Performance chậm
- Giảm số `concurrent_users`
- Tăng thời gian nghỉ giữa các test
- Kiểm tra tài nguyên server

## Files quan trọng

- `performance_test.py`: Script chính
- `req.txt`: Danh sách thư viện cần thiết
- `chromedriver`: WebDriver cho Chrome
- `check_environment.py`: Script kiểm tra môi trường 