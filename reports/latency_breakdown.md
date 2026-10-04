# Báo cáo thời gian từng bước — Lab 18

**Nguồn:** reports/integration_after_m5_fix.log  
**Phạm vi:** main.py, gồm baseline và Production sau khi sửa prompt M5.

| Bước | Thời gian (giây) | Nội dung đo |
|---|---:|---|
| M1 — Đọc tài liệu và cắt đoạn | 0.0 | 26 tài liệu, 121 đoạn con |
| M5 — Làm giàu văn bản | 400.4 | Một lần gọi API cho mỗi đoạn |
| M2 — Lập chỉ mục | 70.2 | BM25, nạp encoder và tạo embedding |
| Khởi tạo đối tượng reranker | 0,0 | Chưa bao gồm nạp trọng số và predict |
| M4 — RAGAS Production | 35.8 | Bốn metric cho 20 câu |
| Các phần còn lại chưa đo riêng | 470.7 | Preflight, baseline, truy vấn Production, nạp reranker, synthesis và I/O |
| **Tổng main.py** | **977.1** | Khoảng 16.3 phút |

Phần còn lại được tính từ tổng trừ các bước đã đo riêng, chưa phải phép đo độc lập từng thao tác. Các giá trị được làm tròn theo log. Thời gian cắt đoạn 0,0 giây chỉ có nghĩa thấp hơn độ chính xác hiển thị, không có nghĩa thao tác không tốn thời gian.

Enrichment là bước lớn nhất trong các bước đo riêng. Em sẽ lưu lại kết quả để chỉ gọi API khi dữ liệu hoặc prompt thay đổi. Với embedding và reranking, cần đo riêng thời gian nạp lần đầu và thời gian xử lý khi mô hình đã sẵn sàng trước khi chọn cách tối ưu.


