# Audit Pydantic ↔ BeeScout spec (Phase 1 dari #102)

> **Phase 1 = audit & rekomendasi.** Tidak ada perubahan kode produksi di sini. Phase 2 mengeksekusi keputusan per-field; Phase 3 strict YAML validator. Lihat [#102](https://github.com/alamanda-projects/beescout/issues/102).

## Metodologi

1. Spec acuan: [`data-contract/docs/README.md`](../data-contract/docs/README.md) — sumber otoritatif (kolom `Required: YES/NO`).
2. Implementasi: semua file di [`repository/app/model/`](../repository/app/model/).
3. Untuk tiap field:
   - Cocokkan spec required vs Pydantic Optional/required
   - Tag dengan rekomendasi awal (maintainer review per-field)
   - Catat alasan kalau rekomendasi ≠ "match spec persis"
4. **Validator YAML** ([main.py:1510](../repository/app/main.py#L1510)) dicek terpisah — saat ini hanya cek 4 field metadata.

## Legenda tag rekomendasi

| Tag | Arti |
|---|---|
| ✅ **Aligned** | Sudah konsisten. Tidak ada aksi. |
| 🔴 **Make required** | Spec wajib, model harus follow. Migrasi data: back-fill default. |
| 🟡 **Spec relax** | Realita lebih realistis Optional; update spec jadi `Required: NO`. |
| 🟠 **Strict write / lenient read** | Schema baca toleran untuk kontrak lama; schema tulis strict. |
| 🐛 **Type bug** | Type Pydantic salah (bukan masalah required-ness). Fix tanpa breaking. |
| ❓ **Needs decision** | Ambigu, butuh maintainer untuk decide. |

> Rekomendasi awal adalah **draft saya** berdasarkan UX feasibility + persona analysis. Maintainer berhak override.

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
| `purpose` | YES | `Optional[str] = None` | 🟡 Spec relax | Persona Bu Retno mungkin tidak selalu bisa artikulasi purpose. Recommend: spec → NO. Atau kalau insists strict, beri default value yang prompt user fill via UI banner. |
| `usage` | YES | `Optional[str] = None` | 🟡 Spec relax | Sama — `usage` `private`/`public` informasi penting tapi mungkin tidak selalu jelas. Bisa default ke `private` di form. |

### `MetadataConsumer`

| Field | Spec | Pydantic | Tag | Rekomendasi & alasan |
|---|---|---|---|---|
| `name` | YES | `Optional[str] = None` | 🔴 Make required | Tidak masuk akal entry consumer tanpa nama. Migrasi: drop entry yang name kosong. |
| `use_case` | YES | `Optional[str] = None` | 🔴 Make required | Use case adalah alasan keberadaan entry consumer (per ADR-0007). Migrasi: kontrak lama dengan entry tanpa `use_case` perlu admin isi atau drop. |

### `MetadataStakeholders`

| Field | Spec | Pydantic | Tag | Rekomendasi & alasan |
|---|---|---|---|---|
| `name` | YES | `str` (required) | ✅ Aligned | — |
| `email` | YES | `Optional[str] = None` | 🟡 Spec relax | Tidak semua stakeholder punya email organisasi (mis. konsultan). Recommend: spec → NO. |
| `role` | YES | `str` (required) | ✅ Aligned | Enum value enforced di UI; backend tidak validate (open question untuk Phase 3) |
| `username` | (ADR-0004: opsional) | `Optional[str] = None` | ✅ Aligned | Per ADR — opsional di spec, tapi wajib untuk jadi approver |
| `date_in` | YES | `Optional[str] = None` | 🟡 Spec relax | Tracking historis berguna tapi tidak essential. Recommend: spec → NO atau default ke tanggal create. |
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

> **Catatan #103**: `effective_date` & `end_of_contract` direkomendasikan dipindah dari `sla.*` ke top-level metadata. Audit di sini tidak preempt — tunggu keputusan #103 dulu untuk decision final atas dua field tsb.

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
| `effective_date` | YES | `Optional[str] = None` | ⏸ Tunggu #103 | — |
| `end_of_contract` | YES | `Optional[str] = None` | ⏸ Tunggu #103 | — |
| `availability` | — | `Optional[str] = None` | 🐛 Cleanup | Field ini **tidak ada di spec**. Sepertinya legacy/runtime. Drop atau document. |
| `cron` | — | `Optional[str] = None` | 🐛 Cleanup | Duplikatif dengan `frequency_cron`? Cek kode pemakaiannya. |

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
| `is_partition` | YES | `Optional[bool] = None` | 🟡 Spec relax | Tidak setiap kolom relevan dengan partitioning (mis. kolom audit kecil). Recommend: spec → NO, treat sebagai opsional. |
| `is_clustered` | YES | `Optional[bool] = None` | 🟡 Spec relax | Sama dengan partition. |
| `is_pii` | YES | `Optional[bool] = None` | 🔴 Make required | Compliance flag — wajib. Default `False`. |
| `is_audit` | YES | `Optional[bool] = None` | 🟡 Spec relax | Audit flag biasanya hanya untuk kolom `created_at`/`updated_at`. Mayoritas false. Recommend: spec → NO. |
| `is_mandatory` | YES | `Optional[bool] = None` | ❓ Needs decision | Duplikatif dengan `is_nullable`? `is_nullable=false` ≈ `is_mandatory=true`. Maintainer: konsolidasi jadi 1 field atau dokumentasikan beda semantik. |
| `description` | YES | `Optional[str] = None` | 🟡 Spec relax | Kolom dengan nama jelas (`user_id`) kadang tidak butuh deskripsi. Recommend: spec → NO atau lenient. |
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
| 🔴 Make required | 13 |
| 🟡 Spec relax | 9 |
| 🟠 Strict-write/lenient-read | 3 |
| 🐛 Type bug / cleanup | 5 |
| ❓ Needs decision | 2 |
| ⏸ Tunggu #103 | 2 |

## Per-field decision sheet (untuk maintainer)

Setelah review draft di atas, maintainer tinggal isi kolom **Keputusan** per field. Saya bisa generate Phase 2 PR(s) berdasarkan keputusan:

| File | Field | Rekomendasi | Keputusan | Catatan |
|---|---|---|---|---|
| metadata.py | `description.purpose` | 🟡 Spec relax | ☐ Make required ☐ Spec relax ☐ Other | |
| metadata.py | `description.usage` | 🟡 Spec relax | ☐ Make required ☐ Spec relax ☐ Other | |
| metadata.py | `consumer[].name` | 🔴 Make required | ☐ Make required ☐ Spec relax ☐ Other | |
| metadata.py | `consumer[].use_case` | 🔴 Make required | ☐ Make required ☐ Spec relax ☐ Other | |
| metadata.py | `stakeholders[].email` | 🟡 Spec relax | ☐ Make required ☐ Spec relax ☐ Other | |
| metadata.py | `stakeholders[].date_in` | 🟡 Spec relax | ☐ Make required ☐ Spec relax ☐ Other | |
| metadata.py | `sla.availability_*` (3 field) | 🔴 Make required | ☐ Make required ☐ Spec relax ☐ Other | |
| metadata.py | `sla.frequency` + `frequency_unit` | 🔴 Make required | ☐ Make required ☐ Spec relax ☐ Other | |
| metadata.py | `sla.retention` + `retention_unit` | 🔴 Make required | ☐ Make required ☐ Spec relax ☐ Other | |
| metadata.py | `sla.effective_date` / `end_of_contract` | ⏸ #103 | (tunggu #103) | |
| metadata.py | `sla.availability` / `cron` | 🐛 Cleanup | ☐ Drop ☐ Document | Tidak ada di spec |
| metadata.py | `contract_reference` type | 🐛 Type bug | ☐ Fix type | List[{number,type}] |
| metadata.py | `stakeholders[]` container | 🔴 Make required | ☐ Make required ☐ Other | Min 1 stakeholder owner |
| metadata.py | `description` container | 🟠 Strict-write | ☐ Strict-write ☐ Other | |
| metadata.py | `consumer` container | 🟠 Strict-write | ☐ Strict-write ☐ Other | |
| metadata.py | `sla` container | 🟠 Strict-write | ☐ Strict-write ☐ Other | |
| model.py | `logical_type` | 🔴 Make required | ☐ Make required ☐ Spec relax ☐ Other | |
| model.py | `physical_type` | 🔴 Make required | ☐ Make required ☐ Spec relax ☐ Other | |
| model.py | `is_primary` | 🔴 Make required (default false) | ☐ Make required ☐ Other | |
| model.py | `is_nullable` | 🔴 Make required (default true) | ☐ Make required ☐ Other | |
| model.py | `is_partition` | 🟡 Spec relax | ☐ Make required ☐ Spec relax ☐ Other | |
| model.py | `is_clustered` | 🟡 Spec relax | ☐ Make required ☐ Spec relax ☐ Other | |
| model.py | `is_pii` | 🔴 Make required (default false) | ☐ Make required ☐ Other | |
| model.py | `is_audit` | 🟡 Spec relax | ☐ Make required ☐ Spec relax ☐ Other | |
| model.py | `is_mandatory` | ❓ Konsolidasi dgn `is_nullable`? | ☐ Konsolidasi ☐ Keep both ☐ Other | |
| model.py | `description` | 🟡 Spec relax | ☐ Make required ☐ Spec relax ☐ Other | |
| examples.py | `type` & `data` defaults | 🐛 Type bug | ☐ Fix `= None` | Pydantic v2 syntax |
| all.py | `examples` container | 🟡 Spec relax | ☐ Optional ☐ Required | |
| all.py | `ports` container | ❓ Needs decision | ☐ Required ☐ Optional | Kontrak file-only tanpa stream? |
| all.py | Shadow class cleanup | 🐛 Cleanup | ☐ Cleanup | Lines 53, 59, 65 |

## Phase 2 plan (setelah keputusan per-field)

Dipecah jadi 2-3 sub-PR berdasarkan keputusan:

1. **PR-A: Type bugs & cleanup** (low risk, no breaking)
   - `contract_reference` type fix
   - `examples.{type,data}` default fix
   - Drop / document `sla.availability` & `sla.cron`
   - Cleanup shadow class di `all.py`
2. **PR-B: Make required group**
   - Update Pydantic model
   - Backfill migration script untuk default value
   - Update FE zod schema + form wizard
   - Run migration di production
3. **PR-C: Spec relax group**
   - Update `data-contract/docs/README.md` field-field yang dipilih jadi `Required: NO`
   - Bump `standard_version` (minor — backward-compatible relaxation)

## Phase 3 plan (setelah Phase 2 deploy)

Strict YAML validator di [`main.py:1510`](../repository/app/main.py#L1510) extend cek field-field hasil keputusan Phase 1/2. Saat ini cuma 4 field metadata.

## Hubungan dengan issue lain

- **#103** (periode kontrak) — `sla.effective_date` & `end_of_contract` decision pending. Audit ini menandai ⏸ untuk 2 field tsb.
- **#94 Phase 3** — overlap area `consumer[]` (documentary per ADR-0007). Konsumer field decision di sini harus konsisten.
- **#100 / #101** (konverter ODCS↔BeeScout) — converter behavior berbeda kalau field jadi required vs tidak; tunggu Phase 2 selesai.
- **#99** (mapping ODCS) — sudah PR #107, sibling.

## Untuk maintainer

Action item: **review kolom Rekomendasi di Per-field decision sheet, isi kolom Keputusan**. Saya generate PR Phase 2 berdasarkan keputusan. Bisa di-cherry-pick per group (mulai dari 🐛 type bug yang low-risk) atau all-at-once.
