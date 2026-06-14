# Audit validasi form FE (Phase 1 dari #114)

> **Phase 1 = audit & rekomendasi.** Tidak ada perubahan kode produksi di sini. Phase 2 membuat helper/pattern bersama; Phase 3 mengeksekusi per kelompok form. Lihat [#114](https://github.com/alamanda-projects/beescout/issues/114).

Companion dari [`pydantic-spec-audit.md`](pydantic-spec-audit.md): dokumen itu mengaudit **layer backend** (Pydantic + YAML validator, #102), dokumen ini mengaudit **layer FE form** (zod + indikator visual). Defense-in-depth — FE = layer 1 (feedback cepat), backend = layer 2-3 (integrity).

## Prinsip (dari maintainer feedback)

> **Standar BeeScout = otoritas.** FE zod harus follow spec, bukan sebaliknya. Setiap field spec-YES yang masih `optional` di zod = gap. Setiap field opsional yang punya format (email, slug, cron, date) tapi tidak divalidasi saat diisi = gap.

Tiga aturan konsistensi yang ingin dicapai (ringkasan dari issue):
1. **Mandatory**: tidak boleh kosong — submit dicegah, indikator `*`, error inline merah.
2. **Optional ber-format**: kalau diisi, harus lolos format check (email/url/date/angka/slug/cron).
3. **Bahasa**: pesan error Bahasa Indonesia, ikut [`glossary.md`](glossary.md). Tidak ada "Field is required".

## Metodologi

1. Acuan required-ness field kontrak: [`data-contract/docs/README.md`](../data-contract/docs/README.md) (kolom `Required`), konsisten dengan keputusan [`pydantic-spec-audit.md`](pydantic-spec-audit.md). Form non-kontrak (user/domain/catalog/setup) memakai business-rule + aturan format dari tabel di issue #114.
2. Untuk tiap form, tiap field dicek:
   - **Required?** menurut spec/business
   - **zod saat ini**: `min(1)` / `optional` / format check (`email`/`regex`/`enum`/`refine`)
   - **Submit prevention**: ada `zodResolver` → otomatis block submit kalau schema fail
   - **Bahasa pesan**: Indonesia / Inggris / tidak ada
3. Semua 12 form sudah memakai `zodResolver` (verified via grep) — jadi submit-prevention "ada" di mana pun ada rule zod. Gap utamanya: **rule yang hilang/longgar**, bukan resolver yang absen.

## Legenda tag

| Tag | Arti | Aksi Phase 3 |
|---|---|---|
| ✅ **Aligned** | Required + pesan ID, atau optional yang memang bebas-format. | — |
| 🔴 **Make required** | Field spec/business wajib tapi zod `optional`/tanpa `min(1)`. | Tambah `min(1)` + pesan ID |
| 📧 **Add format check** | Optional tapi ada format (email/slug/cron/url/angka) yang tidak divalidasi saat diisi. | Tambah refinement format |
| 🔢 **Enum not enforced** | Field enum-closed disimpan sebagai free `z.string()` — bisa nilai liar. | Ganti ke `z.enum([...])` |
| 🌐 **Bahasa/UX** | Pesan Inggris / tanpa pesan / indikator `*` hilang. | Samakan ke pesan ID + `*` |
| 🔗 **Overlap #102** | Required-ness diputuskan di audit Pydantic; FE enforcement nyusul setelah PR-B #102. | Koordinasi dengan #102 PR-B |
| ❓ **Needs decision** | Ambigu (mis. `is_mandatory` vs `is_nullable`). | Tunggu keputusan #102 |

---

## Ringkasan kesehatan per form (TL;DR)

| Form | File | Kondisi | Gap utama |
|---|---|---|---|
| **Kontrak** (4 file) | admin/user × new/edit | 🔴 **Paling lemah** | `description.*`, `sla.*`, `email` format, `role`/`dimension` enum, `model.*type/description` |
| User management | `users/page.tsx` | 🟡 Cukup | edit-password tidak re-validasi strength; username tanpa aturan special-char |
| Domain management | `domains/page.tsx` | 🟡 Cukup | `name` slug (lowercase+hyphen) tidak di-enforce FE |
| Rule catalog (3 file) | admin new/edit, user new | ✅ **Paling kuat** | (reference pattern — regex, enum, refine, includes) |
| Setup wizard | `setup/page.tsx` | ✅ Kuat | username tanpa aturan special-char (minor) |

**Temuan cross-cutting #1**: `grep "\.email("` di seluruh FE = **0 hasil**. Tidak ada satu form pun memvalidasi format email, padahal `stakeholders[].email` punya placeholder `email@domain.com`. Ini persis bug "bisa simpan 'abc' di field email" di issue.

**Temuan cross-cutting #2**: enum-closed (`stakeholders.role`, `quality.dimension/impact/severity`) disimpan sebagai free `z.string()` di form kontrak — padahal catalog forms sudah pakai `z.enum([...])`. Pattern bagus sudah ada, tinggal dipinjam.

---

## 1. Form Kontrak (4 file)

`contracts/new` & `contracts/[cn]/edit` di **frontend-admin** dan **frontend-user**. Skema zod keempatnya ~identik (wizard 6 step: Informasi Dasar · SLA · Pemangku · Struktur Data · Koneksi · Tinjauan). Referensi: [admin new](../frontend-admin/src/app/(protected)/contracts/new/page.tsx), [admin edit](../frontend-admin/src/app/(protected)/contracts/[cn]/edit/page.tsx), [user new](../frontend-user/src/app/(protected)/contracts/new/page.tsx), [user edit](../frontend-user/src/app/(protected)/contracts/[cn]/edit/page.tsx).

### Step "Informasi Dasar" + lifecycle

| Field | Required | zod saat ini | Tag | Rekomendasi |
|---|---|---|---|---|
| `standard_version` | YES | `min(1)` (auto-generated) | ✅ | — |
| `contract_number` | YES | `min(1)` (auto-generated) | ✅ | — |
| `metadata.version` | YES | `min(1)` | ✅ | — |
| `metadata.type` | YES | `min(1, 'Pilih tipe kontrak')` | ✅ | — |
| `metadata.name` | YES | `min(1)` | ✅ | — |
| `metadata.owner` | YES | `min(1)` | ✅ | — |
| `metadata.consumption_mode` | NO | `optional` | ✅ | — |
| `metadata.effective_date` | YES | `min(1)` (#103) | ✅ | — |
| `metadata.expiry_date` | YES | `min(1)` + refine `>= effective_date` (#114 ✅) | ✅ | Cross-field divalidasi saat submit (error di slot `expiry_date`) |
| `metadata.description.purpose` | YES | `optional` | 🔴 🔗 | Wajib per spec (#102). Wizard belum ada field eksplisit di sebagian path |
| `metadata.description.usage` | YES | `optional` | 🔴 🔗 | Wajib (`private`/`public`); default `private` |

### Step "SLA"

> Wizard saat ini memakai **UI alias** `sla.{availability, frequency, retention, cron}` (semua free string `optional`), bukan field spec `availability_start/end/unit`, `frequency_unit`, `retention_unit`. Lihat catatan alias di [`pydantic-spec-audit.md`](pydantic-spec-audit.md#L132). Strict-ke-spec di sini **bergantung #102 PR-B**.

| Field | Required | zod saat ini | Tag | Rekomendasi |
|---|---|---|---|---|
| `sla.availability` (alias) | YES (→ start/end/unit) | `optional` | 🔴 🔗 | Tunggu #102 PR-B refactor expose field spec; lalu mandatory-kan |
| `sla.frequency` (alias) | YES (→ frequency + unit) | `optional` | 🔴 🔗 | Sama |
| `sla.retention` | YES | `min(1)` (#114 3a ✅) | ✅ | Wajib (melengkapi #135). Backend simpan `retention:int` + `retention_unit:str` terpisah (CLAUDE.md) |
| `sla.cron` (`frequency_cron`) | NO | `cronField()` (#114 3a ✅) | ✅ | Validasi sintaks crontab saat diisi |

### Step "Pemangku" (stakeholders[])

| Field | Required | zod saat ini | Tag | Rekomendasi |
|---|---|---|---|---|
| `stakeholders[].name` | YES | `min(1, 'Nama wajib diisi')` | ✅ | — |
| `stakeholders[].role` | YES | `min(1)` free string | 🔴 🔢 | Ganti `z.enum([...7 role])`. UI dropdown sudah batasi, tapi zod bebas |
| `stakeholders[].email` | YES | `optional`, **tanpa format** | 🔴 📧 🔗 | Tambah `.email('Format email tidak valid')`; mandatory-kan per #102 |
| `stakeholders[].username` | NO (ADR-0004) | `optional` | ✅ | — |
| `stakeholders[].date_in` | YES | `min(1)` (#114 T1.3 ✅) | ✅ | — |
| `stakeholders[].date_out` | NO | `optional` | ✅ | Kalau diisi → refine `date_out >= date_in` |

### Step "Konsumen" (consumer[] — documentary, ADR-0007)

| Field | Required | zod saat ini | Tag | Rekomendasi |
|---|---|---|---|---|
| `consumer[].name` | YES (kalau entry ada) | `requiredString` (#114 3a ✅) | ✅ | UI consumer kini di-expose di step Pemangku (4 file) + tampil di halaman detail. Baris kosong dibuang saat submit |
| `consumer[].use_case` | NO (documentary) | `optional` | ✅ | Textarea opsional di UI consumer baru |

### Step "Struktur Data" (model[])

| Field | Required | zod saat ini | Tag | Rekomendasi |
|---|---|---|---|---|
| `model[].column` | YES | `min(1, 'Nama kolom wajib diisi')` | ✅ | — |
| `model[].business_name` | NO | `optional` | ✅ | — |
| `model[].logical_type` | YES | `optional` | 🔴 🔗 | — |
| `model[].physical_type` | YES | `optional` | 🔴 🔗 | — |
| `model[].description` | YES | `optional` | 🔴 🔗 | — |
| `model[].is_*` (7 flag) | YES (default false) | `boolean().optional()` | ✅ | Checkbox selalu ada nilai — fungsional aman |
| `model[].is_mandatory` | ❓ | `boolean().optional()` | ❓ | Tunggu keputusan konsolidasi vs `is_nullable` (#102) |
| `model[].quality[].code` | NO | `min(1)` | ✅ | — |
| `model[].quality[].dimension/impact/severity` | NO (enum) | free `optional` | 🔢 | Ganti `z.enum` untuk konsistensi (low-risk) |

### Step "Koneksi" (ports[]) — sengaja lenient

| Field | Required | zod saat ini | Tag | Rekomendasi |
|---|---|---|---|---|
| `ports[].object` / `properties[].*` | NO | `optional` (baris kosong dibuang di submit) | ✅ | By design — biarkan |

### Quality dataset-level (`metadata.quality[]`)

| Field | Required | zod | Tag |
|---|---|---|---|
| `quality[].code` | NO | `min(1, 'Kode wajib diisi')` | ✅ |
| `quality[].dimension/impact/severity` | NO (enum) | free `optional` | 🔢 (ganti `z.enum`) |

---

## 2. Form User Management — `frontend-admin/.../users/page.tsx`

Dua schema: `createSchema` & `editSchema`. Referensi: [users/page.tsx](../frontend-admin/src/app/(protected)/users/page.tsx).

| Field | Form | Required | zod saat ini | Tag | Rekomendasi |
|---|---|---|---|---|---|
| `username` | create | YES | `min(3)` `max(50)` | 🌐 | `max(50)` tanpa pesan; aturan issue "no special char" belum di-enforce → tambah `regex(/^[a-zA-Z0-9_]+$/)` |
| `password` | create | YES | `min(8)` + 4× `regex` (upper/lower/digit/special) | ✅ | Reference pattern strong-password |
| `name` | create | YES | `min(1)` | ✅ | — |
| `group_access` | create | YES | `min(1, 'Pilih peran')` | ✅ | Bisa `z.enum` (root/admin/developer/business_user) untuk ketat |
| `data_domain` | create | YES | `min(1)` | ✅ | — |
| `is_active` | create | — | `boolean` | ✅ | — |
| `name` | edit | YES | `min(1)` | ✅ | — |
| `group_access` | edit | YES | `min(1)` | ✅ | — |
| `data_domain` | edit | YES | `min(1)` | ✅ | — |
| `password` | edit | NO (ganti opsional) | `optional` **tanpa strength** | 🔴 📧 | Kalau diisi, **tidak** divalidasi strength → bisa set password lemah saat edit. Tambah `.refine` strength bila non-kosong |

---

## 3. Form Domain Management — `frontend-admin/.../domains/page.tsx`

Referensi: [domains/page.tsx](../frontend-admin/src/app/(protected)/domains/page.tsx).

| Field | Form | Required | zod saat ini | Tag | Rekomendasi |
|---|---|---|---|---|---|
| `name` | create | YES | `min(1)` `max(60)` | 📧 | Slug rule (lowercase + hyphen, no spasi) tidak di-enforce FE — backend `slugify_domain()` yang normalize. Tambah `regex(/^[a-z0-9-]+$/)` + hint, atau live-preview slug |
| `label` | create | YES | `min(1)` `max(80)` | ✅ | — |
| `description` | create | NO | `max(200)` `optional` | ✅ | — |
| `label` | edit | YES | `min(1)` `max(80)` | ✅ | — |
| `description` | edit | NO | `max(200)` `optional` | ✅ | — |

---

## 4. Form Rule Catalog (3 file) — reference pattern ✅

[admin new](../frontend-admin/src/app/(protected)/catalog/new/page.tsx), [admin edit](../frontend-admin/src/app/(protected)/catalog/[code]/edit/page.tsx), [user new](../frontend-user/src/app/(protected)/catalog/new/page.tsx). Skema ~identik (edit tanpa `code` karena immutable).

| Field | Required | zod saat ini | Tag |
|---|---|---|---|
| `code` | YES | `min(1)` + `regex(/^[a-z_]+$/, 'snake_case')` | ✅ |
| `label` | YES | `min(1)` | ✅ |
| `description` | NO | `optional` | ✅ |
| `layer` | YES | `z.enum(['dataset','column','both'])` | ✅ |
| `dimension` | YES | `z.enum(['completeness','validity','accuracy','security'])` | ✅ |
| `sentence_template` | YES | `min(1)` + `includes('{')` | ✅ |
| `params[].key` | YES | `min(1)` + `regex(/^[a-z_]+$/)` | ✅ |
| `params[].label` | YES | `min(1)` | ✅ |
| `params[].type` | YES | `z.enum(['text','number','select','multi','date'])` | ✅ |
| `params[].options[].{value,label}` | YES | `min(1)` | ✅ |

> **Kandidat sumber pattern Phase 2** — enum, regex, `includes`, pesan ID konsisten. Tidak ada gap. Catatan kecil: `dimension` di catalog punya `security` (4 nilai) sedangkan model kontrak quality 3 nilai (`completeness/validity/accuracy`) — beda domain, bukan bug.

---

## 5. Form Setup Wizard — `frontend-admin/(public)/setup/page.tsx` ✅

Referensi: [setup/page.tsx](../frontend-admin/src/app/(public)/setup/page.tsx).

| Field | Required | zod saat ini | Tag |
|---|---|---|---|
| `username` | YES | `min(3)` `max(50)` | 🌐 (sama: aturan special-char belum di-enforce) |
| `name` | YES | `min(1)` | ✅ |
| `password` | YES | `min(8)` + 4× regex | ✅ |
| `confirmPassword` | YES | `min(1)` + `.refine(password === confirmPassword)` | ✅ |
| `import_sample_contracts` / `import_catalog_rules` | — | `boolean` | ✅ |

> **Login** (admin+user) di luar scope per issue — username+password trivially required, sudah ada.

---

## Ringkasan rekomendasi

| Tag | Count (kira-kira) | Catatan |
|---|---|---|
| ✅ Aligned | ~38 | Mayoritas required-string & catalog/setup |
| 🔴 Make required | 11 | Hampir semua di form kontrak (description, sla alias, email, model types, consumer) |
| 📧 Add format check | 5 | email (kontrak), cron (kontrak), slug (domain), strength (edit user password) |
| 🔢 Enum not enforced | 3 grup | `role`, `dimension/impact/severity` (kontrak) |
| 🌐 Bahasa/UX | 2 | username special-char rule (users + setup), `max(50)` tanpa pesan |
| 🔗 Overlap #102 | 7 | description/sla/email/model — required-ness ikut #102 PR-B |
| ❓ Needs decision | 1 | `is_mandatory` vs `is_nullable` |

**Prioritas dampak**: (1) format email di stakeholders kontrak — bug yang disebut eksplisit di issue; (2) enum `role`/`dimension` (low-risk, pattern sudah ada di catalog); (3) edit-user password strength (security); (4) sisanya tunggu/koordinasi #102.

---

## Phase 2 plan (eksekusi) — helper / pattern bersama

Tujuan: hilangkan duplikasi rule & samakan pesan. Tiga artefak:

### 2a. Zod helper library — `frontend-admin/src/lib/zod-helpers.ts` (mirror di `frontend-user/`)

Builder kecil dengan pesan ID default, dipakai di semua schema:

```ts
export const requiredString = (msg = 'Wajib diisi') => z.string().min(1, msg)
export const emailField = () =>            // optional tapi format-checked saat diisi
  z.string().email('Format email tidak valid').optional().or(z.literal(''))
export const slugField = (msg = 'Gunakan huruf kecil, angka, dan tanda hubung') =>
  z.string().regex(/^[a-z0-9-]+$/, msg)
export const usernameField = () =>
  z.string().min(3, 'Minimal 3 karakter').max(50, 'Maksimal 50 karakter')
       .regex(/^[a-zA-Z0-9_]+$/, 'Hanya huruf, angka, dan underscore')
export const strongPassword = () => z.string().min(8, 'Minimal 8 karakter')
  .regex(/[A-Z]/, 'Harus ada huruf besar').regex(/[a-z]/, 'Harus ada huruf kecil')
  .regex(/[0-9]/, 'Harus ada angka').regex(/[^A-Za-z0-9]/, 'Harus ada karakter khusus')
export const optionalStrongPassword = () =>  // utk edit user
  z.union([z.literal(''), strongPassword()])
export const cronField = () => /* validasi crontab sederhana, optional */
```

Enum kontrak dipusatkan (role 7-nilai, dimension/impact/severity) supaya FE & display konsisten.

### 2b. `<FormField>` wrapper — `frontend-admin/src/components/ui/form-field.tsx`

Wrapper `Label` + `*` otomatis (kalau `required`) + slot error inline merah dari RHF `errors`. Menghapus pola `Label` + `Input` + manual `<p className="text-red">` yang tersebar. Tetap kompatibel dengan shadcn `Input/Select/Textarea` + `type="button"` safety ([qa-form-buttons.sh](../scripts/qa-form-buttons.sh)).

### 2c. Pesan error terpusat

Konstanta pesan ID (atau pakai default di helper 2a) — referensi [`glossary.md`](glossary.md) untuk istilah. Tidak ada string Inggris.

## Phase 3 plan — sub-PR per kelompok form

| PR | Scope | Effort | Catatan |
|---|---|---|---|
| **3a** | Form kontrak (4 file) | Tinggi | Gap terbanyak. **Koordinasi #102 PR-B** untuk required-ness `description/sla/email/model`. Bisa dipecah: 3a-i (low-risk: email format + enum `role`/`dimension` + `consumer.name`), 3a-ii (required group, setelah #102) |
| **3b** | User management | Rendah | edit-password strength + username special-char |
| **3c** | Domain management | Rendah | slug regex + hint/preview |
| **3d** | Rule catalog | — | Sudah aligned — paling banyak adopsi `<FormField>` (kosmetik), bukan rule baru |
| **3e** | Setup wizard | Sangat rendah | username special-char saja |

Urutan disarankan: **3a-i** (quick win, fix bug email yang disebut issue) → **3b/3c/3e** (kecil, mandiri) → **3a-ii** (tunggu #102 PR-B).

## Acceptance criteria (dari issue, status)

- [x] Phase 1 audit doc (dokumen ini)
- [ ] Phase 2 helper pattern + design tertulis → bagian "Phase 2 plan" di atas (eksekusi PR terpisah)
- [ ] Phase 3 PR(s) per kelompok form
- [ ] Manual test: tiap form, required kosong → submit ter-block, error jelas
- [ ] Manual test: tiap form, optional format salah → error muncul
- [ ] `make test-fe-admin` & `make test-fe-user` lulus
- [ ] `scripts/qa-form-buttons.sh` lulus
- [ ] Tidak ada pesan error Bahasa Inggris di production form

## Hubungan dengan issue lain

- **[#102](https://github.com/alamanda-projects/beescout/issues/102)** — backend Pydantic strict. Field 🔗 di atas (description/sla/email/model types) required-ness diputuskan di sana (PR-B). FE enforcement (issue ini) ship **setelah/berbarengan** PR-B agar tidak block submit untuk field yang backend belum wajibkan.
- **[#103](https://github.com/alamanda-projects/beescout/issues/103)** — `effective_date`/`expiry_date` sudah expose + required di wizard (✅). Refine cross-field `expiry >= effective` kandidat Phase 3a.
- **[#100](https://github.com/alamanda-projects/beescout/issues/100) / [#101](https://github.com/alamanda-projects/beescout/issues/101)** — converter ODCS = double-defense; FE yang lebih ketat mengurangi input invalid yang harus di-reject converter.
- **[#94](https://github.com/alamanda-projects/beescout/issues/94)** (ADR-0007, ✅ merged) — `consumer[]` documentary; FE `consumer.name` direkomendasikan `min(1)` tapi bukan access-control.

## Untuk maintainer

**Status**: Phase 1 audit (dokumen ini) — ready to merge.

**Action item next**: konfirmasi prioritas Phase 3. Default usulan = mulai **3a-i** (fix format email + enum, low-risk, menutup bug yang disebut di issue) tanpa menunggu #102. Field 🔗 (required group) menyusul setelah #102 PR-B agar FE & backend konsisten.
