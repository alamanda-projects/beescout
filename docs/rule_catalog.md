# Katalog Aturan (Rule Catalog)

Katalog Aturan adalah pusat repositori untuk modul pemeriksaan kualitas data (Data Quality Rules) yang dapat digunakan kembali di berbagai Data Contract.

## 📚 Konsep Utama

Setiap aturan dalam katalog mendefinisikan:
- **Code**: Pengenal unik aturan (misal: `null_check`).
- **Dimension**: Kategori kualitas data (Completeness, Validity, Accuracy, dll).
- **Description**: Penjelasan fungsional aturan.
- **Is Built-in**: Menandakan apakah aturan tersebut bawaan sistem atau kustom.

## 🚀 Memulai

### Add-on Katalog Bawaan

Katalog aturan bawaan disimpan sebagai add-on data terpisah di:

```text
repository/app/addons/catalog_rules/default.json
```

Pada setup awal via web, centang **Import add-on katalog aturan kualitas bawaan** untuk memasukkan add-on ini ke database. Jika organisasi ingin memelihara aturan sendiri, edit atau ganti add-on tersebut sebelum menjalankan setup fresh.

Endpoint internal `/catalog/seed` masih tersedia untuk root sebagai fallback operasional saat database sudah berjalan, tetapi jalur utama instalasi adalah setup web.

## 🛠️ Endpoints Terkait

| Method | Endpoint | Peran Minimal | Deskripsi |
|---|---|---|---|
| `GET` | `/catalog/rules` | `user` | List semua aturan yang tersedia |
| `GET` | `/catalog/rules/{code}` | `user` | Detail satu aturan spesifik |
| `POST` | `/catalog/rules` | `admin` | Tambah aturan kustom baru |
| `PATCH` | `/catalog/rules/{code}` | `admin` | Update aturan kustom (built-in tidak bisa diubah) |
| `DELETE` | `/catalog/rules/{code}` | `admin` | Hapus aturan kustom |

## 📝 Contoh Penggunaan dalam Kontrak

Saat mendefinisikan kualitas data pada kolom, rujuklah `code` dari katalog:

```yaml
model:
  - column: email
    quality:
      - code: format_check
        dimension: validity
        custom_properties:
          - property: regex
            value: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
```
