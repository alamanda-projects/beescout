# ADR-0005: Approver = Owner + Producer + Consumer (Steward dilepas)

**Status**: Accepted
**Tanggal**: 2026-05-24
**Decider**: @haninp
**Supersedes**: [ADR-0004](0004-approval-workflow-multi-role.md)

---

## Konteks

ADR-0004 menetapkan approver berasal dari tiga peran: **Steward** (semua admin/root aktif) + Producer + Consumer (dari `metadata.stakeholders[]`). Setelah implementasi (PR #70, PR #71 in-flight), maintainer mereview model dan menemukan ketidakcocokan dengan intent tata kelola yang sebenarnya:

- **Admin/root adalah peran sistem**, bukan peran governance pada kontrak. Mengikat admin/root sebagai approver default mencampur dua dimensi yang berbeda (akses operasional vs. kepemilikan data) dan tidak skalabel saat jumlah admin bertambah.
- Tiga peran governance yang dikenali di domain data contract (ODCS-aligned) adalah **Owner**, **Producer**, dan **Consumer** — semuanya per-kontrak, per-orang.
- Steward sebagai peran governance memang ada (`role: steward` di STAKEHOLDER_ROLES), tapi bukan default approver — itu peran opsional yang tidak setiap kontrak punya.

Hasilnya: model "Steward = admin/root" di ADR-0004 mengikat sistem ke proses operasional, bukan kepemilikan data. Pembetulan: turunkan semua approver dari `metadata.stakeholders[]`, tanpa peran sistem.

## Keputusan

### 1. Sumber data approver per peran

| Peran | Sumber |
|---|---|
| **Owner** | `metadata.stakeholders[*]` dengan `role == "owner"` dan `username` terisi |
| **Producer** | `metadata.stakeholders[*]` dengan `role == "producer"` dan `username` terisi |
| **Consumer** | `metadata.stakeholders[*]` dengan `role == "consumer"` dan `username` terisi |

Admin/root **tidak lagi** otomatis menjadi approver. Bila Bu Retno (steward) atau admin lain ingin diberi hak vote pada kontrak tertentu, mereka dapat ditambahkan sebagai stakeholder eksplisit dengan peran yang sesuai (paling sering: `owner` untuk kontrak yang dia kelola).

### 2. Quorum & veto

Tidak berubah dari ADR-0004:
- Minimum 1 vote `approved` per peran yang non-kosong.
- Peran kosong → auto-pass, dicatat di `fallback_roles` (audit trail).
- Satu vote `rejected` membatalkan pengajuan.

### 3. Struktur approval document

Kunci `approvers_by_role` berubah dari `steward` → `owner`. Struktur lain tetap sama:

```json
{
  "approvers_by_role": {
    "owner":    ["pak_bambang"],
    "producer": ["pak_dimas"],
    "consumer": ["mbak_indah"]
  },
  "fallback_roles": [],
  ...
}
```

### 4. Backward compat untuk approval in-flight

Approval `pending` yang dibuat dengan format ADR-0004 (kunci `steward`) **tidak dimigrasi otomatis**:

- `is_consensus_reached()` bersifat role-agnostic — ia iterasi seluruh kunci di `approvers_by_role`. Jadi approval lama dengan kunci `steward` tetap diverifikasi: butuh ≥1 admin approve, kemudian producer & consumer per kontrak.
- Approval pre-ADR-0004 (tanpa `approvers_by_role`) tetap pakai fallback unanimous-count seperti sebelumnya.

Script migrasi [`repository/scripts/migrate_approval_roles.py`](../../repository/scripts/migrate_approval_roles.py) sekarang menulis kunci baru (`owner` bukan `steward`) saat di-jalankan ulang. Approval lama yang sudah memiliki `approvers_by_role` di-skip oleh filter `$exists: false` — tidak akan di-overwrite.

### 5. Permission update kontrak (di luar approval)

Permission "siapa yang boleh edit kontrak" tidak diatur oleh ADR ini — itu tetap di logika `update_datacontract` (admin/root selalu boleh; user/developer hanya kontrak miliknya atau yang dia jadi manager). Yang berubah hanya derivasi approver.

## Alasan

1. **Pemisahan concern**: peran sistem (admin/root) ≠ peran governance kontrak (owner/producer/consumer). Mencampur keduanya membuat approval bergantung pada siapa yang punya akses admin, bukan siapa yang bertanggung jawab atas data.
2. **Konsistensi sumber data**: ketiga peran approver dari satu tempat (`stakeholders[]`) — mudah dipahami, mudah diaudit.
3. **Skalabilitas**: kontrak baru tidak otomatis butuh persetujuan setiap admin yang dibuat di kemudian hari. Approver tetap stabil walau admin pool berubah.
4. **Aligned dengan ODCS**: spec ODCS menempatkan Owner dan Producer/Consumer sebagai entitas first-class di metadata kontrak. Memakai field yang sama mengurangi divergensi.

## Konsekuensi

### Positif

- Tata kelola eksplisit: setiap kontrak menentukan sendiri siapa approver-nya.
- Tidak ada coupling tersembunyi antara peran sistem dan approval flow.
- Audit lebih bersih — semua approver bisa di-trace ke `stakeholders[]`.

### Negatif / Risiko

- Kontrak tanpa stakeholder `owner` ber-username akan **auto-pass** untuk peran Owner. UI sudah menampilkan banner `fallback_roles` agar operator melengkapi.
- Admin tidak otomatis tahu ada pengajuan baru — `GET /approval/pending` hanya menampilkan approval yang mencantumkan mereka. Admin yang ingin mengawal kontrak harus eksplisit menjadi stakeholder (paling sering: owner).
- Approval pre-ADR-0005 dengan kunci `steward` masih akan diverifikasi sampai resolved — boleh dibiarkan natural drain atau dimigrasi via script.

### Mitigasi

- Run script `python -m scripts.migrate_approval_roles --apply` setelah deploy untuk men-derive ulang approver lama menjadi format `owner` (idempoten — approval yang sudah punya kunci ditinggalkan; hanya yang tanpa `approvers_by_role` di-backfill).
- Untuk in-flight approval format ADR-0004 (kunci `steward`), maintainer dapat menutup manual atau biarkan resolved natural. Tidak ada migrasi otomatis karena bisa mengubah keputusan voting yang sedang berlangsung.

## Alternatif yang ditolak

**Steward sebagai 4th peran**: tambah `steward` di samping owner/producer/consumer.
→ Ditolak. Menambah veto point tanpa keuntungan jelas — Owner sudah mewakili tanggung jawab kepemilikan.

**Steward sebagai fallback**: admin/root jadi approver hanya bila satu peran kosong.
→ Ditolak. Mencampur peran sistem dengan governance lewat kondisi sulit dipahami. Lebih jelas: peran kosong → auto-pass dengan banner.

**Owner dari `metadata.owner` (string)**: pakai field string yang sudah ada.
→ Ditolak. `metadata.owner` adalah nama tim/owner organisasi (mis. "Tim Marketing"), bukan akun user. Tidak ada mapping deterministik ke `username`.

## Referensi

- [ADR-0004](0004-approval-workflow-multi-role.md) — keputusan yang di-supersede
- [Issue #27](https://github.com/alamanda-projects/beescout/issues/27)
- [docs/approval_workflow.md](../approval_workflow.md)
- [repository/app/main.py — derive_approvers_by_role](../../repository/app/main.py)
