# Converter Add-ons — BeeScout ↔ Format Eksternal

BeeScout menyimpan data contract dalam satu bentuk kanonik ([standar internal](../data-contract/docs/README.md)). **Converter** menerjemahkannya dari/ke format eksternal — untuk interop dengan spec lain (ODCS) maupun engine kualitas yang mengeksekusi aturan (lihat [quality-rules.md](../data-contract/docs/quality-rules.md)).

Sejak #154 converter distandarkan sebagai **add-on kode**: satu modul per format di [`repository/app/addons/converters/`](../repository/app/addons/converters/), ditemukan otomatis oleh registry. Menambah format baru **tidak menyentuh `main.py`**.

## Format tersedia

| format_id | Label | Export | Import | Sejak |
|---|---|---|---|---|
| `odcs` | ODCS v3 (Open Data Contract Standard) | ✅ | ✅ | #100/#101 |

Daftar runtime: `GET /converters`.

## Permukaan API

| Endpoint | Peran |
|---|---|
| `GET /converters` | Daftar converter (format_id, label, can_export, can_import) |
| `GET /datacontract/{cn}/export?format=<id>` | Unduh kontrak dalam format eksternal |
| `POST /contracts/validate-yaml?format=<id>` | Validasi file eksternal (dikonversi → BeeScout dulu, lalu jalur validasi sama) |
| `POST /contracts/import-yaml?format=<id>` | Import file eksternal (konversi → enforcement → insert) |

`format=beescout` (default di validate/import) = tanpa konversi. Format tak dikenal → `400` beserta daftar format yang tersedia.

## Menambah converter baru

1. Buat satu file `repository/app/addons/converters/<format>.py`.
2. Tulis fungsi konversinya — **fungsi murni**:
   - `export`: `dict` kontrak BeeScout → `str` (isi file siap unduh)
   - `import`: `dict` hasil parse file eksternal → `(dict BeeScout, list[str] warnings)`
   - **Dilarang** import FastAPI/Mongo/state global — converter harus bisa dipakai sebagai library/CLI dan mudah diekstrak ke paket terpisah.
   - Prinsip non-lossy: field BeeScout tanpa padanan → simpan di mekanisme extension format tujuan (mis. `customProperties` di ODCS); field eksternal yang di-drop → catat di `warnings`, jangan gagal diam-diam.
3. Registrasikan di akhir modul:

   ```python
   from app.addons.converters.base import Converter

   CONVERTER = Converter(
       format_id="sling",                # dipakai di ?format=
       label="Sling YAML",
       file_extension="sling.yaml",      # nama file unduhan: <cn>.<ext>
       media_type="application/yaml",
       export_fn=beescout_to_sling,      # None bila import-only
       import_fn=None,                   # None bila export-only
   )
   ```

4. Tambah test di `repository/tests/` (mirror `test_odcs_converter.py` untuk mapping, `test_converter_registry.py` sudah menguji framework).
5. Update tabel "Format tersedia" di dokumen ini.

Validasi hasil import **bukan** urusan converter — endpoint yang menjalankan Pydantic/YAML validator setelah konversi. Converter cukup jujur soal apa yang tidak bisa dipetakan (warnings).

## Kenapa add-on, bukan hardcode / repo terpisah

- Preseden add-on data sudah ada (`addons/catalog_rules`); ini memperluasnya ke add-on kode.
- In-repo dulu (maintainer tunggal) — disiplin fungsi-murni menjaga opsi ekstraksi ke paket/repo terpisah tetap murah bila ada traksi kontributor.
- **HoneyGrade bukan add-on di sini**: produk berbayar, BeeScout ber-AGPL-3 (ADR-0002) — HoneyGrade mengkonsumsi **data** via API ODCS (#145), mapping di sisi mereka.
