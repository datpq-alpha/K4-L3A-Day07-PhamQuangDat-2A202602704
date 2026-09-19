# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [CẦN ĐIỀN TÊN NHÓM]

| Vai trò | Họ tên | Mã sinh viên |
|---|---|---|
| Thành viên 1 — Fixed-size | [CẦN ĐIỀN] | [CẦN ĐIỀN] |
| Thành viên 2 — Sentence | [CẦN ĐIỀN] | [CẦN ĐIỀN] |
| Thành viên 3 — Recursive | [CẦN ĐIỀN] | [CẦN ĐIỀN] |
| Thành viên 4 — Heading/section | [CẦN ĐIỀN] | [CẦN ĐIỀN] |

**Ngày:** 19/09/2026

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — 10 điểm

### Chủ đề và lý do chọn

**Chủ đề:** Quy định học vụ đại học: đăng ký/rút học phần, cảnh báo học vụ, đánh giá và phúc khảo.

Nhóm chọn chủ đề này vì các quy định có nhiều con số, thời hạn và điều kiện cần được truy xuất chính xác. Các trường thường dùng từ vựng gần giống nhau nhưng quy định khác nhau, vì vậy đây là corpus phù hợp để quan sát ảnh hưởng của chunking, tiêu đề và metadata đến retrieval.

### Danh sách tài liệu

Corpus gồm 10 file đã làm sạch trong `data/academic_regulations/`.

