# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Magician — K4-L3A

**Thành viên:** Nguyễn Vũ Anh, Phạm Quang Đạt, Nguyễn Thanh Duy, Trương Việt Anh

**Ngày:** 19/09/2026

> Báo cáo này tổng hợp kết quả từ bốn báo cáo cá nhân. Bộ benchmark chính thức của nhóm gồm đúng 5 câu hỏi ở Phần 3. Ba thành viên Phạm Quang Đạt, Nguyễn Thanh Duy và Trương Việt Anh đã chạy đúng bộ câu hỏi này. Nguyễn Vũ Anh chạy một phiên bản benchmark sớm hơn trên cùng corpus và cùng các nhóm nghiệp vụ; kết quả đó được dùng như một stress test bổ sung và không được coi là phép so sánh ngang hàng tuyệt đối.

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề và lý do chọn

**Chủ đề:** Quy định và dịch vụ đào tạo đại học, tập trung vào đăng ký/rút học phần, phúc khảo, đánh giá và cảnh báo học vụ.

Đây là miền dữ liệu phù hợp cho RAG vì câu trả lời phải chính xác về trường áp dụng, đối tượng, mốc thời gian, số tín chỉ và ngưỡng điểm. Các tài liệu có cấu trúc điều khoản/heading tương đối rõ, đồng thời có nội dung gần nhau nhưng khác `audience`, tạo điều kiện đánh giá metadata filtering.

### Danh sách tài liệu

Số ký tự dưới đây được tính trên phần nội dung Markdown sau khi bỏ YAML frontmatter.

