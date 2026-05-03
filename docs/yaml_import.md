# Import & Validasi YAML

BeeScout mendukung pengelolaan Data Contract secara deklaratif menggunakan file YAML yang mengikuti standar ODCS (Open Data Contract Standard).

## 🛡️ Lapisan Validasi

Sistem melakukan validasi berlapis saat file YAML diunggah:

1. **Layer 1: YAML Syntax**: Memastikan file adalah format YAML yang valid.
2. **Layer 2: ODCS Schema**:
    - Memastikan adanya field wajib (`standard_version`, `metadata`, `name`, `owner`, dll).
    - Memvalidasi tipe data (misal: `retention` harus integer).
    - Memvalidasi nilai enum (misal: `role` stakeholder harus sesuai standar).

## 🛠️ Endpoints Terkait

| Method | Endpoint | Peran Minimal | Deskripsi |
|---|---|---|---|
| `POST` | `/contracts/validate-yaml` | `admin` | Validasi file tanpa menyimpannya. Mengembalikan error/warning detail. |
| `POST` | `/contracts/import-yaml` | `admin` | Validasi dan simpan kontrak ke database. |

## 📦 Contoh File YAML Standar

Contoh lengkap dapat dilihat di [data-contract/examples/full.yaml](../data-contract/examples/full.yaml).

Struktur minimal:
```yaml
standard_version: 0.4.0
metadata:
  version: 1.0.0
  type: TABLE
  name: user_activity_logs
  owner: data_platform
  sla:
    retention: 30
    retention_unit: days
model:
  - column: user_id
    logical_type: string
    is_primary: true
```

## 💡 Tips Import
- Gunakan endpoint `/validate-yaml` terlebih dahulu untuk mendapatkan feedback instan tanpa risiko duplikasi data.
- Jika `contract_number` tidak disertakan, sistem akan meng-generate nomor unik secara otomatis.