| # | Tài liệu | Trường/nguồn | Phiên bản | Ký tự | Metadata chính |
|---|---|---|---|---:|---|
| 1 | `tvu-course-registration` | [TVU — Sổ tay sinh viên](https://cmp.tvu.edu.vn/so-tay-sinh-vien/) | Sổ tay 2026 | 1.761 | student, registration |
| 2 | `tvu-academic-warning` | [TVU — Sổ tay sinh viên](https://cmp.tvu.edu.vn/so-tay-sinh-vien/) | Sổ tay 2026 | 1.395 | student, academic-warning |
| 3 | `tvu-grade-appeal` | [TVU — Sổ tay sinh viên](https://cmp.tvu.edu.vn/so-tay-sinh-vien/) | Sổ tay 2026 | 1.287 | student, grade-appeal |
| 4 | `qtu-academic-affairs-overview` | [QTU — Quy định công tác học vụ](https://qtu.edu.vn/qd-95-ban-hanh-quy-dinh-ve-cong-tac-hoc-vu-tai-truong-dai-hoc-quang-trung/) | 95/QĐ-ĐHQT, 24/06/2021 | 1.249 | all, academic-policy |
| 5 | `tdmu-grade-appeal` | [TDMU — PDF phúc khảo](https://tdmu.edu.vn/hinh/thuvien/taptin/2-6-2025-4-42-24-pm06-BKTKDDBCL-QT.09-Phuc%20khao%20Bai%20KTr.pdf) | QT/BKTKĐ&ĐBCL/09, lần 01 | 1.893 | student, grade-appeal |
| 6 | `tdmu-grade-appeal-operations` | Cùng PDF TDMU, tách theo đối tượng | QT/BKTKĐ&ĐBCL/09, lần 01 | 1.653 | staff, grade-appeal |
| 7 | `tnut-advanced-registration` | [TNUT — Quy chế CTTT](https://fit.tnut.edu.vn/bai-viet/quy-che-dao-tao-trinh-do-dai-hoc-cho-chuong-trinh-tien-tien-nam-2022-176) | 3571/QĐ-ĐHKTCN, 14/12/2022 | 1.309 | student, registration |
| 8 | `tnut-advanced-withdrawal-assessment` | Cùng quy chế TNUT | 3571/QĐ-ĐHKTCN, 14/12/2022 | 1.384 | student, withdrawal-and-assessment |
| 9 | `ufm-course-registration` | [UFM — Quy chế tín chỉ](https://pdt.ufm.edu.vn/dulieu/quiche/1329_Quy_che_dao_tao_tin_chi_tu_khoa_2021.htm) | 1329/QĐ-ĐHTCM, 16/07/2021 | 1.509 | student, registration |
| 10 | `ufm-assessment` | Cùng quy chế UFM | 1329/QĐ-ĐHTCM, 16/07/2021 | 1.096 | student, assessment |

File kiểm kê nguồn: `data/academic_regulations/sources.csv`.

### Quản trị dữ liệu

- [x] Chỉ dùng URL công khai thuộc tên miền chính thức của trường.
- [x] Không thu thập dữ liệu cá nhân, thông tin đăng nhập hoặc nội dung sau đăng nhập.
- [x] Mỗi file có `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`.
- [x] Corpus có ba audience: `student`, `staff`, `all`.
- [x] Nội dung được làm sạch, chỉ giữ điều khoản cần thiết và không tự bổ sung quy định.
- [x] PDF “Sổ tay Cố vấn học tập UFM 2018” không được đưa vào corpus vì trang đầu ghi “LƯU HÀNH NỘI BỘ”.

**Lưu ý chất lượng nguồn:** Trang Sổ tay TVU có các liên kết spam bất thường ở phần đầu. Nhóm chỉ trích phần Sổ tay sinh viên 2026, loại toàn bộ menu/liên kết nhiễu và cần kiểm tra lại nguồn trước ngày nộp.

### Cấu trúc metadata

| Trường | Kiểu | Ví dụ | Tác dụng |
|---|---|---|---|
| `doc_id` | string | `tdmu-grade-appeal` | Liên kết chunk với tài liệu gốc |
| `title` | string | Quy trình phúc khảo… | Truy vết và giữ ngữ cảnh |
| `audience` | enum | student / staff / all | Loại quy trình dành cho sai đối tượng |
| `institution` | string | Thu Dau Mot University | Phân biệt quy định giữa các trường |
| `department` | string | academic-affairs | Lọc theo đơn vị phụ trách |
| `category` | string | grade-appeal | Lọc theo nghiệp vụ |
| `language` | string | vi | Chọn embedding/ngôn ngữ |
| `source_url` | URL | URL văn bản gốc | Truy vết nguồn |
| `retrieved_at` | date | 2026-09-19 | Kiểm soát độ mới |
| `document_version` | string | 3571/QĐ… | Kiểm soát hiệu lực |
| `chunk_index` | integer | 2 | Xác định vị trí chunk |
| `chunk_strategy` | string | heading_section | Tái lập thí nghiệm |

---

## 2. Thiết kế chiến lược (Strategy Design) — 15 điểm

### Thiết lập chung

- Corpus: cùng 10 tài liệu.
- Embedding: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, vector 384 chiều.
- Top-k: 3.
- Cùng năm query và gold answer.
- Agent: extractive answerer không dùng API, chỉ chọn câu từ context và gắn citation `[1]`, `[2]`.
- Chỉ thay đổi chunker và tham số chunking.

Lệnh tái lập:

```powershell
$env:HF_HUB_OFFLINE = "1"
.\.venv\Scripts\python.exe -X utf8 scripts\benchmark_academic_regulations.py --embedding local
```

### Phân tích baseline trên ba tài liệu

Tham số `chunk_size=500`; bảng ghi “số chunk / độ dài trung bình”.

| Tài liệu | Fixed-size | Sentence | Recursive |
|---|---:|---:|---:|
| TVU — đăng ký/rút học phần | 3 / 493,33 | 4 / 343,25 | 4 / 343,50 |
| TDMU — phúc khảo | 4 / 396,00 | 4 / 356,75 | 4 / 357,00 |
| TNUT — đăng ký CTTT | 2 / 466,50 | 3 / 293,00 | 2 / 440,50 |

Fixed-size tạo ít chunk và chunk dài hơn nhưng có thể cắt mất heading hoặc tên trường. Sentence giữ câu trọn vẹn nhưng độ dài không đồng đều. Recursive ưu tiên ranh giới đoạn/câu và tạo độ dài cân bằng hơn.

### Chiến lược của bốn thành viên

**Thành viên 1 — [CẦN ĐIỀN]**

- Chiến lược: `FixedSizeChunker(chunk_size=500, overlap=75)`.
- Lý do: baseline đơn giản, có overlap để giảm mất thông tin tại ranh giới.
- Toàn corpus: 28 chunks, trung bình 418,32 ký tự.

**Thành viên 2 — [CẦN ĐIỀN]**

- Chiến lược: `SentenceChunker(max_sentences_per_chunk=3)`.
- Lý do: điều khoản thường được diễn đạt bằng một đến ba câu liên tiếp; giữ nguyên dấu câu giúp answerer trích xuất dễ hơn.
- Toàn corpus: 32 chunks, trung bình 322,28 ký tự.

**Thành viên 3 — [CẦN ĐIỀN]**

- Chiến lược: `RecursiveChunker(chunk_size=500)`.
- Lý do: ưu tiên đoạn, dòng, câu và từ; chỉ cắt sâu hơn khi đoạn vượt ngưỡng.
- Toàn corpus: 30 chunks, trung bình 344,10 ký tự.

**Thành viên 4 — [CẦN ĐIỀN]**

- Chiến lược: `HeadingSectionChunker(chunk_size=500)`.
- Lý do: mỗi điều/mục trong quy định là một đơn vị ngữ nghĩa. Heading cấp cao được gắn lại vào mọi section; section dài được đưa qua recursive chunker.
- Toàn corpus: 34 chunks, trung bình 352,21 ký tự.
- Code nằm trong `scripts/benchmark_academic_regulations.py`.

### So sánh giữa các thành viên

| Thành viên | Chiến lược | Điểm retrieval | Điểm mạnh | Điểm yếu |
|---|---|---:|---|---|
| 1 | Fixed-size | 4/10 | Ít chunk, tốc độ tốt, có overlap | Cắt mất quan hệ giữa tên trường và điều khoản |
| 2 | Sentence | 7/10 | Câu hoàn chỉnh, dễ đọc và trích xuất | Có thể tách heading khỏi câu; Q1 thất bại top-3 |
| 3 | Recursive | 8/10 | Cân bằng kích thước và ranh giới tự nhiên | Q1 thất bại; Q3 đúng nhưng ở rank thấp hơn heading |
| 4 | Heading/section | **10/10** | Giữ tên trường và tiêu đề trong từng chunk; cả 5 câu đúng top-1 | Nhiều chunk hơn, cần xử lý section dài |

**Chiến lược tốt nhất:** Heading/section. Corpus gồm quy định của nhiều trường có từ vựng rất giống nhau; việc gắn tên tài liệu và heading vào từng section giúp model phân biệt trường, nghiệp vụ và điều kiện cụ thể. Đây là nguyên nhân chiến lược này đạt 10/10 trong khi fixed-size chỉ đạt 4/10.

---

## 3. Câu hỏi đánh giá và chất lượng truy xuất — 10 điểm

### Năm câu hỏi và gold answer

| # | Query | Gold answer | Chunk chuẩn |
|---|---|---|---|
| Q1 | Tại Trường Y Dược - Đại học Trà Vinh, sinh viên được rút học phần trong thời hạn nào và nếu tự ý bỏ học từ tuần thứ ba thì bị xử lý ra sao? | Được rút trong hai tuần từ đầu học kỳ chính; từ tuần ba, không đi học bị xem là tự ý bỏ học và nhận F. | `tvu-course-registration` |
| Q2 | Sinh viên Đại học Thủ Dầu Một phải nộp đơn phúc khảo ở đâu, trong bao lâu và phải thực hiện quy định lệ phí như thế nào? | Nộp BM.01 về bộ môn quản lý đề cương trong bảy ngày từ ngày công bố điểm và đóng lệ phí theo quy định. | `tdmu-grade-appeal` |
| Q3 | Sinh viên chương trình tiên tiến TNUT được đăng ký tối thiểu và tối đa bao nhiêu tín chỉ trong học kỳ chính? | Năm có ba kỳ chính: 8–16 tín chỉ/kỳ; năm có hai kỳ chính: 10–24 tín chỉ/kỳ. | `tnut-advanced-registration` |
| Q4 | Ở UFM, khi lập kế hoạch đăng ký học phần, sinh viên cần tìm hiểu những gì và có thể nhờ ai tư vấn? | Tìm hiểu chương trình, đề cương, điều kiện đăng ký, kế hoạch, thời khóa biểu; kiểm tra kết quả/điều kiện cá nhân và có thể hỏi cố vấn học tập. | `ufm-course-registration` |
| Q5 | Các ngưỡng điểm trung bình tích lũy nào khiến sinh viên TVU bị cảnh báo theo từng năm và số tín chỉ F tồn đọng tối đa là bao nhiêu? | Dưới 1,20; 1,40; 1,60; 1,80 tương ứng các năm; cảnh báo khi tín chỉ F tồn đọng vượt 24. | `tvu-academic-warning` |

Q2 sử dụng:

```python
metadata_filter={"audience": "student"}
```

TDMU có hai tài liệu cùng nghiệp vụ: hướng dẫn sinh viên và quy trình vận hành cho staff. Trong kết quả không lọc của sentence/recursive/heading, chunk `tdmu-grade-appeal-operations` xuất hiện trong top-3; lọc trước retrieval loại chunk này.

### Kết quả semantic benchmark

| Chiến lược | Q1 | Q2 | Q3 | Q4 | Q5 | Tổng |
|---|---:|---:|---:|---:|---:|---:|
| Fixed-size | 0 | 2 | 1 | 1 | 0 | **4/10** |
| Sentence | 0 | 2 | 1 | 2 | 2 | **7/10** |
| Recursive | 0 | 2 | 2 | 2 | 2 | **8/10** |
| Heading/section | 2 | 2 | 2 | 2 | 2 | **10/10** |

### Top-1 của chiến lược tốt nhất

| Query | Top-1 doc | Score | Chunk đúng? | Agent đúng? |
|---|---|---:|---|---|
| Q1 | `tvu-course-registration` | 0,824929 | Có | Có |
| Q2 | `tdmu-grade-appeal` | 0,755277 | Có | Có |
| Q3 | `tnut-advanced-registration` | 0,751457 | Có | Có |
| Q4 | `ufm-course-registration` | 0,808949 | Có | Có |
| Q5 | `tvu-academic-warning` | 0,608530 | Có | Có |

**Bao nhiêu câu có chunk liên quan trong top-3?** 5/5 với heading/section.

**Bao nhiêu câu có chunk liên quan ở top-1 và câu trả lời đủ ý?** 5/5.

### Phân tích lỗi

Failure case rõ nhất là Q1. Fixed-size, sentence và recursive không đưa `tvu-course-registration` vào top-3 khi dùng semantic embedding. Các chunk nói về rút học phần của TVU bị tách khỏi heading chứa tên trường; model ưu tiên các chunk TNUT/TVU khác có từ khóa gần giống. Heading chunker gắn lại tiêu đề trường và mục “Rút bớt học phần”, đưa đúng chunk lên top-1 với score 0,824929.

Q3 cho thấy fixed-size và sentence vẫn tìm được tài liệu TNUT nhưng ở rank 2 vì một chunk TVU về đăng ký tín chỉ cạnh tranh mạnh. Heading/section giữ cụm “chương trình tiên tiến TNUT” cùng giới hạn tín chỉ, nên đạt top-1.

---

## 4. Thuyết trình (Demo) và bài học nhóm — 5 điểm

### Kịch bản demo

1. Giới thiệu 10 tài liệu, năm trường và metadata.
2. Chạy `pytest tests -q` để xác nhận pipeline lõi.
3. Chạy benchmark semantic bằng lệnh ở mục 2.
4. Chiếu bảng điểm 4/10 → 7/10 → 8/10 → 10/10.
5. Mở Q1 để minh họa fixed-size mất heading còn heading/section giữ đúng ngữ cảnh.
6. Mở Q2 trước/sau `audience=student` để minh họa metadata filtering.
7. Kết thúc bằng failure analysis và giới hạn dữ liệu.

### Ba insight chính

1. Với nhiều trường cùng dùng từ “đăng ký”, “rút học phần”, “phúc khảo”, tên trường và heading là tín hiệu retrieval quan trọng.
2. Chunk nhỏ hơn không tự động tốt hơn; chunk phải giữ được đơn vị quy định hoàn chỉnh.
3. Metadata filtering cần thực hiện trước similarity search để tài liệu dành cho staff không chiếm top-k của câu hỏi sinh viên.

### Bài học và cải tiến

Nếu làm lại, nhóm sẽ tìm bản PDF sạch hơn thay cho trang TVU có dấu hiệu bị chèn liên kết, bổ sung trường `effective_date` tách khỏi `document_version`, và đánh giá thêm embedding khác. Agent hiện là extractive để tái lập không cần API; phiên bản triển khai thực tế nên dùng LLM có kiểm soát cùng trích dẫn nguồn và kiểm tra câu trả lời với gold answer.

---

## Tự đánh giá

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Chất lượng bộ tài liệu | 10 / 10 |
| Thiết kế chiến lược | 15 / 15 |
| Chất lượng truy xuất | 10 / 10 |
| Chuẩn bị demo | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |

> Trước khi nộp: điền tên nhóm, họ tên và mã sinh viên; kiểm tra lại nguồn TVU; cập nhật phần tự đánh giá nếu kết quả demo thực tế khác dự kiến.
