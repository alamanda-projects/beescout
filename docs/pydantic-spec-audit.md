# Audit Pydantic ↔ BeeScout spec (Phase 1 dari #102)

> **Phase 1 = audit & rekomendasi.** Tidak ada perubahan kode produksi di sini. Phase 2 mengeksekusi keputusan per-field; Phase 3 strict YAML validator. Lihat [#102](https://github.com/alamanda-projects/beescout/issues/102).

## Prinsip (dari maintainer feedback)

> **Pertahankan BeeScout standard sebagai otoritas.** Pydantic, FE zod, dan YAML validator harus follow spec — bukan sebaliknya. Default rekomendasi semua field spec-YES = **🔴 Make required**. Spec relax hanya kalau maintainer eksplisit flag setelah review (bukan default).

Per-field tetap perlu maintainer review untuk konfirmasi mandatory vs non-mandatory — direction-nya sudah jelas (ikuti spec), yang di-review adalah **edge case** yang mungkin perlu UX exception.

## Metodologi

1. Spec acuan: [`data-contract/docs/README.md`](../data-contract/docs/README.md) — sumber otoritatif (kolom `Required: YES/NO`).
2. Implementasi: semua file di [`repository/app/model/`](../repository/app/model/).
3. Untuk tiap field:
   - Cocokkan spec required vs Pydantic Optional/required
   - **Default rekomendasi**: match spec persis (kalau spec YES → 🔴 make required)
   - Maintainer override → flag 🟡 dengan alasan tertulis
4. **Validator YAML** ([main.py:1510](../repository/app/main.py#L1510)) dicek terpisah — saat ini hanya cek 4 field metadata, akan extend di Phase 3.

## Legenda tag

| Tag | Arti | Default? |
|---|---|---|
| ✅ **Aligned** | Sudah konsisten. Tidak ada aksi. | — |
| 🔴 **Make required** | Spec wajib, model harus follow. Migrasi data: back-fill default value. | **Default untuk semua spec-YES** |
| 🟡 **Override-relax** | Maintainer eksplisit minta relax karena UX/edge case khusus. Spec di-update jadi NO + alasan. | Hanya kalau di-flag eksplisit |
| 🟠 **Strict-write / lenient-read** | Schema baca toleran untuk kontrak lama; schema tulis strict. Untuk container field. | Untuk container |
| 🐛 **Type bug / cleanup** | Type Pydantic salah atau orphan field. Fix tanpa breaking semantik. | — |
| ❓ **Needs decision** | Ambigu (mis. dua field redundant). | — |
| ⏸ **Pending issue lain** | Menunggu keputusan di issue lain (mis. #103). | — |

> **Perubahan dari draft awal**: sebelumnya saya draft beberapa field sebagai 🟡 spec relax berdasarkan UX feasibility. Per maintainer feedback, default dibalik: semua spec-YES = 🔴 make required. Tabel di bawah sudah di-reframe sesuai prinsip ini.

---

## 1. `all.py` — `All` (root model)

[`repository/app/model/all.py`](../repository/app/model/all.py)

| Field | Spec | Pydantic | Tag | Rekomendasi & alasan |
|---|---|---|---|---|
| `standard_version` | YES | `str` (required) | ✅ Aligned | — |
| `contract_number` | YES | `str` (required) | ✅ Aligned | — |
| `metadata` | YES | `Metadata` (required) | ✅ Aligned | — |
| `model` | YES (di spec section Model) | `List[Model]` (required) | ✅ Aligned | Lihat catatan model 1 minimum di bawah |
| `ports` | (tidak di spec sebagai wajib top-level) | `List[Ports]` (required) | ❓ Needs decision | Spec implisit di section Ports tapi tidak tag YES top-level. Apakah kontrak harus selalu punya `ports[]` non-kosong? Mungkin tidak (kontrak format file tanpa stream). |
| `examples` | NO (section opsional) | `Examples` (required) | 🟡 Spec relax / 🐛 | Pydantic memaksa object `examples` selalu ada padahal spec opsional. Recommend: ubah jadi `Optional[Examples] = None`. |
| `created_by` | (runtime field, bukan spec) | `Optional[str] = None` | ✅ Aligned | — |
| `managers` | (runtime field) | `Optional[List[str]] = None` | ✅ Aligned | — |
| `approval_status` | (runtime field) | `Optional[str] = None` | ✅ Aligned | — |
| `pending_changes` | (runtime field) | `Optional[dict] = None` | ✅ Aligned | — |
| `pending_by` | (runtime field) | `Optional[str] = None` | ✅ Aligned | — |

**Bug kecil di file**: kelas `Ports` (line 53), `Examples` (line 59), `Dbtschema` (line 65) di `all.py` punya **nama yang sama** dengan kelas yang di-import dari `ports.py` & `examples.py`. Ini shadowing — tidak ada bug runtime karena class di-import & dipakai di `All`, lalu shadow class baru tidak di-export. Tapi cleanup direkomendasikan saat Phase 2.

---

## 2. `metadata.py` — `Metadata` & nested

[`repository/app/model/metadata.py`](../repository/app/model/metadata.py)

### `Metadata` (root)

| Field | Spec | Pydantic | Tag | Rekomendasi & alasan |
|---|---|---|---|---|
| `version` | YES | `str` (required) | ✅ Aligned | — |
| `type` | YES | `str` (required) | ✅ Aligned | — |
| `name` | YES | `str` (required) | ✅ Aligned | — |
| `owner` | YES | `str` (required) | ✅ Aligned | — |
| `consumption_mode` | NO | `Optional[str] = None` | ✅ Aligned | — |
| `description` | (section YES via field-nya) | `Optional[MetadataDescription] = None` | 🟠 Strict-write | Field-field di dalam description = YES; tapi container-nya Pydantic Optional. Kontrak lama mungkin tidak punya description block sama sekali → kalau strict, semua kontrak lama 422. **Recommend**: keep Optional pada level container, strict di field-field anak (lihat MetadataDescription). |
| `consumer` | (section YES) | `Optional[List[MetadataConsumer]] = None` | 🟠 Strict-write | Sama dengan description — container Optional, isi strict. Per [ADR-0007](adr/0007-consumer-producer-representation.md), `consumer[]` murni documentary; tetap penting untuk diisi. |
| `stakeholders` | (section YES) | `Optional[List[MetadataStakeholders]] = None` | 🔴 Make required | Setiap kontrak harus punya minimal 1 stakeholder (owner). ADR-0005/0007 mengandalkan stakeholders untuk approval & access. Migrasi: backfill dari `owner` string + admin user. |
| `quality` | (section opsional) | `Optional[List[MetadataQuality]] = None` | ✅ Aligned | — |
| `sla` | (section YES) | `Optional[MetadataSla] = None` | 🟠 Strict-write | Container Optional, isi sebagian strict (lihat MetadataSla). |
| `prev_contract` | NO | `Optional[str] = None` | ✅ Aligned | — |
| `contract_reference` | NO | `Optional[List[str]] = None` | 🐛 Type bug | Spec: `List[{number, type}]` (objects). Pydantic: `List[str]`. **Type harus diperbaiki** — bikin `MetadataContractReference(BaseModel)` dengan `number` & `type`. Tidak breaking pada DB karena field opsional. |

### `MetadataDescription`

| Field | Spec | Pydantic | Tag | Rekomendasi & alasan |
|---|---|---|---|---|
| `purpose` | YES | `Optional[str] = None` | 🔴 Make required | Bu Retno mungkin awalnya susah artikulasi, tapi spec wajib → FE wizard harus paksa isi (placeholder yang membantu, mis. "Untuk analisis bulanan tim sales"). Migrasi: backfill kontrak lama dengan string default "(belum diisi — mohon dilengkapi)" + UI banner notifikasi steward. |
| `usage` | YES | `Optional[str] = None` | 🔴 Make required | Spec wajib (`private`/`public`). FE wizard default ke `private` untuk meminimalkan klik. Migrasi: backfill kontrak lama dengan `private` (safe default). |

### `MetadataConsumer`

| Field | Spec | Pydantic | Tag | Rekomendasi & alasan |
|---|---|---|---|---|
| `name` | YES | `Optional[str] = None` | 🔴 Make required | Tidak masuk akal entry consumer tanpa nama. Migrasi: drop entry yang name kosong. |
| `use_case` | YES | `Optional[str] = None` | 🔴 Make required | Use case adalah alasan keberadaan entry consumer (per ADR-0007). Migrasi: kontrak lama dengan entry tanpa `use_case` perlu admin isi atau drop. |

### `MetadataStakeholders`

| Field | Spec | Pydantic | Tag | Rekomendasi & alasan |
|---|---|---|---|---|
| `name` | YES | `str` (required) | ✅ Aligned | — |
| `email` | YES | `Optional[str] = None` | 🔴 Make required | Spec wajib. Konsultan eksternal yang tidak punya email organisasi tetap bisa diisi email pribadi/freelance. UI: input wajib dengan validasi format email. Migrasi: backfill kontrak lama dengan placeholder `unknown@beescout.local` + flag review. |
| `role` | YES | `str` (required) | ✅ Aligned | Enum value enforced di UI; backend tidak validate (open question untuk Phase 3) |
| `username` | (ADR-0004: opsional) | `Optional[str] = None` | ✅ Aligned | Per ADR — opsional di spec, tapi wajib untuk jadi approver |
| `date_in` | YES | `Optional[str] = None` | 🔴 Make required | Spec wajib untuk audit trail historis (kapan stakeholder ditugaskan). FE wizard: default ke `datetime.now()` saat tambah stakeholder — admin tinggal accept atau ubah. Backend: bisa server-side default kalau client kirim null. |
| `date_out` | NO | `Optional[str] = None` | ✅ Aligned | — |

### `MetadataQuality` & `MetadataQualityCustom`

| Field | Spec | Pydantic | Tag | Catatan |
|---|---|---|---|---|
| `code` | NO (di spec, "code name" optional) | `Optional[str] = None` | ✅ Aligned | — |
| `description` | NO | `Optional[str] = None` | ✅ Aligned | — |
| `dimension` | NO | `Optional[str] = None` | ✅ Aligned | Enum closed `[completeness, validity, accuracy]` |
| `impact` | NO | `Optional[str] = None` | ✅ Aligned | Per ADR-0003 — enum `[operational, financial, regulatory, reputational]` |
| `severity` | (added via ADR-0003) | `Optional[str] = None` | ✅ Aligned | Enum `[low, medium, high]` |
| `custom_properties` | NO | `Optional[List[...]] = None` | ✅ Aligned | — |

### `MetadataSla`

> **Update #103 (Opsi A, standard_version 0.5.0)**: `effective_date` & `end_of_contract` sudah dipindah dari `sla.*` ke top-level `metadata.*`, dan `end_of_contract` di-rename `expiry_date`. PR-A (spec doc) merged. Pydantic update untuk dua field tsb masuk ke PR-B #103 (bareng migration). Field-field SLA lain (availability/frequency/retention) tetap di-audit normal di tabel ini.

| Field | Spec | Pydantic | Tag | Rekomendasi |
|---|---|---|---|---|
| `availability_start` | YES | `Optional[int] = None` | 🔴 Make required | Operasional SLA dasar |
| `availability_end` | YES | `Optional[int] = None` | 🔴 Make required | Sama |
| `availability_unit` | YES | `Optional[str] = None` | 🔴 Make required | Sama — enum `[h, d]` |
| `frequency` | YES | `Optional[int] = None` | 🔴 Make required | — |
| `frequency_unit` | YES | `Optional[str] = None` | 🔴 Make required | Enum `[m, h, d]` |
| `frequency_cron` | NO | `Optional[str] = None` | ✅ Aligned | — |
| `retention` | YES | `Optional[int] = None` | 🔴 Make required | Wajib untuk compliance |
| `retention_unit` | YES | `Optional[str] = None` | 🔴 Make required | Enum `[tahun, bulan, pekan, hari, jam]` |
| ~~`effective_date`~~ | — | (di MetadataSla) | 🔁 Pindah | Naik ke top-level `Metadata` (PR-B #103) |
| ~~`end_of_contract`~~ | — | (di MetadataSla) | 🔁 Pindah + rename | Naik ke top-level `Metadata` sebagai `expiry_date` (PR-B #103) |
| `availability` | — | `Optional[str] = None` | 🐛 Cleanup | Field ini **tidak ada di spec**. Sepertinya legacy/runtime. Drop atau document. |
| `cron` | — | `Optional[str] = None` | 🐛 Cleanup | Duplikatif dengan `frequency_cron`? Cek kode pemakaiannya. |

### `Metadata` (top-level lifecycle, **baru** di standard_version 0.5.0)

| Field | Spec | Pydantic | Tag | Rekomendasi |
|---|---|---|---|---|
| `effective_date` | YES | `str` (PR-C) | ✅ Aligned | Tanggal mulai berlaku (#103) — required di Pydantic + strict YAML validator + FE wizard expose. Compat shim auto-promote legacy `sla.effective_date`. |
| `expiry_date` | YES | `str` (PR-C) | ✅ Aligned | Tanggal berakhir (#103) — required di Pydantic + strict YAML validator + FE wizard expose. Compat shim auto-promote legacy `sla.end_of_contract`. |

---

## 3. `model.py` — `Model` & nested

[`repository/app/model/model.py`](../repository/app/model/model.py)

### `Model` (kolom)

| Field | Spec | Pydantic | Tag | Rekomendasi |
|---|---|---|---|---|
| `column` | YES | `str` (required) | ✅ Aligned | — |
| `business_name` | NO | `Optional[str] = None` | ✅ Aligned | — |
| `logical_type` | YES | `Optional[str] = None` | 🔴 Make required | Field paling fundamental kolom. Migrasi: backfill `"string"` sebagai default sebelum strict. |
| `physical_type` | YES | `Optional[str] = None` | 🔴 Make required | Sama — backfill `"varchar(255)"` atau prompt admin. |
| `is_primary` | YES | `Optional[bool] = None` | 🔴 Make required | Default `False`. |
| `is_nullable` | YES | `Optional[bool] = None` | 🔴 Make required | Default `True`. |
| `is_partition` | YES | `Optional[bool] = None` | 🔴 Make required (default `false`) | Spec wajib — true/false adalah keputusan eksplisit per kolom. UI: checkbox default unchecked. Migrasi: backfill `false` di semua kolom kontrak lama (asumsi aman). |
| `is_clustered` | YES | `Optional[bool] = None` | 🔴 Make required (default `false`) | Sama dengan partition — keputusan eksplisit. |
| `is_pii` | YES | `Optional[bool] = None` | 🔴 Make required | Compliance flag — wajib. Default `False`. |
| `is_audit` | YES | `Optional[bool] = None` | 🔴 Make required (default `false`) | Spec wajib. Mayoritas kolom `false` — UI default unchecked. Audit kolom (mis. `created_at`) admin explicit check. Migrasi: backfill `false`. |
| `is_mandatory` | YES | `Optional[bool] = None` | ❓ Needs decision | Duplikatif dengan `is_nullable`? `is_nullable=false` ≈ `is_mandatory=true`. Maintainer: konsolidasi jadi 1 field atau dokumentasikan beda semantik. |
| `description` | YES | `Optional[str] = None` | 🔴 Make required | Spec wajib — meskipun nama kolom jelas, deskripsi bisnis tetap berguna untuk persona non-IT (Mbak Indah). UI: textarea wajib. Migrasi: backfill dengan business_name + " (deskripsi otomatis dari nama)" sebagai prompt admin lengkapi. |
| `quality` | NO | `Optional[List[ModelQuality]] = None` | ✅ Aligned | — |
| `sample_value` | NO | `Optional[List[str]] = None` | ✅ Aligned | — |
| `tags` | NO | `Optional[List[str]] = None` | ✅ Aligned | — |

### `ModelQuality` & `ModelQualityCustom`

Identik struktur dengan `MetadataQuality` — semua spec NO, Pydantic Optional. ✅ Aligned.

---

## 4. `ports.py`

[`repository/app/model/ports.py`](../repository/app/model/ports.py)

| Field | Spec | Pydantic | Tag |
|---|---|---|---|
| `object` | YES | `str` (required) | ✅ Aligned |
| `properties` | YES (via .property + .value) | `List[PortsProperties]` (required) | ✅ Aligned |
| `properties[].property` | YES | `str` (required) | ✅ Aligned |
| `properties[].value` | YES | `Union[str, int]` (required) | ✅ Aligned |

---

## 5. `examples.py`

[`repository/app/model/examples.py`](../repository/app/model/examples.py)

| Field | Spec | Pydantic | Tag | Rekomendasi |
|---|---|---|---|---|
| `type` | NO | `Optional[str]` (no default!) | 🐛 Type bug | Pydantic v2 butuh default value untuk Optional. Fix: `Optional[str] = None`. |
| `data` | NO | `Optional[str]` (no default!) | 🐛 Type bug | Sama. |

> Bukan field bug, ini API/Pydantic correctness. Quick fix.

---

## 6. `users.py`, `approval.py`, `domains.py`, `rule_catalog.py`

Bukan bagian dari "BeeScout data contract spec" — ini model runtime untuk fitur app (user, approval, domain, catalog). Audit di luar scope #102 karena tidak ada `data-contract/docs/README.md` reference untuk required-ness. Tetap valid untuk audit follow-up terpisah kalau ada concern, tapi tidak terkait spec compliance.

---

## Ringkasan rekomendasi

| Tag | Count |
|---|---|
| ✅ Aligned (no action) | 26 |
| 🔴 Make required (default sesuai spec) | 22 |
| 🟡 Override-relax (kosong — maintainer flag) | 0 |
| 🟠 Strict-write/lenient-read | 3 |
| 🐛 Type bug / cleanup | 5 |
| ❓ Needs decision | 2 |
| ⏸ Tunggu #103 | 2 |

## Per-field decision sheet (untuk maintainer)

Default rekomendasi sudah di-set match spec. Maintainer hanya perlu **flag eksplisit field yang minta override-relax** dengan alasan (kolom Keputusan). Field yang dibiarkan = setuju dengan rekomendasi default.

| File | Field | Default Rekomendasi | Keputusan | Catatan |
|---|---|---|---|---|
| metadata.py | `description.purpose` | 🔴 Make required | ☐ Setuju ☐ Override-relax (alasan: …) | |
| metadata.py | `description.usage` | 🔴 Make required (default `private`) | ☐ Setuju ☐ Override-relax | |
| metadata.py | `consumer[].name` | 🔴 Make required | ☐ Setuju ☐ Override-relax | |
| metadata.py | `consumer[].use_case` | 🔴 Make required | ☐ Setuju ☐ Override-relax | |
| metadata.py | `stakeholders[].email` | 🔴 Make required | ☐ Setuju ☐ Override-relax | |
| metadata.py | `stakeholders[].date_in` | 🔴 Make required (server-default now) | ☐ Setuju ☐ Override-relax | |
| metadata.py | `sla.availability_*` (3 field) | 🔴 Make required | ☐ Setuju ☐ Override-relax | |
| metadata.py | `sla.frequency` + `frequency_unit` | 🔴 Make required | ☐ Setuju ☐ Override-relax | |
| metadata.py | `sla.retention` + `retention_unit` | 🔴 Make required | ☐ Setuju ☐ Override-relax | |
| metadata.py | `metadata.effective_date` / `expiry_date` (top-level) | 🆕 Add + required | ☑ Disetujui (Opsi A, PR-A merged) | Lokasi & nama final via #103 PR-A; Pydantic add di PR-B |
| metadata.py | `sla.availability` / `cron` | 🐛 Cleanup | ☑ Documented (PR #109) | UI aliases, konsolidasi defer ke PR-B |
| metadata.py | `contract_reference` type | 🐛 Type bug | ☑ Fixed (PR #109) | Nested class `MetadataContractReference{number, type}` |
| metadata.py | `stakeholders[]` container | 🔴 Make required | ☐ Setuju ☐ Override-relax | Min 1 stakeholder owner |
| metadata.py | `description` container | 🟠 Strict-write | ☐ Setuju ☐ Other | |
| metadata.py | `consumer` container | 🟠 Strict-write | ☐ Setuju ☐ Other | |
| metadata.py | `sla` container | 🟠 Strict-write | ☐ Setuju ☐ Other | |
| model.py | `logical_type` | 🔴 Make required | ☐ Setuju ☐ Override-relax | |
| model.py | `physical_type` | 🔴 Make required | ☐ Setuju ☐ Override-relax | |
| model.py | `is_primary` | 🔴 Make required (default `false`) | ☐ Setuju ☐ Override-relax | |
| model.py | `is_nullable` | 🔴 Make required (default `true`) | ☐ Setuju ☐ Override-relax | |
| model.py | `is_partition` | 🔴 Make required (default `false`) | ☐ Setuju ☐ Override-relax | |
| model.py | `is_clustered` | 🔴 Make required (default `false`) | ☐ Setuju ☐ Override-relax | |
| model.py | `is_pii` | 🔴 Make required (default `false`) | ☐ Setuju ☐ Override-relax | |
| model.py | `is_audit` | 🔴 Make required (default `false`) | ☐ Setuju ☐ Override-relax | |
| model.py | `is_mandatory` | ❓ Konsolidasi dgn `is_nullable`? | ☐ Konsolidasi ☐ Keep both ☐ Other | |
| model.py | `description` | 🔴 Make required | ☐ Setuju ☐ Override-relax | |
| examples.py | `type` & `data` defaults | 🐛 Type bug | ☑ Fixed (PR #109) | Pydantic v2 default |
| all.py | `examples` container | 🟡 Spec NO → keep Optional | ☐ Setuju ☐ Other | Spec sendiri opsional |
| all.py | `ports` container | ❓ Needs decision | ☐ Required ☐ Optional | Kontrak file-only tanpa stream? |
| all.py | Shadow class cleanup | 🟠 Defer | Skipped — intentional wrapping pattern utk display.py (lihat note PR #109) | Re-evaluate kalau ada refactor |

## Phase 2 plan (eksekusi)

Dipecah jadi 3 sub-PR.

### ✅ PR-A — Type bugs & cleanup — **MERGED via [#109](https://github.com/alamanda-projects/beescout/pull/109)**

3 fix shipped:
- `metadata.contract_reference` type → nested class `MetadataContractReference{number, type}`
- `examples.{type, data}` Pydantic v2 default = None
- `sla.availability` & `cron` documented sebagai UI aliases

Shadow class di `all.py` skipped (intentional wrapping pattern; bukan bug).

### PR-B — Make required group (sesuai spec)

**Status**: 🚧 in-progress. Maintainer setuju "no override" (semua 🔴 → required).

**Pendekatan final (revisi dari draft "Pydantic required + migration")**: ikut pola berlapis yang sudah ada di codebase (#103, #114-T1.3, lihat docstring `metadata.py` Metadata) — **Pydantic tetap `Optional` (lenient read, tanpa migration)**, enforcement required di **write-path** (`/datacontract/add` & `/update`) + **FE zod**. Ini menghindari breakage read kontrak legacy & migration berisiko. **YAML validator** = #102 Phase 3 (terpisah).

Di-ship per slice (PR kecil, review mobile):

- ✅ **Slice 1 — `metadata.description.purpose` + `usage`** (PR #124): FE zod required + label `*` + error inline (4 form) + step-0 trigger; write-time 422 di add/update; test. Tanpa migration (friksi edit legacy hanya 2 field).
- ✅ **Slice 2 — `stakeholders.email` required** (PR #126): helper `requiredEmailField` + 4 form (label `*`, error inline sudah dari #122); write-time 422 di add/update (presence check per stakeholder ber-name, mirror pola `date_in`); test. **Tanpa backfill** (tidak inject email palsu) — friksi: edit kontrak legacy tanpa email stakeholder wajib mengisi. Backfill placeholder = follow-up bila maintainer minta.
- ⏳ **Slice 3 — `model.logical_type` + `physical_type`** (sudah di-expose wizard) — friksi sedang.
- ⏳ **Slice 4 — `model.description`** (per-kolom, friksi tinggi) → butuh backfill migration.
- ⏳ **Slice 5 — SLA spec fields** (`availability_*`, `frequency_unit`, `retention_unit`) → wizard pakai UI alias, perlu refactor expose field spec dulu.
- ⏳ `stakeholders.date_in` ✅ sudah (#114 T1.3); `model.is_*` flags = boolean default, tidak butuh write-check.

Scope draft awal (untuk referensi):
- Update Pydantic model: spec-YES jadi required (atau dengan default value untuk bool yang punya safe default mis. `is_partition=false`).
- Update FE zod schema + form wizard di 4 page (admin+user × new+edit). Field yang **belum di-expose** dan jadi required:
  - `description.purpose` & `description.usage` (wizard belum ada step "Deskripsi" eksplisit)
  - `stakeholders.email` (sudah ada, tapi mandatori-kan)
  - `stakeholders.date_in` (server-side default ke `datetime.now()`)
  - `sla.availability_start/end/unit`, `frequency`, `frequency_unit`, `retention`, `retention_unit` (wizard saat ini pakai UI aliases `availability` & `cron` — perlu refactor expose field spec)
  - Semua `model.is_*` flags (sudah ada di FE, mandatori-kan)
- Migration script `repository/scripts/migrate_pydantic_strict.py`:
  - Backfill default value sesuai catatan kolom Catatan di tabel di atas
  - Dry-run default; `--apply` execute. Idempoten.
- Bump `metadata.version` per [CLAUDE.md Schema Versioning](../CLAUDE.md) — major (breaking)
- Bump `standard_version` di [`data-contract/`](../data-contract/) — minor (relax-checking yang sebelumnya tidak strict)

### PR-C — Override-relax & spec update (hanya jika maintainer flag)

Kalau maintainer flag 1+ field untuk override-relax:
- Update [`data-contract/docs/README.md`](../data-contract/docs/README.md): field tsb `Required: YES` → `NO` dengan rationale tertulis
- Bump `standard_version` (minor — backward-compatible relax)
- Pydantic untuk field tsb stay Optional

## Phase 3 plan (setelah Phase 2 deploy)

Strict YAML validator di [`main.py:1510`](../repository/app/main.py#L1510) extend cek semua field hasil keputusan Phase 1/2. Saat ini cuma 4 field metadata; harus diperluas ke ~30 field wajib.

## Hubungan dengan issue lain

- **[#103](https://github.com/alamanda-projects/beescout/issues/103)** (periode kontrak) — Opsi A diputuskan & PR-A (spec) merged. Field naik ke top-level `metadata.{effective_date, expiry_date}` di `standard_version` 0.5.0. Pydantic add (top-level) + drop dari `MetadataSla` masuk PR-B #103.
- **[#94 Phase 3](https://github.com/alamanda-projects/beescout/issues/94)** — overlap area `consumer[]` (documentary per [ADR-0007](adr/0007-consumer-producer-representation.md)). Konsumer field decision di sini harus konsisten.
- **[#100](https://github.com/alamanda-projects/beescout/issues/100) / [#101](https://github.com/alamanda-projects/beescout/issues/101)** (konverter ODCS↔BeeScout) — converter behavior bergantung field required/optional di model BeeScout; tunggu Phase 2 PR-B selesai.
- **[#99](https://github.com/alamanda-projects/beescout/issues/99) (mapping ODCS)** — ✅ shipped via PR #107.
- **[#109](https://github.com/alamanda-projects/beescout/pull/109) (Phase 2 PR-A)** — ✅ merged. Type bugs cleanup selesai.

## Untuk maintainer

**Status saat ini**:
- ✅ Phase 1 audit (this doc) — ready to merge
- ✅ Phase 2 PR-A (type bugs) — merged via #109
- ⏳ Phase 2 PR-B (make-required group) — menunggu review decision sheet di atas

**Action item next**: review tabel Per-field decision sheet. Default = match spec (🔴 make required). Cukup **flag eksplisit field yang minta override-relax** dengan alasan UX. Tanpa flag = setuju dengan default → saya generate PR-B dengan asumsi semua 🔴 jadi required.

Komen "lanjut tanpa override" di PR #108 = sinyal saya untuk mulai eksekusi PR-B.
