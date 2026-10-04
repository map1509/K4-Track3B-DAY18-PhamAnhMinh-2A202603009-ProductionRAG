# Phân tích lỗi — Lab 18: Production RAG

**Họ và tên học viên:** Phạm Anh Minh  
**Khóa:** K4 - Track 3B

---

## RAGAS Scores

Đã chạy lại API sau khi sửa dấu tiếng Việt trong prompt và fallback M5. Nguồn: reports/integration_after_m5_fix.log. Baseline và Production đều hoàn tất 20 câu hỏi trong cùng phiên chạy.

| Metric | Naive Baseline | Production | Δ |
|---|---:|---:|---:|
| faithfulness | 0.7508 | 0.7775 | +0.0267 |
| answer_relevancy | 0.6695 | 0.7119 | +0.0425 |
| context_precision | 0.9250 | 0.9750 | +0.0500 |
| context_recall | 0.9000 | 0.9250 | +0.0250 |

Cả bốn metric tăng so với baseline cùng phiên và đều trên 0,70. Answer relevancy chưa đạt 0,75; faithfulness chưa đạt 0,85, nên lần đo này không đạt hai điều kiện bonus tương ứng. So với lần đo trước, kết quả không tăng đồng đều. Một lần chạy chưa đủ để tách ảnh hưởng của việc sửa prompt khỏi biến động của LLM và evaluator.

## Bottom-5 Failures

Năm câu dưới đây được xếp tăng dần theo trung bình bốn metric. Em đối chiếu thủ công cả câu trả lời và ngữ cảnh; không mặc định mọi câu trong Bottom-5 đều sai.

### #1

- **Question:** Nhân viên được nghỉ bao nhiêu ngày phép năm?
- **Expected:** Theo chính sách hiện hành (v2024), nhân viên được nghỉ 15 ngày phép năm có lương. Chính sách cũ (v2023) là 12 ngày nhưng đã bị thay thế.
- **Got:** Không tìm thấy.
- **Worst metric:** `faithfulness` — 0.0000. Điểm trung bình: 0.5000.
- **Điểm chi tiết:** Faithfulness 0.0000; Answer Relevancy 0.0000; Context Precision 1.0000; Context Recall 1.0000.
- **Câu trả lời đúng không?** Sai: mô hình trả lời “Không tìm thấy”, trong khi chính sách hiện hành quy định 15 ngày phép năm có lương.
- **Ngữ cảnh có đáp án không?** Có đáp án trong chính sách năm 2024. Tuy nhiên, bản năm 2023 đứng trước bản năm 2024 và nêu 12 ngày. Mô hình đã không sử dụng được thông tin thay thế chính sách dù nó có trong ngữ cảnh.
- **Cần viết lại câu hỏi không?** Câu hỏi đủ rõ. Có thể thêm “theo chính sách hiện hành” trong ứng dụng, nhưng hệ thống vẫn cần tự xử lý phiên bản đã bị thay thế.
- **Root cause / Suggested fix:** Kiểm tra bước sinh câu trả lời và ưu tiên tài liệu còn hiệu lực ở M2/M3. M5 cần giữ metadata phiên bản từ nguồn đã xác minh. Không nên kết luận tìm kiếm thiếu đáp án khi context recall là 1.
- **Error Tree:** Trả lời sai → ngữ cảnh có đáp án nhưng lẫn phiên bản → câu hỏi rõ → sửa chọn phiên bản và cách sử dụng bằng chứng.

### #2

- **Question:** Nhân viên thử việc có được hưởng bảo hiểm sức khỏe PVI không?
- **Expected:** KHÔNG. Nhân viên thử việc chưa được hưởng gói bảo hiểm sức khỏe PVI. Chỉ được tham gia bảo hiểm xã hội bắt buộc.
- **Got:** Không tìm thấy.
- **Worst metric:** `faithfulness` — 0.0000. Điểm trung bình: 0.5000.
- **Điểm chi tiết:** Faithfulness 0.0000; Answer Relevancy 0.0000; Context Precision 1.0000; Context Recall 1.0000.
- **Câu trả lời đúng không?** Sai: mô hình trả lời “Không tìm thấy”. Đáp án là nhân viên thử việc chưa được hưởng PVI, chỉ tham gia bảo hiểm xã hội bắt buộc.
- **Ngữ cảnh có đáp án không?** Có đầy đủ bằng chứng trong thu_viec.md. bao_hiem_suc_khoe.md cũng ghi gói PVI dành cho nhân viên chính thức. Đây là lỗi sử dụng ngữ cảnh, không phải thiếu tài liệu.
- **Cần viết lại câu hỏi không?** Không cần viết lại. Câu hỏi đã nêu rõ đối tượng thử việc và loại bảo hiểm PVI.
- **Root cause / Suggested fix:** Ưu tiên sửa prompt sinh câu trả lời để nhận diện điều khoản phủ định và chỉ từ chối khi thực sự thiếu bằng chứng. M4 cần bổ sung kiểm tra correctness cho trường hợp “Không tìm thấy” dù ngữ cảnh đủ.
- **Error Tree:** Trả lời sai → ngữ cảnh đủ → câu hỏi rõ → sửa synthesis và kiểm tra câu từ chối.

