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
| member_1_fixed_size | 19 | 603,74 | 0 | 2 | 1 | 2 | 2 | 7/10 |
| member_2_sentence | 32 | 314,72 | 0 | 2 | 1 | 2 | 2 | 7/10 |
| member_3_recursive | 29 | 347,69 | 0 | 2 | 2 | 2 | 2 | 8/10 |
| member_4_heading_section | 34 | 346,24 | 2 | 2 | 2 | 2 | 2 | 10/10 |

## Top-3 của fixed-size `800/150`

| Query | Rank 1 | Rank 2 | Rank 3 |
|---|---|---|---|
| Q1 | tvu-grade-appeal (0,708859) | tnut-advanced-withdrawal-assessment (0,672160) | tvu-academic-warning (0,647443) |
| Q2 | tdmu-grade-appeal (0,653956) | tvu-grade-appeal (0,581826) | ufm-course-registration (0,558608) |
| Q3 | tvu-course-registration (0,665663) | tnut-advanced-registration (0,647664) | ufm-course-registration (0,563713) |
| Q4 | ufm-course-registration (0,754191) | tnut-advanced-registration (0,615509) | tdmu-grade-appeal (0,581395) |
| Q5 | tvu-academic-warning (0,612541) | ufm-assessment (0,586161) | tvu-academic-warning (0,585949) |

## Top-3 của heading/section

| Query | Rank 1 | Rank 2 | Rank 3 |
|---|---|---|---|
| Q1 | tvu-course-registration (0,824929) | tvu-grade-appeal (0,703608) | tvu-course-registration (0,702183) |
| Q2 | tdmu-grade-appeal (0,664990) | tvu-grade-appeal (0,607524) | tdmu-grade-appeal (0,589348) |
| Q3 | tnut-advanced-registration (0,751457) | tvu-course-registration (0,689784) | tvu-academic-warning (0,580658) |
| Q4 | ufm-course-registration (0,808949) | ufm-course-registration (0,773463) | ufm-course-registration (0,743790) |
| Q5 | tvu-academic-warning (0,608530) | tnut-advanced-registration (0,592545) | ufm-assessment (0,552939) |

Q2 không nêu người hỏi và được chạy với `metadata_filter={"audience": "student"}`. Không lọc, top-3 của Recursive và Heading/section có thêm `tdmu-grade-appeal-operations` dành cho staff; lọc trước similarity search loại tài liệu này.

## Cách chạy lại

Checkpoint tối thiểu, không cần model ngoài:

```powershell
python -X utf8 bench.py --baseline
```

```powershell
$env:HF_HUB_OFFLINE = "1"
.\.venv\Scripts\python.exe -X utf8 scripts\benchmark_academic_regulations.py --embedding local
```

Fallback không cần model:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts\benchmark_academic_regulations.py --embedding lexical
```
