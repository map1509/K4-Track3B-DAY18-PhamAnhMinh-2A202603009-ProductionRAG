# Bài tự đánh giá — Lab 18: Production RAG

**Họ và tên:** Phạm Anh Minh  
**Khóa:** K4 - Track 3B  
**Ngày hoàn thành:** 04/10/2026

---

## Phần 1: Mapping bài giảng (Lecture Mapping)

Qua bài lab, em hiểu rõ hơn vai trò của từng tầng trong RAG. Tìm được đoạn văn gần với câu hỏi chưa đủ; hệ thống còn phải lấy đúng phiên bản tài liệu và đủ thông tin để trả lời tất cả các ý.

| Khái niệm trong bài giảng | Module | Hàm cụ thể | Quan sát và phân tích |
|---|---|---|---|
| Cắt đoạn theo ngữ nghĩa | M1 | `chunk_semantic()` | Hàm mã hóa câu bằng all-MiniLM-L6-v2 và ngắt đoạn khi độ tương đồng giữa hai câu liên tiếp dưới 0,85. Em cũng triển khai `chunk_hierarchical()` để tìm trên đoạn con và gửi đoạn cha cho LLM, cùng `chunk_structure_aware()` để giữ nội dung theo tiêu đề Markdown. |
| Kết hợp BM25 và tìm kiếm vector | M2 | `segment_vietnamese()`, `reciprocal_rank_fusion()` | BM25 hỗ trợ tìm từ khóa và số liệu, còn vector hỗ trợ tìm theo nghĩa. RRF kết hợp thứ hạng của hai nguồn. Cần đổi dấu gạch dưới do underthesea tạo ra thành khoảng trắng và chuẩn hóa chữ thường ở cả tài liệu lẫn truy vấn. |
| Xếp hạng lại bằng Cross-Encoder | M3 | `CrossEncoderReranker.rerank()` | Mô hình bge-reranker-v2-m3 đọc cả câu hỏi và đoạn văn, chấm lại các ứng viên rồi chọn top-3. Kiểm thử với mô hình thật cho thấy đoạn phù hợp được đưa lên đầu. Em chưa đo riêng độ trễ nên chưa thể kết luận đạt mục tiêu dưới 150 ms. |
| Đánh giá bằng bốn chỉ số RAGAS | M4 | `evaluate_ragas()`, `failure_analysis()` | Sau khi sửa prompt M5 và chạy lại API, Production đạt faithfulness 0.7775; answer relevancy 0.7119; context precision 0.9750; context recall 0.9250. Cả bốn tăng so với baseline cùng phiên, nhưng độ liên quan chưa đạt 0,75. Em vẫn cần đọc từng câu, nhất là các câu từ chối khi ngữ cảnh đã có đáp án. |
| Làm giàu văn bản trước khi tạo embedding | M5 | `contextual_prepend()`, `_enrich_single_call()` | Một lần gọi LLM tạo tóm tắt, câu hỏi giả định, câu bối cảnh và metadata cho mỗi đoạn. Phần làm giàu dùng để tìm kiếm, còn câu trả lời dựa vào đoạn cha gốc. Xử lý 121 đoạn mất 400,4 giây, nên lưu kết quả để dùng lại là hướng tối ưu đáng thử. |

---

## Phần 2: Khó khăn & Cách giải quyết (Challenges & Debugging)

**Lỗi kỹ thuật gặp phải (Exact error message):**

- PyArrow: `DLL load failed while importing _acero: An Application Control policy has blocked this file.`
- Multiprocess: `AttributeError: '_thread.RLock' object has no attribute '_recursion_count'`.
- OpenAI: `401 invalid_api_key` và `429 insufficient_quota`, với mã `credit_balance_exhausted`.

**Nguyên nhân gốc rễ & Cách debug:**

Với PyArrow, kiểm tra nhật ký Code Integrity của Windows cho thấy sự kiện 3077: chính sách kiểm soát ứng dụng chặn module _acero. Sau đó thử import lại trong môi trường ảo thì thành công. Lỗi này giúp em nhận ra cần đọc nguyên nhân bên trong traceback, thay vì chỉ nhìn thông báo ngoài cùng và nghĩ rằng package thiếu chức năng dataset.

Lỗi multiprocess đến từ phiên bản 0.70.19 gọi một phương thức khóa không có trên Python 3.12.0 của máy. Cách xử lý là hạ xuống 0.70.16, ghi ràng buộc phiên bản vào requirements.txt rồi kiểm tra lại việc tạo Dataset và chạy pip check.

