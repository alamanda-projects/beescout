# Alur Persetujuan (Approval Workflow)

BeeScout menerapkan mekanisme tata kelola data di mana perubahan pada kontrak data oleh pengguna non-admin (`user` atau `developer`) harus melalui proses peninjauan dan persetujuan.

Sejak [ADR-0005](adr/0005-approval-owner-replaces-steward.md) (supersedes [ADR-0004](adr/0004-approval-workflow-multi-role.md)), konsensus dihitung **per peran** — **Owner + Producer + Consumer**, semua diturunkan dari `metadata.stakeholders[]`. Admin/root tidak lagi otomatis menjadi approver.

## 🔄 Alur Kerja

```mermaid
sequenceDiagram
    participant User as User/Developer
    participant API as Backend API
    participant DB as MongoDB
    participant Approvers as Approver (per peran)

    User->>API: PUT /datacontract/update
    Note over API: Cek role & izin
    API->>DB: Simpan ke pending_changes
    API->>DB: Derive approvers per peran<br/>(steward + producer + consumer)
    API->>DB: Buat Approval Record (approvers_by_role)
    API-->>User: 200 OK (Status Pending)

    Approvers->>API: GET /approval/pending
    API-->>Approvers: Daftar approval menunggu

    loop Setiap peran (Steward, Producer, Consumer)
        Approvers->>API: POST /approval/{id}/vote
    end

    alt Min 1 approved per peran non-kosong
        API->>DB: Terapkan pending_changes ke kontrak
        API->>DB: Set status: approved
    else Ada vote rejected
        API->>DB: Batalkan pending_changes
        API->>DB: Set status: rejected
    end

    API-->>Approvers: 200 OK (Resolved)
```

## 🛠️ Endpoints

| Method | Endpoint | Deskripsi |
|---|---|---|
| `PUT` | `/datacontract/update` | Mengajukan perubahan (otomatis masuk antrean jika non-admin) |
| `GET` | `/approval/pending` | Approval yang perlu di-vote oleh user saat ini |
| `GET` | `/approval/mine` | Approval yang diajukan oleh user saat ini |
| `POST` | `/approval/{id}/vote` | Memberikan suara (`approved` / `rejected`) |

## 👥 Aturan Voting (ADR-0005)

### Sumber data approver per peran

| Peran | Diambil dari |
|---|---|
| **Owner** | `metadata.stakeholders[*]` dengan `role == "owner"` dan `username` terisi |
| **Producer** | `metadata.stakeholders[*]` dengan `role == "producer"` dan `username` terisi |
| **Consumer** | `metadata.stakeholders[*]` dengan `role == "consumer"` dan `username` terisi |

Ketiga peran berasal dari `metadata.stakeholders[]`. Admin/root **tidak** otomatis menjadi approver — bila perlu, mereka ditambahkan eksplisit sebagai stakeholder dengan peran sesuai (paling sering: `owner`).

Hanya stakeholder yang **username-nya terisi** *dan* **user-nya aktif** di koleksi `dgrusr` yang dihitung. Stakeholder tanpa username tetap valid sebagai informasi, tapi tidak diberi hak vote.

### Konsensus (quorum)

- **Minimum 1 suara `approved` per peran** yang punya approver.
- Peran yang kosong (mis. kontrak tanpa stakeholder Consumer ber-username) → dianggap **auto-pass** dan dicatat di field `fallback_roles` untuk audit trail.
- Satu vote `rejected` dari peran manapun langsung membatalkan pengajuan (veto tetap berlaku).

Contoh approval doc setelah perubahan:

```json
{
  "approval_id": "abc123",
  "approvers": ["pak_bambang", "pak_dimas", "mbak_indah"],
  "approvers_by_role": {
    "owner":    ["pak_bambang"],
    "producer": ["pak_dimas"],
    "consumer": ["mbak_indah"]
  },
  "fallback_roles": [],
  "votes": [
    {"username": "pak_bambang","vote": "approved"},
    {"username": "pak_dimas",  "vote": "approved"},
    {"username": "mbak_indah", "vote": "approved"}
  ],
  "status": "approved"
}
```

### Backward compatibility

Voting endpoint role-agnostic — ia menghitung konsensus dari **kunci apa pun** yang ada di `approvers_by_role`. Konsekuensinya:

- Approval pre-ADR-0004 (tanpa `approvers_by_role`) → fallback ke logika lama (unanimous count).
- Approval format ADR-0004 (kunci `steward`) yang masih `pending` → tetap diverifikasi dengan minimum 1 admin/root + 1 producer + 1 consumer approve. Tidak ada migrasi paksa.
- Approval baru → format ADR-0005 dengan kunci `owner`.

Admin yang ingin men-derive ulang `approvers_by_role` untuk approval lama (tanpa kunci sama sekali) bisa menjalankan:

```bash
docker compose run --rm backend python -m scripts.migrate_approval_roles            # dry-run
docker compose run --rm backend python -m scripts.migrate_approval_roles --apply    # eksekusi
```

Script idempoten — aman dijalankan ulang.

## 🚧 Risiko & mitigasi

| Risiko | Mitigasi |
|---|---|
| Producer/Consumer tidak responsif → approval nyangkut | UI menampilkan progres per peran (kandidat #?? — frontend PR berikutnya). Auto-timeout = kandidat issue terpisah. |
| Kontrak lama belum punya `stakeholders[*].username` | Auto-pass per peran (lihat `fallback_roles`); UI bisa mendorong pelengkapan. |
| Stakeholder ditambah tapi user-nya kemudian dinonaktifkan | Derivation sudah menyaring `is_active: true`. Approval baru otomatis bypass user inaktif. |
