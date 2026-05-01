## Cách xem models Lab 2:

### 1. Clone project về máy

```bash
git clone https://github.com/kieuphat159/Geo3d_Lab2.git
```

**Lưu ý:** File `toa-b4-ktx-khu-b.json` khá lớn, nên việc clone có thể hơi lâu. Hãy kiên nhẫn đợi đến khi terminal hoàn thành rồi tiếp tục.

### 2. Vào thư mục chứa index.html

```bash
cd Geo3d_Lab2/Geo3d_Lab2
```

### 3. Mở file trên browser và xem các models

- Dùng `live server` để mở file index.html
- Dùng chuột trái để kéo/di chuyển bản đồ
- Dùng chuột phải để xoay camera.

### 4. Chi tiết các file JSON theo từng tòa nhà

| STT | Tên model hiển thị | File JSON | Kinh độ (lng) | Vĩ độ (lat) | Scale | Ghi chú |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | BK | `bk.json` | 106.80250000000001 | 10.879000000000001 | 0.001 | Khu BK, model nhỏ nên scale thấp |
| 2 | UIT-E | `uit-e.json` | 106.80265000000001 | 10.869900000000001 | 0.02 | Tòa E của UIT |
| 3 | NongLam-CatTuong | `nonglam-cat-tuong.json` | 106.79026 | 10.87337 | 0.0008 | Khu Nông Lâm, cụm Cát Tường |
| 4 | KHTN | `khtn.json` | 106.79508 | 10.87961 | 0.0227 | Model có tinh chỉnh ánh sáng riêng |
| 5 | NongLam-HuongDuong | `nonglam-huong-duong.json` | 106.79026 | 10.87366 | 0.0008 | Khu Nông Lâm, cụm Hướng Dương |
| 6 | VienKhoaHocSucKhoe | `vien-khoa-hoc-suc-khoe.json` | 106.78958 | 10.87196 | 0.031 | Viện Khoa Học Sức Khỏe |
| 7 | Đại học Nông Lâm giảng đường B | `nong-lam-giang-duong-b.json` | 106.78934 | 10.87277 | 0.037 | Giảng đường B - ĐH Nông Lâm |
| 8 | Tòa B4 KTX Khu B | `toa-b4-ktx-khu-b.json` | 106.78309 | 10.88278 | 10 | File lớn, dữ liệu mô hình dày |

> Nguồn thông số được lấy trực tiếp từ `MODEL_LIST` trong `Geo3d_Lab2/index.html`.
