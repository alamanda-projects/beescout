# Perbendaharaan Aturan Kualitas (Quality Rules Library)

Dokumen ini adalah **katalog kanonik** aturan kualitas data (quality rules) pada standar Data Contract BeeScout — padanan yang bisa dibaca mesin ada di [`repository/app/addons/catalog_rules/default.json`](../../repository/app/addons/catalog_rules/default.json). Keduanya harus selalu sinkron; ubah bersama-sama.

Perbendaharaan ini mengadopsi pola dari [Sling Data Quality](https://docs.slingdata.io/concepts/data-quality) — constraints level kolom (`value ~ regex`, `value in (...)`, `value > threshold`), pemeriksaan level dataset (row count, freshness), dan escape hatch SQL kustom — diterjemahkan ke bentuk deklaratif BeeScout (`quality[].code` + `custom_properties`).

> **BeeScout menyimpan deklarasi, bukan mengeksekusi.** Aturan pada kontrak adalah kesepakatan; eksekusinya menjadi tanggung jawab engine kualitas eksternal (mis. HoneyGrade) yang membaca kontrak ini.

## Dimensi Kualitas

Enum tertutup, gaya DAMA + `security`:

| Dimensi | Label UI | Makna |
|---|---|---|
| `completeness` | Kelengkapan | Data hadir sesuai volume/kolom yang diharapkan |
| `validity` | Keabsahan | Nilai sesuai format/pola/daftar yang disepakati |
| `accuracy` | Akurasi | Nilai berada dalam rentang yang masuk akal/benar |
| `security` | Keamanan | Data sensitif (PII) terlindungi |
| `uniqueness` | Keunikan | Tidak ada nilai/baris ganda |
| `timeliness` | Ketepatan Waktu | Data cukup segar sesuai kesepakatan |
| `consistency` | Konsistensi | Data konsisten antar sumber/aturan bisnis |

## Ringkasan Perbendaharaan

| Code | Label UI | Layer | Dimensi | Padanan Sling |
|---|---|---|---|---|
| `distinct_check` | Tidak Ada Data Ganda | dataset | completeness | — |
| `count_check` | Jumlah Baris Sesuai | dataset | completeness | — |
| `pii_check` | Data Sensitif Dilindungi | dataset | security | — |
| `row_count_range_check` | Jumlah Baris Dalam Rentang | dataset | completeness | `run.total_rows >= N` (check hook) |
| `freshness_check` | Data Selalu Segar | dataset | timeliness | freshness check hook |
| `custom_sql_check` | Pemeriksaan SQL Kustom | dataset | consistency | query hook |
| `null_check` | Tidak Boleh Kosong | column | completeness | — |
| `format_check` | Format / Panjang Sesuai | column | validity | — |
| `string_check` | Hanya Berisi Teks | column | accuracy | — |
| `date_range_check` | Rentang Tanggal Valid | column | accuracy | — |
| `pattern_check` | Sesuai Pola (Regex) | column | validity | `value ~ '^...$'` |
| `enum_check` | Nilai Dari Daftar | column | validity | `value in ('a', 'b')` |
| `range_check` | Rentang Angka Valid | column | accuracy | `value > threshold` |
| `length_range_check` | Rentang Panjang Sesuai | column | validity | — |
| `unique_check` | Nilai Unik Per Kolom | column | uniqueness | — |

Aturan **dataset** dideklarasikan di `metadata.quality[]`; aturan **column** di `model[].quality[]`. Parameter aturan dibawa lewat `custom_properties` (pasangan `property`/`value`); param bernilai jamak diulang sebagai beberapa entri `property` yang sama (lihat `distinct_check`).

---

## Aturan Level Dataset

### `distinct_check` — Tidak Ada Data Ganda

Kombinasi kolom yang ditentukan harus unik (mendukung keunikan gabungan/composite).

| Param | Wajib | Keterangan |
|---|---|---|
| `field_name` | ya (boleh diulang) | Kolom yang membentuk kunci keunikan |

```yaml
metadata:
  quality:
    - code: distinct_check
      dimension: completeness
      custom_properties:
        - property: field_name
          value: uid
        - property: field_name
          value: join_date
```

### `count_check` — Jumlah Baris Sesuai

Jumlah baris memenuhi kondisi terhadap atribut kolom.

| Param | Wajib | Keterangan |
|---|---|---|
| `field_condition` | ya | `is_nullable=false` \| `is_audit=true` |

### `pii_check` — Data Sensitif Dilindungi

Kolom ber-flag `is_pii: true` pada model harus sudah dilindungi (masking/enkripsi). Kolom terdeteksi otomatis dari model — `field_name` diisi otomatis oleh UI.

### `row_count_range_check` — Jumlah Baris Dalam Rentang

Padanan Sling: `check: "run.total_rows >= 1000"`.

| Param | Wajib | Keterangan |
|---|---|---|
| `min_rows` | tidak | Batas bawah jumlah baris |
| `max_rows` | tidak | Batas atas jumlah baris |

```yaml
metadata:
  quality:
    - code: row_count_range_check
      dimension: completeness
      custom_properties:
        - property: min_rows
          value: "1000"
```

### `freshness_check` — Data Selalu Segar

Data terbaru tidak boleh lebih tua dari umur maksimal.

| Param | Wajib | Keterangan |
|---|---|---|
| `max_age` | ya | Umur maksimal (angka) |
| `age_unit` | ya | `jam` \| `hari` \| `pekan` |
| `timestamp_column` | tidak | Kolom timestamp acuan, mis. `updated_at` |

```yaml
metadata:
  quality:
    - code: freshness_check
      dimension: timeliness
      custom_properties:
        - property: max_age
          value: "24"
        - property: age_unit
          value: jam
        - property: timestamp_column
          value: updated_at
```

### `custom_sql_check` — Pemeriksaan SQL Kustom

Escape hatch ala Sling query hooks: deklarasi query yang dijalankan engine eksternal; BeeScout tidak mengeksekusi SQL apa pun.

| Param | Wajib | Keterangan |
|---|---|---|
| `query` | ya | Query SQL yang dijalankan engine |
| `expectation` | tidak | Hasil yang diharapkan, mis. `= 0` |

```yaml
metadata:
  quality:
    - code: custom_sql_check
      dimension: consistency
      custom_properties:
        - property: query
          value: SELECT COUNT(*) FROM orders WHERE amount < 0
        - property: expectation
          value: "= 0"
```

---

## Aturan Level Kolom

### `null_check` — Tidak Boleh Kosong

| Param | Wajib | Keterangan |
|---|---|---|
| `compare_to` | ya | `total dataset row` \| `specific row count` |
| `comparison_type` | ya | `equal to` \| `less than` |

### `format_check` — Format / Panjang Sesuai

| Param | Wajib | Keterangan |
|---|---|---|
| `length` | ya | Panjang karakter eksak (1–65535) |

### `string_check` — Hanya Berisi Teks

| Param | Wajib | Keterangan |
|---|---|---|
| `contains_only` | ya | `alphabet` \| `numeric` \| `alphanumeric` |

### `date_range_check` — Rentang Tanggal Valid

| Param | Wajib | Keterangan |
|---|---|---|
| `min_date` | tidak | `YYYY-MM-DD` |
| `max_date` | tidak | `YYYY-MM-DD`, atau `today` |

### `pattern_check` — Sesuai Pola (Regex)

Padanan Sling: `email: string | value ~ '^[^@]+@[^@]+\.[^@]+$'`.

| Param | Wajib | Keterangan |
|---|---|---|
| `pattern` | ya | Regular expression |

```yaml
model:
  - column: email
    quality:
      - code: pattern_check
        dimension: validity
        custom_properties:
          - property: pattern
            value: ^[^@]+@[^@]+\.[^@]+$
```

### `enum_check` — Nilai Dari Daftar

Padanan Sling: `status: string | value in ('active', 'pending', 'inactive')`.

| Param | Wajib | Keterangan |
|---|---|---|
| `allowed_values` | ya | Daftar nilai, dipisah koma |

```yaml
model:
  - column: status
    quality:
      - code: enum_check
        dimension: validity
        custom_properties:
          - property: allowed_values
            value: active, pending, inactive
```

### `range_check` — Rentang Angka Valid

Padanan Sling: `amount: decimal | value > 0`.

| Param | Wajib | Keterangan |
|---|---|---|
| `min_value` | tidak | Batas bawah |
| `max_value` | tidak | Batas atas |

### `length_range_check` — Rentang Panjang Sesuai

Pelengkap `format_check` (yang mengunci panjang eksak) untuk rentang min–max.

| Param | Wajib | Keterangan |
|---|---|---|
| `min_length` | tidak | Panjang minimal (0–65535) |
| `max_length` | tidak | Panjang maksimal (1–65535) |

### `unique_check` — Nilai Unik Per Kolom

Setiap nilai kolom harus unik. Tanpa parameter (kolom sudah menjadi konteks). Untuk keunikan gabungan beberapa kolom, gunakan `distinct_check` di level dataset.

---

## Atribut Umum Setiap Aturan

Setiap entri `quality[]` (dataset maupun kolom) membawa:

| Field | Keterangan |
|---|---|
| `code` | Kode aturan dari perbendaharaan ini (atau modul kustom) |
| `description` | Penjelasan bebas |
| `dimension` | Salah satu dari 7 dimensi di atas |
| `impact` | Jenis dampak: `operational` \| `financial` \| `regulatory` \| `reputational` |
| `severity` | Tingkat: `low` \| `medium` \| `high` |
| `on_failure` | Opsional — tindakan engine saat rule gagal, lihat bawah (#151 / [ADR-0008](../../docs/adr/0008-quality-on-failure.md)) |
| `custom_properties` | Parameter aturan (pasangan `property`/`value`) |

## Semantik Kegagalan (`on_failure`)

Adopsi pola Sling: kontrak mendeklarasikan apa yang harus engine lakukan saat sebuah rule gagal. `severity` menyatakan *seberapa penting bagi bisnis*; `on_failure` menyatakan *tindakan mesin* — dua sumbu berbeda (filosofi yang sama dengan pemisahan impact/severity di ADR-0003).

| Nilai | Makna | Layer valid |
|---|---|---|
| `abort` | Hentikan pipeline/proses | dataset & kolom |
| `warn` | Lanjut, dengan peringatan | dataset & kolom |
| `skip` | Buang record/baris bermasalah, lanjut | **hanya kolom** — rule dataset tidak punya record untuk di-skip |
| `quiet` | Diam — catat saja | dataset & kolom |

- **Opsional.** Bila absen, engine memakai fallback dari `severity`: `high → abort`, selainnya `warn`. Kontrak lama tetap bermakna penuh tanpa migrasi.
- Write-path menolak nilai di luar enum, dan menolak `skip` pada `metadata.quality[]` (422).
- Eksekusi tetap tanggung jawab engine eksternal — BeeScout hanya menyimpan deklarasinya.
- ODCS tidak punya padanan field ini — saat export disimpan sebagai argument `beescout_on_failure` (lihat [comparison-odcs.md](./comparison-odcs.md)); converter Sling memetakannya langsung ke `on_failure` hook.

## Modul Kustom

Selain perbendaharaan builtin, admin dapat menambah modul lewat `POST /catalog/rules` (user/developer lewat jalur approval). Modul builtin baru pada rilis BeeScout tidak otomatis masuk ke instalasi berjalan — root dapat menariknya dengan `POST /catalog/seed?sync_missing=true` (idempoten, tidak menyentuh modul yang sudah ada).
