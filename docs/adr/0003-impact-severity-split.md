# ADR-0003: Pisah field `impact` menjadi `impact` + `severity`

**Status**: Accepted
**Tanggal**: 2026-05-15
**Decider**: @haninp

---

## Konteks

Field `impact` di Quality Rule saat ini menerima tiga value: `operational`, `high`, `low`.

Ini mencampur dua dimensi taksonomi yang berbeda dalam satu field:

| Value | Dimensi yang dimaksud |
|---|---|
| `operational` | **Jenis dampak** — area mana yang terdampak |
| `high` | **Tingkat keparahan** — seberapa parah dampaknya |
| `low` | **Tingkat keparahan** — seberapa parah dampaknya |

Akibat di UI:
- Engineer mode: `Operasional / Tinggi / Rendah` — semantik tidak konsisten dalam satu pilihan
- Biz mode: `'Cukup penting' | 'Penting sekali' | 'Rendah'` — urutan tidak monotonik

Verifikasi canonical di `data-contract/examples/full.yaml` hanya menggunakan `impact: operational` — menguatkan bahwa `high`/`low` adalah ekstensi BeeScout yang belum terformalisasi.

## Keputusan

Pisah menjadi dua field terpisah:

```python
impact: Optional[str]    # operational | financial | regulatory | reputational
severity: Optional[str]  # low | medium | high
```

UI menampilkan dua input terpisah:
- **Biz mode**: dua baris radio button — "Jenis dampak" + "Tingkat"
- **Eng mode**: dua dropdown `impact` + `severity` berdampingan

## Alasan

1. **Monotonik di UI**: `low → medium → high` punya urutan yang jelas, sedangkan `operational | high | low` tidak.
2. **Extensible**: `impact` bisa diperluas ke `financial`, `regulatory`, `reputational` tanpa memengaruhi severity.
3. **Konsisten dengan ODCS spec**: spec ODCS tidak mendefinisikan `high`/`low` sebagai impact value. Memisahkan keduanya menjaga alignment dengan upstream spec.
4. **Persona Bu Retno**: pengguna bisnis butuh makna yang jelas — "jenis dampak apa" dan "seberapa parah" adalah dua pertanyaan berbeda.

## Konsekuensi

### Positif
- Semantik field menjadi jelas
- Pilihan bisa diperluas secara independen
- UI severity monotonik (rendah → sedang → tinggi)

### Negatif / Risiko
- **Breaking change** untuk data lama yang menyimpan `impact: high` atau `impact: low`
- Butuh migration script yang dijalankan saat deploy

### Mitigasi breaking change
- `severity: Optional[str] = None` — field opsional, kontrak lama tetap valid
- Migration script `repository/scripts/migrate_impact_severity.py` — idempoten, dry-run dulu
- Logika migrasi: `impact='high'` → `(impact='operational', severity='high')`, `impact='low'` → `(impact='operational', severity='low')`, `impact='operational'` → `severity='medium'` (default)
- Pydantic menerima value lama (free `Optional[str]`) — tidak ada validasi enum, sehingga kontrak lama tidak langsung error

## Alternatif yang ditolak

**Tidak pisah, hanya rename value**: `high → high_operational`, `low → low_operational` — tidak menyelesaikan masalah semantik, hanya memindahkan kebingungan.

**Pisah tapi dengan backward-compat validator**: Pydantic validator yang auto-konversi `high`/`low` saat read — lebih kompleks, dan menyembunyikan masalah alih-alih memperbaikinya.

## Referensi

- [Issue #4](https://github.com/alamanda-projects/beescout/issues/4)
- `data-contract/examples/full.yaml`
- [ODCS spec — quality](https://github.com/bitol-io/open-data-contract-standard)
- `docs/personas.md` — persona Bu Retno
