# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [CẦN ĐIỀN HỌ TÊN]
**Nhóm:** [CẦN ĐIỀN TÊN NHÓM]
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

Chiến lược cá nhân được chọn là `HeadingSectionChunker(chunk_size=500)`. Heading cấp cao chứa tên trường được gắn lại vào từng section; section vượt giới hạn được chia tiếp bằng `RecursiveChunker`. Benchmark dùng 10 tài liệu, mô hình đa ngữ cục bộ và `top_k=3`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được | Điểm Score | Có liên quan không? | Câu trả lời của Agent |
|---|-----------------|----------------------------|------------|----------------------|-----------------------|
| 1 | Thời hạn rút học phần và hậu quả bỏ học từ tuần ba tại TVU | `tvu-course-registration`: rút trong hai tuần, từ tuần ba bỏ học nhận F | 0,824929 | Có | Trả đúng thời hạn hai tuần và hậu quả điểm F |
| 2 | Nơi nộp, thời hạn và lệ phí phúc khảo tại TDMU | `tdmu-grade-appeal`: BM.01, bộ môn quản lý đề cương, bảy ngày | 0,755277 | Có | Trả đúng nơi nộp, bảy ngày và nghĩa vụ lệ phí |
| 3 | Giới hạn tín chỉ chương trình tiên tiến TNUT | `tnut-advanced-registration`: 8–16 hoặc 10–24 tín chỉ | 0,751457 | Có | Trả đúng hai trường hợp số học kỳ chính |
| 4 | Thông tin cần tìm hiểu và người tư vấn đăng ký tại UFM | `ufm-course-registration`: chương trình, đề cương, điều kiện và cố vấn | 0,808949 | Có | Trả đúng danh sách cần kiểm tra và cố vấn học tập |
| 5 | Ngưỡng cảnh báo tích lũy và tín chỉ F tại TVU | `tvu-academic-warning`: 1,20/1,40/1,60/1,80 và trên 24 tín chỉ F | 0,608530 | Có | Trả đúng các ngưỡng theo năm và tín chỉ F |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5. Cả năm chunk liên quan đều ở top-1 và agent trả lời đủ các ý bắt buộc, tương ứng 10/10 điểm retrieval.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác:**

So sánh với ba chiến lược còn lại cho thấy giữ nguyên câu hoặc dùng overlap chưa đủ khi corpus chứa quy định của nhiều trường có từ vựng giống nhau. Fixed-size đạt 4/10, sentence đạt 7/10 và recursive đạt 8/10, trong khi heading/section đạt 10/10. Bài học quan trọng nhất là phải gắn tên tài liệu và tiêu đề mục vào chunk để không mất ngữ cảnh nguồn.

Q2 được chạy với `metadata_filter={"audience": "student"}`. Việc lọc trước retrieval loại tài liệu vận hành phúc khảo dành cho staff, tránh trộn thao tác của cán bộ với hướng dẫn dành cho sinh viên.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
