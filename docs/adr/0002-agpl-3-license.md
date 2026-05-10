# ADR-0002: Memilih AGPL-3.0 sebagai Lisensi

- **Status**: Diterima
- **Tanggal**: 2026-05-10
- **Pengusul**: [@haninp](https://github.com/haninp)

## Konteks

BeeScout dirancang sebagai **platform tata kelola data contract yang dapat dipakai dan dikembangkan komunitas**. Saat akan dirilis sebagai Open Source Software, lisensi adalah keputusan filosofis yang menentukan:

- Siapa yang boleh memakai dan memodifikasi
- Apakah modifikasi harus dibagi balik
- Apa yang boleh dilakukan jika BeeScout dipakai sebagai layanan internal/komersial

Karena BeeScout pada dasarnya adalah **software yang dideploy sebagai layanan jaringan** (web app + API yang diakses pengguna), risiko utamanya adalah **"SaaS loophole"** di lisensi copyleft tradisional: perusahaan bisa fork BeeScout, modifikasi besar-besaran, deploy sebagai SaaS internal/komersial, tanpa harus membagikan modifikasinya — karena distribusi terjadi via jaringan, bukan distribusi binary.

Tujuan kami:

1. **Komunitas berbagi balik** — modifikasi yang dideploy harus tetap open
2. **Tetap ramah self-host** — perusahaan yang sekadar pakai (tidak modifikasi) harus tetap nyaman
3. **Cocok dengan filosofi AI-Native** — kontribusi dari komunitas (manusia + AI) tetap mengalir balik

## Keputusan

BeeScout dirilis di bawah **GNU Affero General Public License v3.0 (AGPL-3.0)**.

File [`LICENSE`](../../LICENSE) berisi teks lisensi resmi. [`README.md`](../../README.md) dan [`SECURITY.md`](../../SECURITY.md) menyebutkan implikasi lisensi untuk pengguna.

### Implikasi konkret untuk pengguna

| Skenario | AGPL mensyaratkan apa? |
|---|---|
| Self-host BeeScout tanpa modifikasi (apa adanya) | Tidak ada kewajiban tambahan |
| Self-host BeeScout dengan modifikasi internal saja (tidak ada user eksternal) | Tidak ada kewajiban tambahan |
| Deploy BeeScout (dimodifikasi) sebagai layanan untuk pengguna lain — termasuk lintas-organisasi atau publik | **Wajib** menyediakan source code modifikasinya kepada pengguna layanan tersebut |
| Bundling BeeScout ke dalam produk komersial | Hanya boleh jika produk turunannya juga AGPL-kompatibel |
| Memakai sebagian kode BeeScout di proyek lain | Proyek lain itu juga harus AGPL-kompatibel |

### Implikasi untuk kontributor

- Kontribusi yang dikirim ke BeeScout dianggap berlisensi sama (AGPL-3.0)
- Output AI yang dikirim sebagai kontribusi tidak boleh menyalin kode dari sumber dengan lisensi tidak kompatibel (mis. proprietary atau license yang tidak kompatibel dengan AGPL)

## Alternatif yang Dipertimbangkan

### a. MIT / Apache 2.0 (permisif)

Kelebihan: adopsi maksimum, ramah perusahaan.
Kekurangan: SaaS loophole — perusahaan besar bisa fork dan tutup hasil modifikasinya. Untuk proyek tata kelola data yang ingin tetap berbasis komunitas, ini risiko strategis.
**Tidak dipilih** karena tidak melindungi spirit "berbagi balik" yang jadi nilai inti.

### b. GPL-3.0 (copyleft tapi tidak network-aware)

Kelebihan: copyleft yang sudah teruji.
Kekurangan: punya SaaS loophole sama seperti MIT/Apache untuk software berbasis web/API. Modifikasi yang hanya dideploy via jaringan **tidak** dianggap "distribusi".
**Tidak dipilih** karena BeeScout adalah software jaringan — celah ini relevan.

### c. AGPL-3.0 (copyleft dengan klausul jaringan)

Kelebihan: menutup SaaS loophole secara eksplisit. Modifikasi yang dideploy via jaringan = wajib bagikan source.
Kekurangan: beberapa perusahaan (terutama enterprise besar) punya kebijakan "no AGPL" karena risiko legal — jadi adopsi bisa lebih kecil dari MIT/Apache.
**Dipilih** karena melindungi spirit komunitas. Trade-off adopsi vs proteksi diputuskan untuk pihak proteksi.

### d. SSPL / BUSL / fair-source license

Kelebihan: lebih ketat lagi terhadap penggunaan komersial.
Kekurangan: bukan OSI-approved, bukan "open source" dalam definisi formal, mengurangi kepercayaan komunitas.
**Tidak dipilih** karena BeeScout ingin tetap menjadi OSS yang valid (OSI-approved).

### e. Dual license (AGPL + komersial)

Kelebihan: bisa monetisasi langsung dari fork komersial.
Kekurangan: kompleks secara legal, butuh CLA (Contributor License Agreement) yang mempersulit kontributor non-tech.
**Belum dipilih** untuk fase awal. Bisa dipertimbangkan kembali jika ada kebutuhan komersial di masa depan, melalui ADR baru.

## Konsekuensi

**Positif**:
- Modifikasi yang dideploy di organisasi mana pun **wajib** bisa diakses penggunanya — sehingga komunitas berpotensi mendapat kontribusi balik
- Memberi sinyal jelas: BeeScout adalah proyek komunitas, bukan benih SaaS proprietary
- Konsisten dengan tone proyek "AI-Native, kolaboratif, transparan"

**Negatif**:
- Beberapa enterprise menolak AGPL karena kebijakan internal — mereka tidak akan adopsi atau kontribusi
- Perlu edukasi kontributor: AGPL ≠ "tidak boleh dipakai komersial" (boleh — asalkan modifikasinya juga open)

**Netral**:
- File `SECURITY.md` dan `README.md` perlu menyebutkan AGPL secara eksplisit agar pengguna sadar implikasinya sebelum deploy

**Resiko yang dimitigasi**:
- Bila di masa depan ada kebutuhan dual-license atau lisensi alternatif, bisa dilakukan via ADR baru — kontributor lama bisa diminta re-license, atau modul baru ditulis di bawah lisensi berbeda

## Referensi

- [Teks lengkap AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0.html)
- [Pertanyaan Umum AGPL (FSF)](https://www.gnu.org/licenses/why-affero-gpl.html)
- File [`LICENSE`](../../LICENSE) di root repo
- Diskusi terkait di [SECURITY.md — Catatan Lisensi](../../SECURITY.md)
