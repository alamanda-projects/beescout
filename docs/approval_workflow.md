# Alur Persetujuan (Approval Workflow)

BeeScout menerapkan mekanisme tata kelola data di mana perubahan pada kontrak data oleh pengguna non-admin (`user` atau `developer`) harus melalui proses peninjauan dan persetujuan.

## 🔄 Alur Kerja

```mermaid
sequenceDiagram
    participant User as User/Developer
    participant API as Backend API
    participant DB as MongoDB
    participant Admin as Admin/Root

    User->>API: PUT /datacontract/update
    Note over API: Cek Role & Izin
    API->>DB: Simpan ke 'pending_changes'
    API->>DB: Buat Approval Record
    API-->>User: 200 OK (Status Pending)
    
    Admin->>API: GET /approval/pending
    API-->>Admin: Daftar Approval Menunggu
    
    Admin->>API: POST /approval/{id}/vote
    Note over Admin: Vote: Approved / Rejected
    
    alt Semua Approver Setuju
        API->>DB: Terapkan 'pending_changes' ke Kontrak Utama
        API->>DB: Update Status Approval: 'approved'
    else Ada yang Menolak
        API->>DB: Batalkan 'pending_changes'
        API->>DB: Update Status Approval: 'rejected'
    end
    
    API-->>Admin: 200 OK (Resolved)
```

## 🛠️ Endpoints Terkait

| Method | Endpoint | Deskripsi |
|---|---|---|
| `PUT` | `/datacontract/update` | Mengajukan perubahan (otomatis masuk antrean jika non-admin) |
| `GET` | `/approval/pending` | Melihat daftar approval yang perlu di-vote oleh user saat ini |
| `GET` | `/approval/mine` | Melihat daftar approval yang diajukan oleh user saat ini |
| `POST` | `/approval/{id}/vote` | Memberikan suara (approve/reject) pada pengajuan |

## 👥 Aturan Voting

1. **Approver**: Secara otomatis mencakup semua Admin/Root yang aktif, serta pengelola kontrak yang bersangkutan.
2. **Konsensus**: Perubahan hanya akan diterapkan jika **seluruh** approver yang ditugaskan memberikan suara `approved`.
3. **Veto**: Satu suara `rejected` akan langsung membatalkan seluruh pengajuan.
