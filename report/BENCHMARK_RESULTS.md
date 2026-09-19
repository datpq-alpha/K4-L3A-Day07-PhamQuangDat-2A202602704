# Kết quả Benchmark — Quy định học vụ

## Thiết lập

- Ngày chạy: 19/09/2026
- Corpus: 10 tài liệu trong `data/academic_regulations/`
- Embedding: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Top-k: 3
- Script: `scripts/benchmark_academic_regulations.py`

## Tổng hợp

| Strategy | Chunks | Độ dài TB | Q1 | Q2 | Q3 | Q4 | Q5 | Tổng |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| member_1_fixed_size | 28 | 418,32 | 0 | 2 | 1 | 1 | 0 | 4/10 |
| member_2_sentence | 32 | 322,28 | 0 | 2 | 1 | 2 | 2 | 7/10 |
| member_3_recursive | 30 | 344,10 | 0 | 2 | 2 | 2 | 2 | 8/10 |
| member_4_heading_section | 34 | 352,21 | 2 | 2 | 2 | 2 | 2 | 10/10 |

## Top-3 của heading/section

| Query | Rank 1 | Rank 2 | Rank 3 |
|---|---|---|---|
| Q1 | tvu-course-registration (0,824929) | tvu-grade-appeal (0,703608) | tvu-course-registration (0,702183) |
| Q2 | tdmu-grade-appeal (0,755277) | tdmu-grade-appeal (0,709948) | tdmu-grade-appeal (0,653358) |
| Q3 | tnut-advanced-registration (0,751457) | tvu-course-registration (0,689784) | tdmu-grade-appeal (0,592676) |
| Q4 | ufm-course-registration (0,808949) | ufm-course-registration (0,773463) | ufm-course-registration (0,743790) |
| Q5 | tvu-academic-warning (0,608530) | tnut-advanced-registration (0,592545) | ufm-assessment (0,552939) |

Q2 được chạy với `metadata_filter={"audience": "student"}`. Không lọc, top-3 của heading/section có thêm `tdmu-grade-appeal-operations` dành cho staff.

## Cách chạy lại

```powershell
$env:HF_HUB_OFFLINE = "1"
.\.venv\Scripts\python.exe -X utf8 scripts\benchmark_academic_regulations.py --embedding local
```

Fallback không cần model:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts\benchmark_academic_regulations.py --embedding lexical
```
