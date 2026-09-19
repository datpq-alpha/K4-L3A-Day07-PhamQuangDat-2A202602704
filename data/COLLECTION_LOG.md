# Nhật ký thu thập và làm sạch dữ liệu

## Phạm vi

- Chủ đề: quy định học vụ đại học.
- Ngày lấy dữ liệu ghi trong corpus: `2026-09-19`.
- Đầu vào tái lập: `data/urls.csv` gồm 5 URL công khai duy nhất.
- Corpus cuối: 10 tài liệu đã làm sạch trong `data/academic_regulations/`.
- Crawler chỉ dùng cho HTML/text và phải ghi ra thư mục staging; không ghi đè corpus cuối.
- Lần chạy kiểm chứng ngày `2026-09-19`: 2 nguồn lưu được, 3 nguồn bị bỏ qua; đầu ra chi tiết nằm trong `data/crawl_log.txt`.
- Các nguồn crawler không lấy được đều được đọc, trích xuất và làm sạch thủ công; không vô hiệu hóa `robots.txt` hoặc kiểm tra chứng chỉ SSL.

## Kết quả lần chạy crawler

| Tổng URL | Lưu được | Bỏ qua | Manifest staging | Nhật ký |
|---:|---:|---:|---|---|
| 5 | 2 | 3 | `data/crawl_raw/sources.csv` | `data/crawl_log.txt` |

Crawler được chạy với thư mục đầu ra riêng `data/crawl_raw/`. Vì vậy, lần chạy này không tạo, sửa hoặc ghi đè bất kỳ file nào trong `data/academic_regulations/`.

## Ánh xạ nguồn sang corpus

| # | Nguồn | Phương pháp thu thập | Trạng thái crawler | Tài liệu sau làm sạch | Thao tác làm sạch/tách |
|---|---|---|---|---|---|
| 1 | [TVU — Sổ tay sinh viên](https://cmp.tvu.edu.vn/so-tay-sinh-vien/) | Đọc, trích xuất và làm sạch thủ công từ trang công khai; crawler chỉ dùng để kiểm tra khả năng thu thập tự động | **Bỏ qua** — `disallowed by robots.txt`; không crawl hoặc vượt qua hạn chế | `tvu-course-registration.md`; `tvu-academic-warning.md`; `tvu-grade-appeal.md` | Loại menu, liên kết spam và nội dung ngoài sổ tay; tách thành đăng ký/rút học phần, cảnh báo học vụ và phúc khảo |
| 2 | [QTU — Quy định công tác học vụ](https://qtu.edu.vn/qd-95-ban-hanh-quy-dinh-ve-cong-tac-hoc-vu-tai-truong-dai-hoc-quang-trung/) | Crawler lấy HTML vào thư mục staging, sau đó rà soát và làm sạch thủ công | **Đã lưu** — `data/crawl_raw/source-qtu-academic-affairs.md` | `qtu-academic-affairs-overview.md` | Loại menu/tin liên quan; giữ phạm vi và nội dung học vụ có thể kiểm chứng |
| 3 | [TDMU — QT.09 phúc khảo](https://tdmu.edu.vn/hinh/thuvien/taptin/2-6-2025-4-42-24-pm06-BKTKDDBCL-QT.09-Phuc%20khao%20Bai%20KTr.pdf) | PDF công khai; đọc, trích xuất và làm sạch thủ công | **Bỏ qua** — `unsupported content type: application/pdf`; crawler chỉ hỗ trợ HTML/text | `tdmu-grade-appeal.md`; `tdmu-grade-appeal-operations.md` | Giữ các bước, mốc bảy ngày, lệ phí và cách xử lý điểm; tách hướng dẫn người học (`student`) khỏi vận hành cán bộ (`staff`) |
| 4 | [TNUT — Quy chế chương trình tiên tiến](https://fit.tnut.edu.vn/bai-viet/quy-che-dao-tao-trinh-do-dai-hoc-cho-chuong-trinh-tien-tien-nam-2022-176) | Crawler lấy HTML vào thư mục staging, sau đó rà soát và làm sạch thủ công | **Đã lưu** — `data/crawl_raw/source-tnut-advanced-regulation.md`; bản thô còn menu và nội dung nhiễu | `tnut-advanced-registration.md`; `tnut-advanced-withdrawal-assessment.md` | Loại menu và phần ngoài phạm vi; tách đăng ký tín chỉ khỏi rút học phần/đánh giá |
| 5 | [UFM — Quy chế đào tạo tín chỉ](https://pdt.ufm.edu.vn/dulieu/quiche/1329_Quy_che_dao_tao_tin_chi_tu_khoa_2021.htm) | Đọc, trích xuất và làm sạch thủ công từ trang công khai; crawler chỉ dùng để kiểm tra khả năng thu thập tự động | **Bỏ qua** — không xác minh được `robots.txt` do `SSL: CERTIFICATE_VERIFY_FAILED`; không tắt kiểm tra chứng chỉ | `ufm-course-registration.md`; `ufm-assessment.md` | Loại điều hướng và nội dung ngoài phạm vi; tách tổ chức đăng ký học tập khỏi đánh giá/tính điểm |

## Cách chạy kiểm chứng

Chạy crawler vào thư mục staging để không ghi đè 10 tài liệu đã làm sạch:

```powershell
python -X utf8 scripts/fetch_public_pages.py data/urls.csv `
    --output-dir data/crawl_raw `
    --delay 1.2 2>&1 |
    Tee-Object -FilePath data/crawl_log.txt
```

Diễn giải kết quả:

- `Saved`: URL được `robots.txt` cho phép, trả HTML/text và đã được lưu ở staging.
- `disallowed by robots.txt`: giữ thông báo trong log, không vượt qua hạn chế; thay nguồn nếu cần dùng crawler.
- `unsupported content type`: không dùng crawler cho nguồn đó; TDMU là trường hợp PDF đã biết.
- `cannot verify robots.txt` do lỗi chứng chỉ SSL: không tắt xác minh SSL; tài liệu UFM được xử lý thủ công.
- `extracted content is too short`: trang có thể render bằng JavaScript; đổi nguồn, không cố lấy dữ liệu rỗng.

Không đưa nội dung trong `data/crawl_raw/` vào benchmark trước khi đọc lại và làm sạch. Corpus dùng cho benchmark vẫn là `data/academic_regulations/`, với kiểm kê cuối tại `data/academic_regulations/sources.csv`.

Các file trong `data/academic_regulations/` là corpus sạch đã được tổng hợp ban đầu. Không sao chép tự động bản thô từ `data/crawl_raw/` sang corpus này và không dùng lần chạy crawler để ghi đè chúng.
