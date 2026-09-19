# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phạm Quang Đạt
**Mã sinh viên:** 2A202602704
**Nhóm:** Magician
**Ngày:** 19/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung trong `REPORT_NHOM.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) — Bài tập 1.1

**Độ tương tự cosine cao nghĩa là gì?**

Độ tương tự cosine cao nghĩa là hai vector embedding hướng gần giống nhau, vì vậy hai đoạn văn thường có nội dung hoặc ý nghĩa liên quan. Giá trị gần `1` biểu thị mức tương đồng cao, gần `0` biểu thị ít liên quan, còn gần `-1` biểu thị hai hướng đối lập.

**Ví dụ có độ tương tự CAO:**

- Câu A: “Sinh viên đăng ký học phần trên cổng học vụ.”
- Câu B: “Người học ghi danh môn học qua hệ thống trực tuyến.”
- Tại sao tương đồng: Hai câu cùng nói về việc sinh viên đăng ký môn học qua một hệ thống trực tuyến, dù dùng từ ngữ khác nhau.

**Ví dụ có độ tương tự THẤP:**

- Câu A: “Sinh viên phải đóng học phí đúng hạn.”
- Câu B: “Hôm nay thời tiết có nhiều mây.”
- Tại sao khác: Một câu nói về nghĩa vụ tài chính của sinh viên, câu còn lại nói về thời tiết nên hầu như không có quan hệ ngữ nghĩa.

**Tại sao cosine similarity được ưu tiên hơn khoảng cách Euclid cho text embeddings?**

Cosine similarity tập trung vào góc, tức hướng ngữ nghĩa của vector, thay vì bị ảnh hưởng mạnh bởi độ lớn của vector. Vì thế nó phù hợp để so sánh nội dung văn bản, đặc biệt khi độ dài văn bản hoặc độ lớn embedding khác nhau.

### Bài toán tính toán Chunking — Bài tập 1.2

**Tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50`:**

```text
step = chunk_size - overlap = 500 - 50 = 450
số chunk = ceil((10000 - 50) / 450)
          = ceil(22,111...)
          = 23
```

**Đáp án: 23 chunks.**

**Nếu overlap tăng lên 100:**

```text
step = 500 - 100 = 400
số chunk = ceil((10000 - 100) / 400)
          = ceil(24,75)
          = 25
```

Số lượng tăng từ 23 lên 25 chunks vì bước dịch cửa sổ giảm từ 450 xuống 400 ký tự. Overlap lớn hơn giúp giữ lại ngữ cảnh ở ranh giới giữa hai chunk và giảm khả năng một ý quan trọng bị cắt đôi, nhưng cũng làm tăng lượng dữ liệu lưu trữ và tính toán.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**Chiến lược cá nhân — `FixedSizeChunker`:**

Tôi sử dụng `FixedSizeChunker(chunk_size=800, overlap=150)`. Mỗi cửa sổ chứa tối đa 800 ký tự và cửa sổ kế tiếp dịch 650 ký tự, nhờ đó 150 ký tự ở ranh giới được giữ lại để hạn chế cắt mất ý. Đây là fixed-size thuần: vị trí chia chỉ phụ thuộc số ký tự, không dựa vào câu, heading hoặc section. Cấu hình được chọn sau khi chạy cùng corpus, năm câu hỏi, mô hình embedding và `top_k=3`; so với cấu hình ban đầu `500/75` đạt 4/10, cấu hình `800/150` đạt 7/10.

**`SentenceChunker.chunk`:**

Tôi dùng regex `(?<=[.!?])(?:[ \t]+|\r?\n+)` để tách tại khoảng trắng hoặc xuống dòng đứng sau dấu kết thúc câu. Positive lookbehind giúp giữ lại dấu câu, sau đó các câu được gom theo `max_sentences_per_chunk` và loại bỏ khoảng trắng thừa. Text rỗng trả về danh sách rỗng; hạn chế còn lại là các chữ viết tắt như `TS.` hoặc số thập phân có thể bị nhận diện nhầm là ranh giới câu.

**`RecursiveChunker.chunk` / `_split`:**

