<!--
Terima kasih atas kontribusinya! 🐝
Mohon isi template di bawah ini agar reviewer mudah memahami perubahan Anda.
Hapus section yang tidak relevan untuk perubahan Anda.
-->

## Ringkasan

<!-- Apa yang berubah dalam PR ini? Cukup 1-3 kalimat. -->


## Mengapa perubahan ini diperlukan?

<!-- Hubungkan ke issue terkait, atau jelaskan masalah/kebutuhan yang mendorong perubahan ini.
     Sebutkan persona pengguna yang terdampak: Pak Bambang (root), Bu Retno (admin),
     Mas Dimas (developer), atau Mbak Indah (user). Lihat docs/personas.md.
-->

- Closes #...
- Persona terdampak: <!-- mis. "Bu Retno (admin)" atau "Mbak Indah (user)" -->

## Jenis Perubahan

<!-- Centang yang sesuai -->

- [ ] 🐛 Bug fix (perubahan non-breaking yang memperbaiki masalah)
- [ ] ✨ Fitur baru (perubahan non-breaking yang menambah fungsi)
- [ ] 💥 Breaking change (fix atau fitur yang menyebabkan perilaku lama berubah)
- [ ] 📚 Dokumentasi
- [ ] 🔧 Refactor / perbaikan internal (tidak mengubah perilaku yang terlihat)
- [ ] 🔒 Keamanan
- [ ] 🧪 Test

## Bukti Pengujian

<!-- Wajib untuk perubahan kode. Tunjukkan PR ini benar-benar bekerja. -->

- [ ] `make test-backend` lulus (jika menyentuh backend)
- [ ] `make test-fe-admin` lulus (jika menyentuh frontend-admin)
- [ ] `make test-fe-user` lulus (jika menyentuh frontend-user)
- [ ] Diuji manual di browser / curl (lampirkan screenshot atau output)

<details>
<summary>Screenshot / output</summary>

<!-- Tempel screenshot atau cuplikan terminal di sini -->

</details>

## AI Usage Disclosure

> BeeScout adalah proyek **AI-Native OSS**. Penggunaan AI tidak dilarang — justru disambut.
> Kami hanya minta transparansi agar reviewer tahu konteks asal perubahan.

- [ ] Tidak menggunakan AI / dibuat sepenuhnya manual
- [ ] **AI-assisted** — saya menggunakan AI untuk sebagian (mis. boilerplate, refactor) lalu meninjau hasilnya
- [ ] **AI-driven** — AI (mis. Claude Code) menulis sebagian besar perubahan; saya bertindak sebagai reviewer/operator

Jika AI digunakan, saya menyatakan:

- [ ] Saya telah **membaca dan memahami** semua kode yang dihasilkan AI
- [ ] Saya bertanggung jawab atas hasil akhir, sebagaimana jika saya menulisnya sendiri
- [ ] Saya tidak hanya menempel output AI tanpa verifikasi

## Checklist Reviewer

- [ ] PR mengikuti konvensi di [CLAUDE.md](../CLAUDE.md)
- [ ] Tidak ada secret, token, atau kredensial yang masuk ke repo
- [ ] Tidak menyentuh `LICENSE`, `.env`, atau file generate-only kecuali memang itu fokus PR
- [ ] Sudah memperbarui dokumentasi terkait (`docs/`, `CHANGELOG.md`) jika perlu
- [ ] Commit message jelas (lihat [CONTRIBUTING.md](../CONTRIBUTING.md))

## Catatan Tambahan untuk Reviewer

<!-- Hal-hal yang perlu perhatian khusus, trade-off yang dipilih, atau pertanyaan terbuka -->
