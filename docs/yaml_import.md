# Import & Validasi YAML

BeeScout mendukung pengelolaan Data Contract secara deklaratif menggunakan file YAML yang mengikuti [**BeeScout standard**](../data-contract/docs/README.md) (lihat juga [contoh kanonik](../data-contract/examples/full.yaml)). Untuk perbandingan dengan ODCS sebagai standar industri komparasi, lihat [comparison-odcs.md](../data-contract/docs/comparison-odcs.md). Konverter dua arah ODCS↔BeeScout di-track di [#100](https://github.com/alamanda-projects/beescout/issues/100) dan [#101](https://github.com/alamanda-projects/beescout/issues/101).

## 🛡️ Lapisan Validasi

Sistem melakukan validasi berlapis saat file YAML diunggah:

1. **Layer 1: YAML Syntax**: Memastikan file adalah format YAML yang valid.
2. **Layer 2: BeeScout Schema**:
    - Memastikan adanya field wajib (`standard_version`, `metadata`, `name`, `owner`, dll).
    - Memvalidasi tipe data (misal: `retention` harus integer).
    - Memvalidasi nilai enum (misal: `role` stakeholder harus sesuai BeeScout standard).

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

## 📤 Export ke ODCS (#101)

Kontrak BeeScout bisa diekspor ke format **ODCS v3** (Open Data Contract Standard) untuk dibagikan ke tim/tooling luar.

- **Endpoint**: `GET /datacontract/{contract_number}/export?format=odcs` → mengembalikan YAML (`Content-Disposition: attachment`, nama file `{cn}.odcs.yaml`). Akses sama dengan melihat kontrak.
- **UI**: tombol **Export ODCS** di tab **YAML** halaman detail kontrak (admin & user).
- **Pemetaan**: mengikuti [comparison-odcs.md](../data-contract/docs/comparison-odcs.md). Field overlap dipetakan ke padanan ODCS (`schema/properties`, `team/members`, `serviceLevelAgreements`, `quality`, `authoritativeDefinitions`).
- **Non-lossy**: field BeeScout-specific (`consumer[]`, `consumption_mode`, `frequency_cron`, `ports[]`, `is_clustered`/`is_audit`, `examples`) **tidak di-drop** — disimpan di `customProperties` ODCS, dengan catatan di header file.
- Konverter ada di [`repository/app/core/odcs_converter.py`](../repository/app/core/odcs_converter.py) (`beescout_to_odcs`). Importer ODCS→BeeScout (#100) akan ditambahkan ke modul yang sama; round-trip test menyusul di sana.
