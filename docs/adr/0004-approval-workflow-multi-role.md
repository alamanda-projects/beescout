# ADR-0004: Approval workflow multi-peran (Steward + Producer + Consumer)

**Status**: Superseded by [ADR-0005](0005-approval-owner-replaces-steward.md)
**Tanggal**: 2026-05-24
**Decider**: @haninp

> Steward (admin/root auto-derived) sudah tidak menjadi approver. Lihat ADR-0005:
> approver kini Owner + Producer + Consumer, semua dari `metadata.stakeholders[]`.

---

## Konteks

Approval workflow saat ini di [repository/app/main.py:811](../../repository/app/main.py#L811):

```python
approvers = list({u["username"] for u in admin_users} | set(existing.get("managers") or []))
```

Semua approver diperlakukan setara — satu suara per orang, dan konsensus diukur dari jumlah approved == jumlah approvers. Konsekuensi tata kelola:

- Admin/Root memegang kontrol penuh; tim Producer dan Consumer tidak punya suara formal.
- Pengelola kontrak yang seharusnya **mewakili tim** (produsen vs konsumen data) tidak terlibat secara struktural.
- Tidak ada audit trail "siapa mewakili peran apa" — sulit dilihat saat post-mortem.

Issue [#27](https://github.com/alamanda-projects/issues/27) meminta perubahan: setiap pengajuan kontrak harus disetujui oleh **tiga peran berbeda** — Data Steward (Bu Retno), perwakilan Producer, dan perwakilan Consumer.

## Keputusan

### 1. Sumber data approver per peran

| Peran | Sumber | Catatan |
|---|---|---|
| Steward | Semua user aktif dengan `group_access in {root, admin}` | Sama seperti sebelumnya. |
| Producer | `metadata.stakeholders[*]` dengan `role == "producer"` dan `username` terisi | Per-orang, bukan per-tim. |
| Consumer | `metadata.stakeholders[*]` dengan `role == "consumer"` dan `username` terisi | Per-orang, bukan per-tim. |

### 2. Schema change — `MetadataStakeholders.username`

Tambah field opsional `username: Optional[str]` pada model `MetadataStakeholders`:

```python
class MetadataStakeholders(BaseModel):
    name: str
    email: Optional[str] = None
    role: str
    username: Optional[str] = None   # NEW — referensi ke dgrusr.username
    date_in: Optional[str] = None
    date_out: Optional[str] = None
```

- **Opsional** karena kontrak lama belum punya field ini.
- Frontend (PR2) akan menyediakan dropdown user dari `/user/lists` saat menambah pemangku.
- Stakeholder tanpa `username` tetap valid sebagai informasi, tapi **tidak dihitung** sebagai approver.

### 3. Quorum

**Opsi C** — minimum 1 vote `approved` per peran. Satu vote `rejected` dari peran manapun langsung membatalkan pengajuan (veto tetap berlaku).

### 4. Fallback graceful untuk kontrak tanpa producer/consumer username

Kontrak lama atau belum lengkap mungkin tidak punya stakeholder Producer/Consumer dengan username terisi. Aturan:

- Jika sebuah peran punya ≥ 1 approver → wajib minimum 1 approved dari peran itu.
- Jika sebuah peran tidak punya approver (kosong) → peran itu **dianggap auto-pass** (tidak memblokir konsensus). Steward tidak pernah kosong sehingga keputusan tetap terkontrol.
- Catatan akan dicantumkan di approval record (`fallback_roles: ["producer"]`) sebagai audit trail.

### 5. Struktur approval document

Approval doc baru:

```python
{
  "approval_id": "...",
  "contract_number": "...",
  "requested_by": "...",
  "proposed_changes": {...},
  "approvers": ["bu_retno", "pak_dimas", "mbak_indah"],     # flat — untuk query lama
  "approvers_by_role": {
    "steward":  ["bu_retno"],
    "producer": ["pak_dimas"],
    "consumer": ["mbak_indah"],
  },
  "fallback_roles": [],     # ["producer"] jika kontrak tidak punya producer
  "votes": [...],
  "status": "pending",
  "created_at": "...",
  "resolved_at": null,
}
```

- `approvers` (flat) tetap ada — backward-compatible dengan query `GET /approval/pending` (`{"approvers": username, ...}`).
- `approvers_by_role` baru — sumber kebenaran untuk validasi konsensus per peran.
- `fallback_roles` — audit kapan peran auto-pass karena tidak ada approver.

### 6. Backward compat untuk in-flight approval

Approval record yang sudah ada (status `pending` sebelum deploy) **tidak dimigrasi otomatis** — voting logic tetap kompatibel:

- Jika doc tidak punya `approvers_by_role`, fallback ke logika lama (konsensus = semua approver setuju).
- Hanya approval baru yang pakai logika multi-role.

Script migrasi opsional disediakan ([repository/scripts/migrate_approval_roles.py](../../repository/scripts/migrate_approval_roles.py)) untuk admin yang ingin men-derive `approvers_by_role` retroaktif. Dry-run by default.

### 7. Rule Catalog di luar scope

Issue #27 menyebut Rule Catalog juga. Keputusan: untuk Rule Catalog approval berlaku **Opsi C khusus steward-only** (Bu Retno saja). Tapi Rule Catalog approval workflow belum diimplementasi — itu issue #69 (depends on this ADR). Tidak dikerjakan di PR yang menyertai ADR ini.

## Alasan

1. **Tata kelola: Producer dan Consumer punya suara.** Steward saja terlalu sentralistis untuk perubahan yang langsung memengaruhi kedua belah pihak.
2. **Per-orang via stakeholders[] lebih ringan daripada per-tim.** Stakeholders sudah ada di kontrak dan punya peran eksplisit. Tidak perlu menambah model team-membership baru.
3. **Quorum=1 per peran (Opsi C).** Operasional ringan: cukup satu wakil tim merespons, tetap menjamin keterlibatan tiap peran.
4. **Fallback graceful daripada hard-block.** Memblokir kontrak lama karena tidak ada producer username akan menyandera operasional. Lebih baik audit trail jelas + dorong UI mendorong pelengkapan data.
5. **`username` opsional, bukan wajib.** Memperkenalkan field wajib akan invalidasi kontrak lama (breaking) — bertentangan dengan policy schema versioning di CLAUDE.md.

## Konsekuensi

### Positif

- Tata kelola lebih seimbang; Producer dan Consumer ikut bertanggung jawab.
- Audit trail jelas: tahu siapa mewakili peran apa.
- Migrasi non-disruptive — kontrak lama tetap jalan, approval in-flight tidak rusak.

### Negatif / Risiko

- **Approval bisa stuck** kalau tidak ada producer/consumer responsif.
  - **Mitigasi**: fallback auto-pass jika peran kosong; UI menampilkan progres per peran sehingga pengajuan transparan.
  - **Belum diselesaikan**: timeout otomatis (auto-reject setelah N hari) — kandidat issue terpisah jika diperlukan.
- Stakeholder schema berubah (tambah field) — perlu PR frontend (PR2) supaya form pemangku punya dropdown user.
- Approval doc menjadi lebih kompleks (`approvers_by_role`, `fallback_roles`). Worth it karena memungkinkan reasoning per-peran.

### Mitigasi breaking change

- `MetadataStakeholders.username = Optional[str] = None` — kontrak lama tetap valid.
- Approval doc lama (tanpa `approvers_by_role`) tetap bisa di-vote dengan logika lama.
- Tidak ada perubahan ke endpoint signature — `POST /approval/{id}/vote` tetap sama.

## Alternatif yang ditolak

**Match by email**: pakai `stakeholder.email` → cari `dgrusr.email`. Tidak butuh schema baru.
→ Ditolak karena `email` opsional dan banyak stakeholder lama tanpa email — sama saja butuh data cleanup.

**Per-tim approval (team-level)**: tambah `metadata.producer[]` dengan struktur seperti `metadata.consumer[]`. Approver = semua user dengan `data_domain` cocok.
→ Ditolak karena mengganggu schema kontrak ODCS dan memaksa setiap tim punya minimal 1 anggota di setiap kontrak. Stakeholder-level lebih fleksibel. _(Update #99: framing "schema kontrak ODCS" keliru — acuan sebenarnya [BeeScout standard](../../data-contract/docs/README.md); ODCS hanya komparasi industri. Alasan utama penolakan tetap valid: memaksa minimum 1 anggota per tim.)_

**Quorum mayoritas (>50% per peran)**: alih-alih min 1 approved.
→ Ditolak karena menambah cognitive load tanpa keuntungan jelas; mayoritas tim Producer/Consumer kemungkinan hanya 1–3 orang.

## Referensi

- [Issue #27](https://github.com/alamanda-projects/beescout/issues/27)
- [docs/approval_workflow.md](../approval_workflow.md)
- [docs/personas.md](../personas.md) — peran Bu Retno (Steward), Mas Dimas (Producer-side), Mbak Indah (Consumer-side)
- [repository/app/main.py:811](../../repository/app/main.py#L811) — implementasi lama