| # | Tài liệu | Nguồn công khai | Phiên bản / ngày lấy | Ký tự | Metadata chính |
|---|---|---|---|---:|---|
| 1 | `tvu-course-registration.md` | [Sổ tay SV TVU](https://cmp.tvu.edu.vn/so-tay-sinh-vien/) | Sổ tay SV 2026 / 19-09-2026 | 1.380 | `audience=student`, `category=registration`, `institution=Tra Vinh University` |
| 2 | `tvu-academic-warning.md` | [Sổ tay SV TVU](https://cmp.tvu.edu.vn/so-tay-sinh-vien/) | Sổ tay SV 2026 / 19-09-2026 | 1.004 | `audience=student`, `category=academic-warning`, `institution=Tra Vinh University` |
| 3 | `tvu-grade-appeal.md` | [Sổ tay SV TVU](https://cmp.tvu.edu.vn/so-tay-sinh-vien/) | Sổ tay SV 2026 / 19-09-2026 | 905 | `audience=student`, `category=grade-appeal`, `institution=Tra Vinh University` |
| 4 | `qtu-academic-affairs-overview.md` | [QTU — QĐ 95](https://qtu.edu.vn/qd-95-ban-hanh-quy-dinh-ve-cong-tac-hoc-vu-tai-truong-dai-hoc-quang-trung/) | 95/QĐ-ĐHQT / 19-09-2026 | 836 | `audience=all`, `category=academic-policy`, `institution=Quang Trung University` |
| 5 | `tdmu-grade-appeal.md` | [TDMU — QT.09](https://tdmu.edu.vn/hinh/thuvien/taptin/2-6-2025-4-42-24-pm06-BKTKDDBCL-QT.09-Phuc%20khao%20Bai%20KTr.pdf) | QT.09 Lần 01 / 19-09-2026 | 1.434 | `audience=student`, `category=grade-appeal`, `institution=Thu Dau Mot University` |
| 6 | `tdmu-grade-appeal-operations.md` | [TDMU — QT.09](https://tdmu.edu.vn/hinh/thuvien/taptin/2-6-2025-4-42-24-pm06-BKTKDDBCL-QT.09-Phuc%20khao%20Bai%20KTr.pdf) | QT.09 Lần 01 / 19-09-2026 | 1.194 | `audience=staff`, `category=grade-appeal`, `institution=Thu Dau Mot University` |
| 7 | `tnut-advanced-registration.md` | [TNUT — QĐ 3571](https://fit.tnut.edu.vn/bai-viet/quy-che-dao-tao-trinh-do-dai-hoc-cho-chuong-trinh-tien-tien-nam-2022-176) | 3571/QĐ-ĐHKTCN / 19-09-2026 | 883 | `audience=student`, `category=registration`, `institution=Thai Nguyen University of Technology` |
| 8 | `tnut-advanced-withdrawal-assessment.md` | [TNUT — QĐ 3571](https://fit.tnut.edu.vn/bai-viet/quy-che-dao-tao-trinh-do-dai-hoc-cho-chuong-trinh-tien-tien-nam-2022-176) | 3571/QĐ-ĐHKTCN / 19-09-2026 | 928 | `audience=student`, `category=withdrawal-and-assessment`, `institution=Thai Nguyen University of Technology` |
| 9 | `ufm-course-registration.md` | [UFM — QĐ 1329](https://pdt.ufm.edu.vn/dulieu/quiche/1329_Quy_che_dao_tao_tin_chi_tu_khoa_2021.htm) | 1329/QĐ-ĐHTCM / 19-09-2026 | 1.104 | `audience=student`, `category=registration`, `institution=University of Finance - Marketing` |
| 10 | `ufm-assessment.md` | [UFM — QĐ 1329](https://pdt.ufm.edu.vn/dulieu/quiche/1329_Quy_che_dao_tao_tin_chi_tu_khoa_2021.htm) | 1329/QĐ-ĐHTCM / 19-09-2026 | 695 | `audience=student`, `category=assessment`, `institution=University of Finance - Marketing` |

Tất cả tài liệu đều có `source_url`, `retrieved_at`, `document_version`, `audience`, `department`, `category` và `language`. Nguồn đều công khai; corpus không chứa mật khẩu, dữ liệu cá nhân hoặc tài liệu nội bộ.

### Metadata schema

| Trường | Ví dụ | Mục đích truy xuất |
|---|---|---|
| `doc_id` | `tdmu-grade-appeal` | Định danh tài liệu và liên kết các chunk cùng nguồn. |
| `audience` | `student`, `staff`, `all` | Lọc đúng đối tượng áp dụng trước khi xếp hạng. |
| `department` | `academic-affairs` | Phân biệt đơn vị/nghiệp vụ phụ trách. |
| `category` | `registration`, `grade-appeal` | Giảm nhiễu giữa các loại quy định. |
| `institution` | `Tra Vinh University` | Phân biệt quy định có từ khóa giống nhau giữa các trường. |
| `language` | `vi` | Hỗ trợ lựa chọn mô hình embedding phù hợp. |
| `document_version` | `QT/BKTKĐ&ĐBCL/09` | Kiểm tra phiên bản và hiệu lực văn bản. |
| `source_url`, `retrieved_at` | URL, `2026-09-19` | Truy vết nguồn và độ mới dữ liệu. |

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Baseline

Nhóm chạy `ChunkingStrategyComparator().compare(chunk_size=200)` trên ba tài liệu sau khi bỏ YAML frontmatter:

| Tài liệu | Fixed-size (số chunk / TB ký tự) | Sentence (số chunk / TB ký tự) | Recursive (số chunk / TB ký tự) |
|---|---:|---:|---:|
| `tdmu-grade-appeal.md` | 10 / 188,40 | 4 / 356,75 | 10 / 141,60 |
| `tnut-advanced-registration.md` | 6 / 188,83 | 3 / 293,00 | 7 / 124,43 |
| `tvu-course-registration.md` | 9 / 197,78 | 4 / 343,25 | 10 / 136,20 |

Fixed-size tạo các cửa sổ đồng đều nhưng có thể cắt ngang câu. Sentence giữ nguyên câu nhưng có thể tách hai câu liên quan sang hai chunk. Recursive tôn trọng ranh giới đoạn/câu hơn fixed-size, nhưng nếu không gắn lại heading thì chunk có thể mất tên trường hoặc tên mục.

### Chiến lược của từng thành viên

| Thành viên | Chiến lược | Cấu hình / quy mô | Embedding dùng khi benchmark | Lý do và đánh đổi |
|---|---|---|---|---|
| Nguyễn Vũ Anh | `HeadingRecursiveChunker` có **Preamble Context Merging** | Tách theo heading, gộp phần mở đầu/tiêu đề vào section đầu rồi recursive; báo cáo cá nhân không ghi tổng số chunk/TB ký tự | `semantic_hash_embed`, 128 chiều, unigram + bigram | Giữ tên trường, đề mục và số liệu trong cùng chunk; khắc phục lỗi phần mở đầu chiếm top-1 còn section chứa đáp án bị đẩy xuống sau. |
| Phạm Quang Đạt | `FixedSizeChunker` | `chunk_size=800`, `overlap=150`; 19 chunks; TB 616,47 ký tự | `paraphrase-multilingual-MiniLM-L12-v2` | Đơn giản, overlap giảm mất ngữ cảnh biên; vẫn dễ lẫn trường và cắt sai đơn vị ngữ nghĩa. |
| Nguyễn Thanh Duy | `SentenceChunker` | `max_sentences_per_chunk=3`; 32 chunks; TB 322,28 ký tự | Không nêu tên backend trong báo cáo cá nhân | Không cắt gãy câu; Q2 cho thấy câu về lệ phí có thể bị đẩy sang chunk kế tiếp. |
| Trương Việt Anh | `HeadingSectionChunker` | `chunk_size=500`; 34 chunks; TB 352,21 ký tự | `VietnameseLexicalEmbedder`, unigram + bigram + trigram | Gắn heading cấp cao vào từng section và recursive section dài; phù hợp corpus Markdown nhưng phụ thuộc heading được chuẩn hóa. |

### Kết quả và so sánh giữa các chiến lược

| Thành viên / chiến lược | Kết quả được báo cáo | Điểm mạnh quan sát được | Failure case / hạn chế |
|---|---:|---|---|
| Phạm Quang Đạt — Fixed-size | 4/5 có tài liệu đúng trong top-3; **7/10** | Cấu hình 800/150 tốt hơn baseline 500/75 (4/10). | Q1 không có tài liệu TVU đúng trong top-3; Q3 đúng tài liệu ở hạng 2 nhưng câu trả lời thiếu mốc tín chỉ. |
| Nguyễn Thanh Duy — Sentence | 5/5 tài liệu đúng ở top-1; **9/10 theo rubric nghiêm ngặt** | Bảo toàn câu; Q1, Q3–Q5 có đủ bằng chứng. | Q2 lấy đúng nơi nộp và 7 ngày nhưng câu trả lời thiếu chi tiết lệ phí, nên tính 1/2 cho câu này. |
| Trương Việt Anh — Heading/section | 5/5 ở mức tài liệu và nội dung; **10/10** | Heading giữ tín hiệu tên trường/chủ đề; toàn bộ answer terms nằm trong top-3. | Lexical embedding còn yếu với câu diễn đạt lại bằng từ đồng nghĩa. |
| Nguyễn Vũ Anh — Heading/recursive + preamble merging *(stress test trên bộ câu hỏi sớm)* | 5/5 top-1 ở cả mức `doc_id` và nội dung; **10/10 nghiêm ngặt** | Sau tối ưu, cả 5 chunk top-1 đều chứa đầy đủ dữ liệu trả lời; preamble không còn tách thành chunk gây nhiễu. | Kết quả không so sánh trực tiếp với ba dòng trên vì câu hỏi và backend khác; báo cáo không cung cấp tổng số chunk/TB ký tự. |

Các con số cho thấy heading-aware phù hợp nhất với corpus này. `HeadingSectionChunker` đạt 10/10 trên bộ benchmark chung; `HeadingRecursiveChunker` có Preamble Context Merging cũng đạt 10/10 trên stress test riêng. Tuy nhiên, đây chưa phải thí nghiệm cô lập hoàn toàn tác động của chunking vì các thành viên dùng embedding backend khác nhau. Kết luận chắc chắn nhất là: cấu trúc heading và việc giữ preamble giúp bảo toàn ngữ cảnh nguồn; còn điểm số tuyệt đối phụ thuộc đồng thời vào chunker, embedding, query wording và cách chấm nội dung.

## 3. Câu hỏi đánh giá và chất lượng truy xuất — Nhóm (10 điểm)

### Bộ 5 câu hỏi benchmark chính thức

| # | Câu hỏi benchmark | Gold answer | Chunk chứa thông tin |
|---|---|---|---|
| 1 | Tại Trường Y Dược - Đại học Trà Vinh, sinh viên được rút học phần trong thời hạn nào và nếu tự ý bỏ học từ tuần thứ ba thì bị xử lý ra sao? | Được rút trong hai tuần đầu học kỳ chính; từ tuần thứ ba, tự ý bỏ học bị nhận điểm F. | `tvu-course-registration#2` |
| 2 | Sinh viên Đại học Thủ Dầu Một phải nộp đơn phúc khảo ở đâu, trong bao lâu và phải thực hiện quy định lệ phí như thế nào? | Nộp BM.01 về bộ môn quản lý đề cương trong bảy ngày kể từ ngày công bố điểm và đóng lệ phí theo quy định. | `tdmu-grade-appeal#1`; dùng `metadata_filter={"audience": "student"}` |
| 3 | Sinh viên chương trình tiên tiến TNUT được đăng ký tối thiểu và tối đa bao nhiêu tín chỉ trong học kỳ chính? | Năm có ba học kỳ chính: 8–16 tín chỉ/kỳ; năm có hai học kỳ chính: 10–24 tín chỉ/kỳ. | `tnut-advanced-registration#1` |
| 4 | Ở UFM, khi lập kế hoạch đăng ký học phần, sinh viên cần tìm hiểu những gì và có thể nhờ ai tư vấn? | Tìm hiểu chương trình, đề cương, điều kiện đăng ký, kế hoạch đào tạo, thời khóa biểu và có thể nhờ cố vấn học tập. | `ufm-course-registration#1` |
| 5 | Các ngưỡng điểm trung bình tích lũy nào khiến sinh viên TVU bị cảnh báo học vụ theo từng năm và số tín chỉ F tồn đọng tối đa là bao nhiêu? | Dưới 1,20; 1,40; 1,60; 1,80 theo từng năm tương ứng; hoặc tín chỉ F tồn đọng vượt 24. | `tvu-academic-warning#1` |

Các câu hỏi bao phủ nhiều dạng thông tin: thời hạn và chế tài, quy trình kèm metadata filter, khoảng số tín chỉ, danh sách điều kiện/tư vấn và bảng ngưỡng điểm theo năm.

### Kết quả tổng hợp

| Chiến lược | Q1 | Q2 | Q3 | Q4 | Q5 | Tổng |
|---|---:|---:|---:|---:|---:|---:|
| Fixed-size 800/150 | 0/2 | 2/2 | 1/2 | 2/2 | 2/2 | **7/10** |
| Sentence, 3 câu/chunk | 2/2 | 1/2 | 2/2 | 2/2 | 2/2 | **9/10** |
| Heading/section 500 | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | **10/10** |

`HeadingSectionChunker` đạt kết quả tốt nhất trên bộ benchmark chung vì giữ heading trong từng chunk và chỉ dùng recursive fallback khi section vượt giới hạn. `SentenceChunker` lấy đúng tài liệu ở cả 5 câu nhưng Q2 thiếu một chi tiết nằm ở câu kế tiếp. Fixed-size cải thiện khi tăng cửa sổ và overlap, song vẫn bị nhiễu bởi tài liệu có từ vựng tương tự.

### Thử nghiệm metadata filtering

Q2 bắt buộc dùng `metadata_filter={"audience": "student"}`. Pre-filter loại `tdmu-grade-appeal-operations.md` (`audience=staff`) trước khi tính similarity, nhờ đó agent không trộn thao tác nội bộ của cán bộ với hướng dẫn dành cho sinh viên.

Trong phép thử A/B của Trương Việt Anh, cả khi có và không có filter, `tdmu-grade-appeal` vẫn ở top-1 và đạt 2/2 vì câu hỏi đã chứa các từ phân biệt mạnh như “sinh viên” và “nộp đơn”. Kết quả này cho thấy filter là guardrail đúng đối tượng và đáp ứng yêu cầu L3A, nhưng không phải truy vấn nào cũng làm thay đổi thứ hạng quan sát được.

### Phân tích lỗi chung

1. **Fixed-size — Q1:** Chunk TVU đúng không vào top-3 vì ranh giới ký tự làm yếu tín hiệu tên trường và hành vi rút học phần. Tăng overlap giúp nhưng không giải quyết hoàn toàn việc cắt sai đơn vị ngữ nghĩa.
2. **Sentence — Q2:** Nơi nộp và thời hạn nằm trong chunk đầu, còn chi tiết lệ phí sang chunk tiếp theo. Có thể dùng sentence overlap hoặc gom theo heading.
3. **Heading/recursive — lỗi ban đầu và tối ưu:** Phần mở đầu từng chiếm top-1 nhờ lặp từ khóa, trong khi section chứa bảng ngưỡng điểm bị đẩy xuống sau. Preamble Context Merging đã gộp tên trường/tiêu đề vào section đầu, đưa cả 5 chunk chứa đáp án lên top-1 và tăng kết quả nghiêm ngặt từ 7/10 lên 10/10 trên stress test của Nguyễn Vũ Anh.
4. **Embedding:** `MockEmbedder` cho kết quả gần ngẫu nhiên; lexical hashing tốt với từ khóa/số liệu chính xác nhưng yếu với paraphrase và phủ định. Hướng cải thiện là multilingual neural embedding hoặc hybrid dense + lexical retrieval.

## 4. Demo và bài học nhóm — Nhóm (5 điểm)

Demo sử dụng cùng corpus và hiển thị top-3 cho từng truy vấn, kèm `doc_id`, score, metadata và đoạn nội dung. Nhóm rút ra bốn kết luận:

1. Đúng tài liệu chưa đủ; chunk trong top-3 phải thực sự chứa các `answer_terms` cần thiết.
2. Heading/section là ranh giới ngữ nghĩa tự nhiên cho văn bản quy định và giúp giữ tên trường, tên mục trong từng chunk.
3. Metadata pre-filtering là lớp bảo vệ quan trọng khi corpus có tài liệu cùng chủ đề nhưng khác đối tượng áp dụng.
4. Muốn so sánh chunking công bằng phải giữ nguyên corpus, 5 câu hỏi, embedding backend, `top_k` và quy tắc chấm. Việc các báo cáo cá nhân dùng backend hoặc phiên bản câu hỏi khác nhau là hạn chế của lần thử nghiệm này.

Nếu làm lại, nhóm sẽ chuẩn hóa một script benchmark duy nhất cho cả bốn thành viên, bổ sung `effective_date` và `status=active`, dùng sentence overlap cho các điều khoản liền nhau và thử hybrid retrieval để bắt tốt cả ngữ nghĩa lẫn số liệu.

## Tự đánh giá

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Lựa chọn tài liệu | 10/10 |
| Thiết kế chiến lược | 15/15 |
| Chất lượng truy xuất | 10/10 |
| Thuyết trình | 5/5 |
| **Tổng** | **40/40** |