Thuật toán lần lượt thử các separator từ ranh giới lớn đến nhỏ: đoạn văn, dòng, câu, từ và cuối cùng là ký tự. Mảnh dài hơn `chunk_size` tiếp tục được tách đệ quy bằng separator có ưu tiên thấp hơn; các mảnh nhỏ liền nhau được gom lại đến gần giới hạn để tránh tạo nhiều chunk vụn. Các base case gồm text rỗng, text đã nằm trong giới hạn và hết separator thì cắt cố định theo ký tự.

### Lớp EmbeddingStore

**`add_documents` + `search`:**

Mỗi `Document` được chuẩn hóa thành một record in-memory gồm ID nội bộ duy nhất, nội dung, bản sao metadata và embedding. `add_documents` không tự chunk mà lưu một record cho mỗi `Document`. Khi tìm kiếm, truy vấn được embed một lần, tính tích vô hướng với mọi record rồi sắp xếp score giảm dần; với embedding đã chuẩn hóa, tích vô hướng tương đương cosine similarity.

**`search_with_filter` + `delete_document`:**

Metadata được lọc trước khi thực hiện similarity search để các record không phù hợp không chiếm vị trí trong top-k. Bộ lọc hỗ trợ đồng thời nhiều cặp khóa–giá trị bằng điều kiện tất cả đều phải khớp. Khi xóa, store loại toàn bộ record có `metadata['doc_id']` bằng ID yêu cầu và trả về `True` nếu kích thước store thực sự giảm.

### Tác tử KnowledgeBaseAgent

**`answer`:**

Agent truy xuất top-k chunk, đánh số từng đoạn `[1]`, `[2]`, ... và đưa nội dung cùng nguồn vào prompt. Prompt yêu cầu LLM chỉ dùng ngữ cảnh được cung cấp, trích dẫn số nguồn và nói rõ khi không đủ thông tin nhằm giảm hallucination. Nếu store không trả kết quả, agent trả thông báo ngay và không gọi LLM.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết quả kiểm thử

Lệnh đã chạy:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -v
```

Kết quả:

```text
============================= test session starts =============================
platform win32 -- Python 3.11.0, pytest-9.1.1, pluggy-1.6.0
collected 42 items

tests/test_solution.py ..........................................       [100%]

============================= 42 passed in 0.11s ==============================
```

**Số lượng bài test vượt qua: 42 / 42.**

Ngoài bộ test, `main.py` cũng chạy hoàn chỉnh với mock embedding: nạp được 5 tài liệu hiện có, lưu 5 record, trả top-3 kết quả và gọi được `KnowledgeBaseAgent.answer()`.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Thí nghiệm dùng mô hình đa ngữ cục bộ `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. Các dự đoán được ghi trước khi chạy; trong thí nghiệm nhỏ này, score từ khoảng `0,4` được xem là tương đồng cao, nhưng ngưỡng thực tế cần được hiệu chỉnh theo corpus.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-------|-------|---------|---------------|-------|
| 1 | Sinh viên đăng ký học phần trên cổng học vụ. | Người học ghi danh môn học qua hệ thống trực tuyến. | Cao | 0,508616 | Có |
| 2 | Thư viện cho phép sinh viên mượn sách. | Sinh viên có thể mượn tài liệu tại thư viện. | Cao | 0,916984 | Có |
| 3 | Sinh viên phải đóng học phí đúng hạn. | Hôm nay thời tiết có nhiều mây. | Thấp | -0,015411 | Có |
| 4 | Cần nộp đơn phúc khảo để yêu cầu xem lại điểm. | Sinh viên gửi yêu cầu chấm lại kết quả thi. | Cao | 0,492566 | Có |
| 5 | Ký túc xá đóng cửa lúc 23 giờ. | Học bổng được xét dựa trên thành tích học tập. | Thấp | -0,011089 | Có |

**Kết quả bất ngờ nhất và bài học:**

