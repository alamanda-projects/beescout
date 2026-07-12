# ADR-0008: Field `on_failure` per quality rule — tindakan engine saat rule gagal

**Status**: Accepted
**Tanggal**: 2026-07-12
**Decider**: @haninp

---

## Konteks

Perbendaharaan aturan kualitas (#150) mengadopsi pola [Sling Data Quality](https://docs.slingdata.io/concepts/data-quality). Satu konsep Sling belum bisa diekspresikan standar BeeScout: **apa yang harus engine lakukan ketika sebuah rule gagal** (`on_failure: abort | warn | skip | quiet`). Kebutuhannya nyata untuk engine eksternal yang mengeksekusi kontrak (converter Sling #155 sudah forward-compat; HoneyGrade #147 akan mengkonsumsi deklarasi yang sama).

Empat kandidat letak dibahas (diskusi maintainer 2026-07-12, terekam di [#151](https://github.com/alamanda-projects/beescout/issues/151)):

1. **Per-rule di kontrak** (`quality[].on_failure`)
2. Default per modul di **rule catalog**
3. Default level kontrak (`metadata.quality_defaults`)
4. Hanya di **engine/converter** (tidak di kontrak)

## Keputusan

**Kandidat 1 — field opsional `on_failure` per entri `quality[]`** (dataset & kolom).

```yaml
metadata:
  quality:
    - code: row_count_range_check
      severity: high
      on_failure: abort        # abort | warn | quiet
model:
  - column: uid
    quality:
      - code: pattern_check
        on_failure: skip       # abort | warn | skip | quiet
```

Ketentuan:

- **`skip` hanya bermakna di rule kolom** — rule dataset tidak punya record untuk di-skip (cermin Sling: constraints kolom kenal `skip`; check hooks tidak). Write-path menolak `skip` di `metadata.quality[]` (422).
- **Fallback saat absen**: engine menurunkan dari `severity` — `high → abort`, selainnya `warn`. Kontrak lama tetap bermakna penuh, **tanpa migration**.
- **Dua sumbu dipertahankan**: `severity` = seberapa penting bagi bisnis; `on_failure` = tindakan mesin. Konsisten dengan filosofi ADR-0003 (pemisahan impact/severity) — satu field satu sumbu.
- **Pola strict-write/lenient-read**: Pydantic tetap `Optional[str]`; enum ditegakkan di write-path (`/datacontract/add`, `/update`, YAML validate/import).
- **Standard bump minor** `0.1.0 → 0.2.0` (field opsional baru).
- **ODCS**: tidak ada padanan — saat export disimpan sebagai argument `beescout_on_failure` agar round-trip lossless; tercatat sebagai divergensi di [comparison-odcs.md](../../data-contract/docs/comparison-odcs.md).
- **Rule catalog** boleh memberi *saran default di UI* (pre-select) — murni UX; nilai selalu tersimpan eksplisit di kontrak.

## Alternatif yang ditolak

- **Default di rule catalog (semantik)** — katalog mutable oleh admin dan berbeda antar instalasi; makna kontrak tidak boleh berubah setelah disepakati.
- **Default level kontrak** — menambah tempat ketiga yang harus dicek pembaca; fallback `severity` sudah memberi default natural. Bisa ditambah kelak (additive) bila terbukti dibutuhkan.
- **Hanya di engine/converter** — konsekuensi pelanggaran kualitas adalah inti kesepakatan producer–consumer; harus tertulis di kontrak, bukan tafsir engine.

## Konsekuensi

- Engine downstream (Sling via converter #155, HoneyGrade #145/#147) membaca satu sumber deklarasi yang deterministik: `on_failure` eksplisit, atau fallback severity yang terdefinisi.
- FE menampilkan kontrol "Saat gagal" (default "Otomatis (ikut Tingkat)") di sentence builder & eng mode.
- Menambah nilai enum baru kelak (mis. `retry`) = minor bump berikutnya + update validasi write-path.
