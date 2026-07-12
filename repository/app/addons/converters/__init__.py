"""
Converter add-ons — penerjemah kontrak BeeScout ↔ format eksternal (#154).

Berbeda dengan add-on data (catalog_rules, sample_contracts), folder ini
berisi add-on *kode*: satu modul per format. Menambah converter baru =
menambah satu file yang mengekspor objek `CONVERTER` — registry menemukannya
otomatis, tanpa menyentuh main.py. Lihat docs/converters.md.

Aturan main: converter adalah fungsi murni atas dict kontrak BeeScout —
dilarang import FastAPI/Mongo, supaya bisa dipakai sebagai library/CLI dan
mudah diekstrak ke paket terpisah kelak.
"""