### #3

- **Question:** Một nhân viên Senior có 9 năm thâm niên được nghỉ bao nhiêu ngày phép năm và lương trong khoảng nào?
- **Expected:** Theo chính sách v2024: 15 ngày cơ bản + 3 ngày thâm niên (9÷3=3) = 18 ngày phép. Lương Senior (P3-P4): 20-35 triệu VNĐ/tháng.
- **Got:** Nhân viên có 9 năm thâm niên sẽ được nghỉ 18 ngày phép năm (15 ngày + 3 ngày thêm cho 3 năm thâm niên). Lương sẽ được tính theo quy định và không có thông tin cụ thể trong context về mức lương, nên không thể xác định được.
- **Worst metric:** `answer_relevancy` — 0.0000. Điểm trung bình: 0.5750.
- **Điểm chi tiết:** Faithfulness 0.8000; Answer Relevancy 0.0000; Context Precision 1.0000; Context Recall 0.5000.
- **Câu trả lời đúng không?** Đúng tổng 18 ngày phép nhưng thiếu dải lương Senior 20–35 triệu VNĐ/tháng. Cách diễn đạt “3 ngày thêm cho 3 năm thâm niên” cũng không chính xác: 9 năm tương ứng ba chu kỳ 3 năm.
- **Ngữ cảnh có đáp án không?** Có chính sách nghỉ phép năm nhưng không có bang_luong_2024.md. Các đoạn còn lại đều liên quan đến nghỉ phép, nên thiếu bằng chứng cho ý hỏi về lương.
- **Cần viết lại câu hỏi không?** Nên tách thành hai truy vấn: phép năm theo thâm niên và khung lương Senior. Giữ nguyên câu hỏi gốc trong bộ benchmark để so sánh công bằng.
- **Root cause / Suggested fix:** M2/M3 cần chọn bằng chứng đa dạng theo từng ý và loại trùng đoạn cha. Synthesis cần kiểm tra đủ ý, giải thích đúng công thức 15 + 9/3 = 18 và nêu rõ dữ liệu còn thiếu.
- **Error Tree:** Trả lời thiếu ý → ngữ cảnh thiếu bảng lương → tách truy vấn theo ý → sửa retrieval, reranking và diễn giải.

### #4

- **Question:** Nhân viên tạm ứng 15 triệu, sau 20 ngày mới thanh toán. Bị phạt bao nhiêu?
- **Expected:** Thời hạn thanh toán là 15 ngày. Quá hạn 5 ngày, bị tính phí 2%/tháng trên 15.000.000 VNĐ = 300.000 VNĐ/tháng (tính pro-rata khoảng 50.000 VNĐ cho 5 ngày).
- **Got:** Nhân viên tạm ứng 15 triệu VNĐ và đã thanh toán sau 20 ngày. Thời hạn thanh toán là 15 ngày, nên nhân viên đã trễ 5 ngày.

Phí phạt là 2%/tháng trên số tiền chưa hoàn ứng. Vì 20 ngày tương đương với khoảng 0.67 tháng, nên phí phạt sẽ được tính như sau:

Phí phạt = 15.000.000 VNĐ * 2% * 0.67 = 15.000.000 VNĐ * 0.02 * 0.67 = 1.005.000 VNĐ.

