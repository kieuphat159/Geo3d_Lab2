# Geo3d_Lab3 — Hướng dẫn sử dụng

Hướng dẫn ngắn để chuyển model từ SketchUp sang JSON và dùng trong project này.

Các bước:

1. Tạo file model trong SketchUp với đuôi `.skp`.

2. Tạo tài khoản SketchUp Pro (bản trial 7 ngày), mở model và export sang định dạng `.obj`.

3. Giải nén (nếu cần) và thêm folder chứa file `.obj` vào repo, đúng cấp (cùng cấp với `index.html`).

4. Mở terminal trong thư mục chứa `obj_to_json_converter.py` và chạy:

   `py obj_to_json_converter.py`

   Lưu ý: script sẽ đọc các file `.obj` trong folder đã thêm và tạo ra file JSON tương ứng.

5. Thêm file `.json` mới tạo vào các template cần thiết trong `index.html` để load model lên web.

6. Chỉnh sửa tọa độ bằng GUI trên web.
   - Hiện tại chưa có cơ chế ghi đè tự động.
   - `index.html` sẽ reload ngay khi file thay đổi, nên hãy sao chép các tọa độ ra nơi khác trước khi ghi vào HTML.

