# ADR-0007: Konsolidasi representasi konsumen/produser kontrak

**Status**: Accepted
**Tanggal**: 2026-05-26
**Decider**: @haninp
**Related**: Issue [#76](https://github.com/alamanda-projects/beescout/issues/76), [#92](https://github.com/alamanda-projects/beescout/issues/92), [#94](https://github.com/alamanda-projects/beescout/issues/94)

---

## Konteks

### Acuan standar

Standar rujukan BeeScout adalah **[`/data-contract/`](../../data-contract/README.md)** — spec internal yang sengaja dipisah dari ODCS. Lihat [`data-contract/docs/README.md`](../../data-contract/docs/README.md) untuk definisi lengkap field, dan [`data-contract/examples/full.yaml`](../../data-contract/examples/full.yaml) untuk contoh kanonik.

ODCS ([Open Data Contract Standard](https://github.com/bitol-io/open-data-contract-standard)) adalah referensi industri yang menginspirasi BeeScout, **bukan otoritas yang diikuti langsung**. BeeScout sengaja divergen pada beberapa hal (`consumer[]` first-class, `stakeholders[].role` enum closed, `standard_version` independen, `ports[]` alih-alih `servers[]`, dsb). Issue [#A — mapping](../../data-contract/docs/comparison-odcs.md) (akan dibuat) mendokumentasikan perbedaannya.

### Dua field representasi konsumen

BeeScout punya **dua field terpisah** yang sama-sama menyebut "konsumen kontrak":

| Field | Granularitas | Dipakai untuk |
|---|---|---|
| `metadata.consumer[].name` | Team (string nama tim) | Filter visibilitas kontrak — `user_team in consumer[].name` |
| `metadata.stakeholders[*]` dengan `role="consumer"` + `username` | Per-orang | Approval workflow (ADR-0005) |

Untuk producer & owner, hanya field per-orang yang ada — tidak ada `metadata.producer[]` setara consumer.

### Bug yang memicu (sudah direproduksi)

Mas Dimas (developer) tidak melihat kontrak yang dibuat admin. Akar persis:

1. Admin buat kontrak via wizard di [`frontend-admin/.../contracts/new/page.tsx`](../../frontend-admin/src/app/(protected)/contracts/new/page.tsx)
2. Form schema admin **tidak punya** `metadata.consumer` (zod definition tidak menyebutnya sebelum PR #97/#92). Payload yang dikirim ke `POST /datacontract/add` tidak punya field tersebut → backend simpan dengan `metadata.consumer = None`.
3. Dimas (`data_domain="penjualan"`) buka `/contracts` di frontend-user → frontend memanggil [`GET /datacontract/filter`](../../repository/app/main.py) (tanpa `contract_number`).
4. Backend [`main.py:1182-1189`](../../repository/app/main.py#L1182-L1189) filter list mode untuk non-admin:
   ```python
   accessible = [
       c for c in all_contracts
       if user_team in [m.get("name") for m in (c.get("metadata") or {}).get("consumer") or []]
   ]
   ```
   `consumer = None` → list kosong → `"penjualan" in []` → False → kontrak hilang.

**Klarifikasi vs issue #76**: Bug **bukan** di `/datacontract/lists` (yang filter pakai `created_by`/`managers`). Bug di `/datacontract/filter` mode list. Hot-fix #92 (PR #97) menutup jalur paling sering (form wizard) tapi tidak menyelesaikan akar.

### Asimetri producer

`access_verification_filter` di [`verificator.py:115-122`](../../repository/app/core/verificator.py#L115-L122) hanya cek `consumer[]` — tidak ada `producer[]`. Tim produser tidak punya filter visibilitas setara consumer, hanya bisa lihat kontrak via stakeholder lens (ADR-0005).

### Apa kata BeeScout standard tentang dua field ini

Dari [`data-contract/docs/README.md`](../../data-contract/docs/README.md) (sumber otoritatif):

| Field di spec | Required | Definisi (kutipan langsung) |
|---|---|---|
| `metadata.consumer.name` | YES | "Nama tim, sistem atau _consumer apps_ produk data" |
| `metadata.consumer.use_case` | YES | "Deskripsi singkat use case yang dapat dijalankan dengan dataset ini" |
| `metadata.stakeholders.name` | YES | Nama orang (Product Owner / Manager / dst) |
| `metadata.stakeholders.email` | YES | Email orang |
| `metadata.stakeholders.role` | YES | Enum closed: `owner`, `producer`, `consumer`, `reviewer` |
| `metadata.stakeholders.date_in/out` | — | Kapan masuk/keluar daftar |

**Kesimpulan:** BeeScout standard memang **menetapkan keduanya sebagai first-class field** dengan tujuan berbeda:

- `consumer[]` = **team/sistem level** dengan `use_case` (intent dokumentasi — siapa pakai untuk apa)
- `stakeholders[]` = **per-orang** dengan role enum (siapa pertanggungjawaban data)

**Bukan duplikasi spec-level.** Yang duplikasi adalah **penggunaan-nya di backend**: filter visibilitas saat ini exact-match ke `consumer[].name` (treating it as access key), padahal spec menempatkan `consumer[]` sebagai documentary. Akses-control yang lebih tepat: derive dari `stakeholders[role=consumer].username → user.data_domain`. Ini selaras dengan intent spec — `stakeholders[]` adalah field per-orang yang sudah punya link ke user account (lewat `username` per ADR-0004).

### `consumer[].use_case` jangan hilang

Spec menetapkan `metadata.consumer.use_case` sebagai **required**. Kalau kita drop `consumer[]` total, informasi *bagaimana* tim memakai data hilang — bukan hal trivial untuk audit & compliance. Solusi: pertahankan `consumer[]` sesuai spec, tapi jangan dipakai untuk access-control.

---

## Opsi yang dipertimbangkan

| Opsi | Inti | Effort | Migration | Sesuai BeeScout spec? | Drift |
|---|---|---|---|---|---|
| A. Drop `consumer[]`, derive dari stakeholders | Single source | Tinggi | Wajib | ❌ `consumer.use_case` wajib di spec | ✅ Hilang |
| B. Tetap dua field, auto-sync via backend validator | Backward-compat | Sedang | Tidak | ✅ | ⚠️ Sync hook harus cover semua path |
| C. Tambah `producer[]` untuk simetri | Additive | Rendah | Optional | ❌ Spec tidak punya `producer[]` | ❌ Menggandakan problem |
| D. UI auto-fill (hot-fix #92) | Form-only | Sudah ship | Tidak | ✅ | ⚠️ YAML/API bypass |
| **A'. Hybrid (pilihan)** | **Pisahkan concern**: `consumer[]` = documentary (sesuai spec), akses derive dari stakeholders | **Sedang** | **Phased** | **✅ Selaras intent spec** | **✅ Hilang** |

### Detail Opsi A' (rekomendasi)

Pisahkan **dua concern berbeda** yang saat ini tercampur di `consumer[]`:

1. **Access-control** (siapa boleh lihat kontrak) → derive dari `metadata.stakeholders[role=consumer].username → user.data_domain`. Tidak perlu `consumer[].name` lagi untuk filter.
2. **Documentation** (apa use case tim) → `metadata.consumer[]` tetap ada untuk `use_case` saja. `name` tetap di-isi sebagai keterangan, tapi **tidak lagi** dipakai backend untuk akses.

Hasil:
- Bug visibilitas hilang permanen — sumber tunggal (stakeholders) untuk akses.
- `use_case` documentation tetap ada sesuai BeeScout spec.
- Producer dapat filter setara consumer secara gratis (`stakeholders[role=producer]`).
- Selaras intent BeeScout spec: `consumer[]` tetap field documentary (sesuai definisi spec), `stakeholders[]` jadi field per-orang (yang sudah link ke user account via `username` per ADR-0004).
- Backward-compat tidak break: kontrak lama yang punya `consumer[].name` tapi tanpa stakeholder username → tetap perlu migration (lihat di bawah).

## Keputusan

**Pilih Opsi A' (Hybrid).** Source of truth untuk visibilitas: `metadata.stakeholders[role IN (consumer, producer)].username → user.data_domain`. `metadata.consumer[]` tetap ada di schema sebagai dokumentasi `use_case` saja.

### Spesifikasi teknis

#### 1. Visibility filter baru

`access_verification_filter` ([`verificator.py:115-122`](../../repository/app/core/verificator.py#L115-L122)) dan `/datacontract/filter` list mode ([`main.py:1182-1189`](../../repository/app/main.py#L1182-L1189)) dipindah ke helper baru `derive_team_scope(contract) -> set[str]`:

```python
async def derive_team_scope(contract: dict) -> set[str]:
    """Tim yang punya akses ke kontrak berdasarkan stakeholders (consumer
    & producer) — derive ke data_domain via lookup user. Tidak lagi
    membaca metadata.consumer[].name."""
    stakeholders = (contract.get("metadata") or {}).get("stakeholders") or []
    usernames = [
        s.get("username") for s in stakeholders
        if s.get("role") in ("consumer", "producer") and s.get("username")
    ]
    if not usernames:
        return set()
    users = await usrcollection.find(
        {"username": {"$in": usernames}},
        {"_id": 0, "username": 1, "data_domain": 1}
    ).to_list(None)
    return {u["data_domain"] for u in users if u.get("data_domain")}
```

Filter list mode jadi `O(n_contracts)` lookup user — untuk skala BeeScout (<500 kontrak) dapat diterima tanpa denormalisasi (lihat keputusan denormalisasi di bawah).

#### 2. Backward-compat reading (Phase 1)

Sebelum migration selesai, derive function juga **fallback** ke `consumer[].name` lama bila stakeholders kosong:

```python
if not usernames:
    legacy = [m.get("name") for m in (contract.get("metadata") or {}).get("consumer") or []]
    return {n for n in legacy if n}
```

Setelah migration verified & legacy contracts cleaned, fallback dihapus (Phase 3).

#### 3. Write path

`POST /datacontract/add` dan `PUT /datacontract/update` **tidak menyentuh** `consumer[].name` lagi (selain documentation `use_case`). Hot-fix #92 (auto-populate `consumer[]` dari stakeholders) menjadi tidak perlu setelah Phase 1 deployed — bisa di-revert atau dibiarkan sebagai redundansi sampai Phase 3.

#### 4. Migration legacy contracts

Script [`repository/scripts/migrate_consumer_to_stakeholders.py`](../../repository/scripts/migrate_consumer_to_stakeholders.py) (baru, mirror pola `migrate_approval_roles.py`):

Untuk setiap kontrak dengan `metadata.consumer[]` non-kosong:
1. Untuk setiap `consumer[].name`, cari user aktif dengan `data_domain == name`
2. Untuk tiap user yang ditemukan, **tambah ke stakeholders[]** dengan `role="consumer"` + `username=user.username` bila belum ada
3. Kalau tidak ada user dengan `data_domain == name`: skip, tulis warning ke output (admin perlu invistigasi manual — kemungkinan typo atau tim sudah bubar)

Idempoten + dry-run default + `--apply` untuk eksekusi (sesuai pattern existing scripts).

#### 5. Phasing (di #94 implementasi)

```
Phase 1 (1 PR) — Backend dual-source read
   ├─ derive_team_scope() helper baru dengan fallback consumer[]
   ├─ /datacontract/filter list mode pakai helper
   ├─ access_verification_filter pakai helper
   ├─ Tests: kontrak baru pakai stakeholders, kontrak legacy pakai consumer[]
   └─ Tidak break apapun

Phase 2 (1 PR) — Migration legacy
   ├─ scripts/migrate_consumer_to_stakeholders.py
   ├─ Jalankan sekali di production
   └─ Verifikasi: semua kontrak legacy sekarang punya stakeholders[]

Phase 3 (1 PR) — Drop fallback + revert #92 hot-fix
   ├─ Hapus fallback consumer[] read di derive_team_scope
   ├─ Hapus auto-sync di form admin (#92) — sudah tidak perlu
   ├─ consumer[] tetap ada di schema tapi semata documentary
   └─ Tests: kontrak tanpa stakeholders → tidak terlihat siapa pun

Phase 4 (jauh kemudian, opsional)
   └─ Drop consumer[].name field, sisakan use_case sebagai consumer[].use_case
     (perubahan model — major version bump kontrak per CLAUDE.md)
```

### Denormalisasi: cache vs lookup

**Keputusan: lookup-on-read, tanpa cache.**

Trade-off:
- **Cache** `stakeholders[].data_domain` di dokumen kontrak: fast query, tapi stale saat user PATCH `data_domain` (sekarang admin bisa pindah user antar tim via `/user/{username}`). Perlu invalidation hook di setiap update user.
- **Lookup** per request: `O(n_contracts)` user lookup. Pada skala BeeScout (<500 kontrak, <50 stakeholder rata-rata), <5000 lookup per `/datacontract/filter` call. MongoDB dengan index pada `username` (sudah ada — unique index) eksekusi sub-ms.

Pada pre-1.0 dengan beban kecil, lookup correct-by-default lebih aman daripada cache yang harus di-invalidate manual. Denormalisasi bisa ditambahkan **nanti** kalau profiling menunjukkan latency issue — keep it simple sekarang.

---

## Konsekuensi

### Positif

- **Bug visibilitas hilang permanen** — single source of truth untuk akses.
- **Producer simetri gratis** — `stakeholders[role=producer]` masuk filter dengan effort 0.
- **Eliminasi class drift** — admin tidak bisa "lupa" satu sisi karena hanya satu sisi.
- **Sesuai BeeScout spec** — backend yang sebelumnya keliru pakai `consumer[]` (documentary) untuk access-control sekarang sejajar dengan intent spec.
- **`use_case` documentation tetap utuh** — `consumer[]` tetap di tempatnya sebagai field documentary, sesuai requirement spec.

### Negatif / Risiko

- **Tiga PR sequential** (#94 dipecah) — koordinasi deploy lebih ketat. Mitigasi: Phase 1 zero-breakage karena fallback masih ada.
- **Performance** lookup-on-read: O(n_contracts × n_stakeholders) per request. Pada skala pre-1.0 dapat diterima; profiling jadi tugas masa depan.
- **Migration kontrak legacy** tergantung ada-tidaknya user yang `data_domain`-nya cocok dengan `consumer[].name`. Yang tidak match perlu manual review (script print warning, tidak fail).
- **`consumer[]` jadi field yang "looks like access-control tapi tidak"** — perlu dokumentasi jelas di Pydantic docstring dan glossary supaya kontributor tidak salah pakai. Mitigasi: comment eksplisit + entry baru di [docs/glossary.md](../glossary.md).

### Mitigasi tambahan

- **Hot-fix #92 dipertahankan** sampai Phase 3. Walau redundant setelah Phase 1, dia tidak harmful (data tetap konsisten).
- **Pydantic validator opsional** di Phase 1: warn (logging) bila contract di-create dengan `consumer[]` non-kosong tapi tanpa matching stakeholders — mendorong admin lengkapi stakeholders lebih dini.

---

## Alternatif yang ditolak

**Opsi A pure (drop `consumer[]` total)**: kehilangan `use_case` documentation yang BeeScout spec tetapkan sebagai required. Ditolak — auditor/steward butuh info ini dan menghapus field wajib spec adalah breaking change semantik.

**Opsi B (auto-sync dua arah)**: memang kerja, tapi backend tetap simpan duplikasi semantik (akses + dokumentasi di field yang sama). Hook sync harus cover: form wizard, YAML import, direct API, migration script. Lebih banyak surface untuk drift dibanding Opsi A' yang memisahkan concern di level desain.

**Opsi C (tambah `metadata.producer[]`)**: menggandakan problem ke sisi produser. BeeScout spec tidak menetapkan `producer[]` sebagai field — menambahkannya = extend spec tanpa kebutuhan. Producer simetri lebih baik dicapai via Opsi A' (derive dari `stakeholders[role=producer]`) tanpa ubah spec.

**Opsi D pure (hot-fix #92 saja, tidak ada perubahan backend)**: cukup untuk close bug observasi tapi tidak menyelesaikan: (a) YAML import bypass, (b) producer asimetri, (c) ambiguity desain (`consumer[]` masih dipakai untuk dua tujuan). Hot-fix sengaja sempit dan disebut "hot-fix" — bukan solusi struktural.

---

## Referensi

### Acuan utama

- [`data-contract/docs/README.md`](../../data-contract/docs/README.md) — BeeScout standard, otoritatif untuk definisi field
- [`data-contract/examples/full.yaml`](../../data-contract/examples/full.yaml) — contoh kanonik (sumber `consumer[].use_case` & `stakeholders[]`)

### Related di BeeScout

- Issue [#76](https://github.com/alamanda-projects/beescout/issues/76) — analisa awal
- Issue [#92](https://github.com/alamanda-projects/beescout/issues/92) — hot-fix UX (in production via PR [#97](https://github.com/alamanda-projects/beescout/pull/97))
- Issue [#94](https://github.com/alamanda-projects/beescout/issues/94) — implementasi (scope di-update sesuai phasing di atas)
- [ADR-0004](0004-approval-workflow-multi-role.md), [ADR-0005](0005-approval-owner-replaces-steward.md) — keputusan stakeholder-per-orang yang jadi basis Opsi A'
- [`repository/app/main.py:1182-1189`](../../repository/app/main.py#L1182-L1189) — filter list mode
- [`repository/app/core/verificator.py:115-122`](../../repository/app/core/verificator.py#L115-L122) — `access_verification_filter`

### Komparasi industri (bukan acuan)

- [Open Data Contract Standard (ODCS)](https://github.com/bitol-io/open-data-contract-standard) — referensi industri yang menginspirasi BeeScout. Bukan otoritas; BeeScout sengaja divergen pada beberapa concept. Detail perbedaan & rationale akan didokumentasikan di `data-contract/docs/comparison-odcs.md` (issue terpisah).