Với OpenAI, thay key giải quyết được lỗi xác thực nhưng chưa giải quyết được lỗi số dư. Kiểm tra riêng một yêu cầu chat và một yêu cầu embedding giúp xác định tài khoản hết credit API. Sau khi nạp credit, cả hai yêu cầu đều thành công và pipeline mới chấm được điểm thật. Em cũng bổ sung bước kiểm tra trước khi chạy để phát hiện lỗi key hoặc kết nối sớm hơn.

Khi ghép các module, em nhận ra cần giữ liên kết giữa đoạn con và đoạn cha. Tìm kiếm và reranking dùng đoạn con, nhưng LLM cần đoạn cha để có đủ ngữ cảnh. Báo cáo cũng được bổ sung kết quả từng câu thay vì chỉ lưu điểm trung bình, nhờ vậy có thể đọc lại câu trả lời và đoạn trích khi phân tích lỗi.

**Kiến thức còn thiếu & Cách khắc phục:**

Em cần tìm hiểu thêm về truy vấn nhiều bước và quản lý phiên bản tài liệu. Trong câu hỏi về nhân viên Senior, hệ thống tìm được chính sách phép năm nhưng thiếu bảng lương. Em dự định thử tách câu hỏi thành từng ý và kiểm tra xem mỗi ý đã có bằng chứng hay chưa.

Một vấn đề khác là suy luận số học. Câu hỏi phí tạm ứng bị trả lời sai, trong khi tài liệu chưa ghi rõ quy ước tính phí theo ngày. Em cần học cách yêu cầu mô hình nêu giả định, dùng công cụ tính toán và rà soát đáp án chuẩn. Ngoài RAGAS, em sẽ chấm tay một số câu để tránh phụ thuộc hoàn toàn vào điểm tự động.

---

## Phần 3: Action Plan cho Project cá nhân (Application Plan)

### Project: Trợ lý tra cứu quy chế nội bộ tiếng Việt

Em dự định phát triển tiếp pipeline của bài lab thành một trợ lý tra cứu quy chế, ưu tiên trả lời có nguồn và phân biệt được tài liệu đang có hiệu lực.

#### 1. Hiện trạng

- **Pipeline hiện tại:** Cắt đoạn cha–con → làm giàu văn bản → BM25 và vector kết hợp RRF → Cross-Encoder → LLM trả lời → RAGAS đánh giá. Toàn bộ 47 bài kiểm thử đã đạt; baseline và Production đều có kết quả cho 20 câu hỏi.
- **Vấn đề đang gặp:** Câu hỏi nhiều ý có thể thiếu tài liệu cho một ý; tài liệu cũ vẫn lọt vào ngữ cảnh; mô hình còn tính phí sai. Hai PDF scan cần OCR để đọc được. Tổng thời gian chạy là 977,1 giây, nên cần đo riêng từng bước trước khi tối ưu tốc độ.

#### 2. Kế hoạch cải tiến

1. **Chiến lược cắt đoạn:** Giữ cấu trúc cha–con và thử kết hợp ranh giới tiêu đề để không tách điều khoản khỏi phần giải thích. Với PDF scan, bổ sung OCR và kiểm tra văn bản nhận dạng trước khi lập chỉ mục.
2. **Tìm kiếm:** Tiếp tục dùng Hybrid Search với RRF. Với câu hỏi nhiều ý, thử tìm riêng từng ý rồi gộp bằng chứng. Bổ sung metadata về phiên bản và ngày hiệu lực từ tài liệu để hạn chế lấy quy định cũ.
3. **Xếp hạng lại:** Dùng bge-reranker-v2-m3, nhưng loại các kết quả trùng đoạn cha trước khi chọn ngữ cảnh cuối cùng. Đo riêng thời gian nạp mô hình và xử lý truy vấn để biết bước nào cần cải thiện.
4. **Đánh giá:** Giữ bốn metric RAGAS, bổ sung kiểm tra tính đúng và đủ của đáp án, nhất là câu hỏi phủ định, tính toán và xung đột phiên bản. Dùng thêm câu hỏi ngoài bộ 20 câu của lab.
5. **Làm giàu văn bản:** Giữ chế độ một lần gọi cho mỗi đoạn và lưu kết quả theo nội dung tài liệu. Chỉ làm giàu lại khi tài liệu hoặc prompt thay đổi; luôn giữ nguồn và văn bản gốc để đối chiếu.

#### 3. Timeline triển khai

- **Tuần 1:** Rà soát metadata phiên bản, thử OCR hai PDF scan và bổ sung câu hỏi kiểm thử. Đo riêng thời gian tìm kiếm, reranking và sinh câu trả lời để có mốc so sánh.
- **Tuần 2:** Thử tìm kiếm theo từng ý, lọc phiên bản cũ và lưu kết quả enrichment. So sánh điểm, thời gian và chi phí với cấu hình hiện tại; ưu tiên thay đổi giúp xử lý các lỗi đã thấy trong Bottom-5.