Vậy, nhân viên bị phạt 1.005.000 VNĐ.
- **Worst metric:** `faithfulness` — 0.2500. Điểm trung bình: 0.6351.
- **Điểm chi tiết:** Faithfulness 0.2500; Answer Relevancy 0.7905; Context Precision 1.0000; Context Recall 0.5000.
- **Câu trả lời đúng không?** Sai cả cách tính thời gian lẫn phép nhân. Mô hình dùng 20 ngày thay vì 5 ngày quá hạn; ngay cả biểu thức 15.000.000 × 0,02 × 0,67 cũng bằng 201.000, không phải 1.005.000 VNĐ.
- **Ngữ cảnh có đáp án không?** Có thời hạn 15 ngày và mức 2%/tháng. Tài liệu chưa ghi rõ quy ước tính phần tháng; đáp án chuẩn giả định tháng 30 ngày để ra khoảng 50.000 VNĐ cho 5 ngày.
- **Cần viết lại câu hỏi không?** Nên yêu cầu nêu số ngày quá hạn, đơn vị phí và giả định tính theo ngày. Chính sách nguồn cũng cần làm rõ quy ước pro-rata.
- **Root cause / Suggested fix:** Sửa bước sinh câu trả lời: không dùng toàn bộ 20 ngày để tính phí, nêu công thức và dùng công cụ tính toán. M4 cần kiểm tra số học và rà soát giả định trong ground truth.
- **Error Tree:** Trả lời sai → có mức phí nhưng thiếu quy ước ngày → làm rõ giả định → sửa suy luận thời gian, số học và dữ liệu đánh giá.

### #5

- **Question:** Nhân viên được tài trợ khóa học 25 triệu, nghỉ việc sau 8 tháng hoàn thành khóa học. Phải hoàn trả bao nhiêu?
- **Expected:** Nhân viên phải cam kết làm việc ít nhất 1 năm sau khi hoàn thành khóa học. Nghỉ sau 8 tháng là trước hạn cam kết, phải hoàn trả 100% chi phí tức 25.000.000 VNĐ.
- **Got:** Nhân viên phải hoàn trả **100% chi phí** đào tạo đã được tài trợ, tức là **25 triệu VNĐ**.
- **Worst metric:** `faithfulness` — 0.5000. Điểm trung bình: 0.8249.
- **Điểm chi tiết:** Faithfulness 0.5000; Answer Relevancy 0.7995; Context Precision 1.0000; Context Recall 1.0000.
- **Câu trả lời đúng không?** Đúng: nghỉ sau 8 tháng chưa đủ cam kết một năm, phải hoàn trả 100% chi phí, tức 25 triệu VNĐ. Câu trả lời có thể giải thích thêm điều khoản áp dụng.
- **Ngữ cảnh có đáp án không?** hoan_chi_dao_tao.md có đủ cam kết một năm và mức hoàn trả 100%. Không thấy bằng chứng cho rằng retrieval thiếu đáp án.
- **Cần viết lại câu hỏi không?** Không cần viết lại. Có thể yêu cầu giải thích ngắn điều khoản để người đọc dễ kiểm tra.
- **Root cause / Suggested fix:** M4 cần đối chiếu thủ công điểm faithfulness 0,5. Nhãn hallucination tự động chưa chứng minh đáp án sai. Synthesis có thể nêu 8 < 12 tháng và mức hoàn trả 100%.
- **Error Tree:** Trả lời đúng → ngữ cảnh đủ → câu hỏi rõ → rà soát evaluator và bổ sung giải thích.

## Case Study (cho presentation)

**Câu hỏi chọn phân tích:** Nhân viên thử việc có được hưởng bảo hiểm sức khỏe PVI không?

**Error Tree walkthrough:**

1. **Output đúng?** Không. Mô hình từ chối trả lời dù đáp án là chưa được hưởng PVI.
2. **Context đúng?** Có. Chính sách thử việc ghi rõ điều khoản này, và chính sách bảo hiểm nêu đối tượng nhân viên chính thức.
3. **Query rewrite cần thiết?** Không. Câu hỏi đủ rõ về đối tượng và loại bảo hiểm.
4. **Fix ở bước nào?** Ưu tiên synthesis: xử lý điều khoản phủ định và kiểm tra bằng chứng trước khi trả lời “Không tìm thấy”.

**Nếu có thêm một giờ:** em sẽ kiểm tra các câu từ chối khi ngữ cảnh đủ, thử prompt yêu cầu trích điều khoản áp dụng, sau đó xử lý truy vấn nhiều ý và lọc phiên bản. Việc cải thiện cần được kiểm tra trên cùng tập câu hỏi và một tập độc lập.