Cặp thư viện đạt 0,916984, cao hơn rõ rệt hai cặp diễn đạt tương đương còn lại. Cặp đăng ký học phần chỉ đạt 0,508616 dù “đăng ký” và “ghi danh” gần nghĩa, cho thấy embedding vẫn nhạy với cách diễn đạt và mức độ trùng lặp từ vựng. Hai cặp khác chủ đề có score gần 0 đúng như dự đoán.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Tôi đảm nhận vai trò **Thành viên 1 — Fixed-size chunking** với cấu hình `FixedSizeChunker(chunk_size=800, overlap=150)`. Benchmark dùng 10 tài liệu, mô hình đa ngữ cục bộ `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` và `top_k=3`. Chiến lược tạo 19 chunks, độ dài trung bình 603,74 ký tự.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được | Điểm Score | Có liên quan không? | Câu trả lời của Agent |
|---|-----------------|----------------------------|------------|----------------------|-----------------------|
| 1 | Thời hạn rút học phần và hậu quả bỏ học từ tuần ba tại TVU | `tvu-grade-appeal`: nội dung phúc khảo tại TVU | 0,708859 | Không; tài liệu đúng không có trong top-3 | Trả nhầm quy định rút học phần của TNUT, thiếu mốc hai tuần của TVU — 0 điểm |
| 2 | Quy trình phúc khảo tại TDMU bắt đầu thế nào, thời hạn và lệ phí ra sao (không nêu đối tượng hỏi) | `tdmu-grade-appeal`: hướng dẫn phúc khảo cho người học | 0,653956 | Có | Sau lọc `audience=student`, trả đúng BM.01, bộ môn quản lý đề cương, bảy ngày và lệ phí — 2 điểm |
| 3 | Giới hạn tín chỉ chương trình tiên tiến TNUT | `tvu-course-registration`: quy định đăng ký tại TVU | 0,665663 | Không ở top-1; `tnut-advanced-registration` ở hạng 2 với 0,647664 | Có tài liệu liên quan trong top-3 nhưng câu trả lời thiếu các mức 8–16 và 10–24 tín chỉ — 1 điểm |
| 4 | Thông tin cần tìm hiểu và người tư vấn đăng ký tại UFM | `ufm-course-registration`: chuẩn bị đăng ký học phần | 0,754191 | Có | Trả đúng chương trình, đề cương, điều kiện và cố vấn học tập — 2 điểm |
| 5 | Ngưỡng cảnh báo tích lũy và tín chỉ F tại TVU | `tvu-academic-warning`: cảnh báo và buộc thôi học | 0,612541 | Có | Trả đúng 1,20/1,40/1,60/1,80 và trên 24 tín chỉ F — 2 điểm |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5. Q2, Q4 và Q5 có tài liệu đúng ở top-1 đồng thời agent trả lời đủ ý; Q3 có tài liệu đúng ở hạng 2 nhưng câu trả lời chưa đủ; Q1 không có tài liệu đúng trong top-3. Tổng điểm retrieval là **7/10**.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác:**

Tăng cửa sổ và overlap giúp fixed-size cải thiện từ 4/10 ở cấu hình `500/75` lên 7/10 ở cấu hình `800/150`, nhưng không giải quyết triệt để việc mất ngữ cảnh nguồn. Q1 cho thấy chunk chứa quy định rút học phần của TVU không giữ được tín hiệu tên trường đủ mạnh, còn Q3 cho thấy một chunk TVU có từ vựng tương tự có thể vượt chunk TNUT. Khi so sánh, sentence đạt 7/10, recursive đạt 8/10 và heading/section đạt 10/10; vì vậy bài học quan trọng là ranh giới cấu trúc và tên tài liệu có thể hữu ích hơn việc chỉ tăng kích thước hoặc overlap.

Q2 cố ý không nêu người hỏi và được chạy với `metadata_filter={"audience": "student"}`. Ở chiến lược fixed-size, tài liệu staff không lọt vào top-3 không lọc; tuy nhiên khi cả nhóm chạy cùng query, Recursive và Heading/section đều đưa `tdmu-grade-appeal-operations` vào top-3 không lọc và câu trả lời trộn thao tác của cán bộ. Lọc trước retrieval loại tài liệu staff và giữ đúng hướng dẫn dành cho người học.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 7 / 10 |
| **Tổng phần cá nhân** | **57 / 60** |
