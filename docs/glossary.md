# Glosarium — Istilah Bisnis ↔ Teknis

> Kamus ini membantu **kontributor non-teknis** memahami istilah teknis di codebase, dan sebaliknya membantu **developer** memilih kata yang tepat saat menulis UI/dokumentasi yang dilihat persona bisnis.
>
> Saat ragu istilah mana yang dipakai di UI: lihat kolom **"Dipakai di UI"**.

## Cara membaca tabel ini

- **Istilah teknis** — apa yang muncul di kode, API, dokumen teknis
- **Padanan bisnis (ID)** — bahasa Indonesia natural untuk persona non-tech
- **Penjelasan singkat** — apa artinya tanpa jargon
- **Dipakai di UI** — versi mana yang muncul di tampilan pengguna

---

## A. Konsep Inti

| Istilah teknis | Padanan bisnis (ID) | Penjelasan singkat | Dipakai di UI |
|---|---|---|---|
| Data Contract | Kontrak Data | Kesepakatan formal antara pihak yang menyediakan data dan yang memakai, berisi struktur, kualitas, dan komitmen layanan | Kontrak Data |
| Data Producer | Penyedia Data | Pihak/sistem yang menghasilkan data dan bertanggung jawab atas kualitasnya | Penyedia Data |
| Data Consumer | Pengguna Data | Pihak/sistem yang memakai data untuk analisis, laporan, atau pipeline lanjutan | Pengguna Data |
| Stewardship | Tata Kelola | Aktivitas menjaga kualitas, kepatuhan, dan akuntabilitas data | Tata Kelola |
| Data Steward | Pengelola Data | Orang yang bertanggung jawab atas kualitas dan dokumentasi sebuah dataset (persona Bu Retno) | Pengelola Data |
| Schema | Struktur Data | Definisi kolom-kolom data: nama, tipe, constraint | Struktur Data |
| Metadata | Informasi Kontrak | Info tentang kontrak (nama, pemilik, deskripsi, versi) — bukan datanya itu sendiri | Informasi Kontrak |
| ODCS | Open Data Contract Standard | Standar industri untuk format data contract yang dipakai BeeScout | (jarang muncul di UI; di README sebagai referensi) |

## B. Kualitas & SLA

| Istilah teknis | Padanan bisnis (ID) | Penjelasan singkat | Dipakai di UI |
|---|---|---|---|
| Quality Rule | Aturan Kualitas | Aturan yang dataset/kolom harus penuhi (mis. tidak boleh kosong, harus unik) | Aturan Kualitas |
| Completeness | Kelengkapan | Dimensi kualitas: apakah datanya lengkap (tidak kosong)? | Kelengkapan |
| Validity | Validitas | Dimensi kualitas: apakah formatnya benar (mis. email valid, angka di rentang yang masuk akal)? | Validitas |
| Accuracy | Akurasi | Dimensi kualitas: apakah datanya sesuai dengan kenyataan? | Akurasi |
| SLA (Service Level Agreement) | Komitmen Layanan | Janji performa dataset: kapan tersedia, seberapa sering update, berapa lama disimpan | SLA / Komitmen Layanan |
| Retention | Masa Simpan | Berapa lama data dipertahankan sebelum dihapus | Masa Simpan |
| Frequency | Frekuensi Update | Seberapa sering dataset diperbarui | Frekuensi |
| Availability | Jam Tersedia | Rentang jam saat dataset bisa diakses | Jam Tersedia |

## C. Kontrol Akses

| Istilah teknis | Padanan bisnis (ID) | Penjelasan singkat | Dipakai di UI |
|---|---|---|---|
| RBAC (Role-Based Access Control) | Hak Akses Berdasarkan Peran | Sistem keamanan: hak akses ditentukan berdasarkan peran user | (umumnya di docs/dev, jarang di UI) |
| Role / Group Access | Peran | Kategori user: root, admin, developer, user | Peran |
| Data Domain | Domain Data | Pengelompokan data berdasarkan unit bisnis (mis. penjualan, marketing, finance) | Domain Data |
| Service Account | Akun Layanan | Akun khusus untuk sistem-ke-sistem (bukan manusia), pakai key bukan password | Akun Layanan / SA |
| JWT | Token Sesi | Tanda bukti login dalam bentuk string ber-enkripsi | (tersembunyi di cookie, jarang ditampilkan) |

## D. Workflow Persetujuan

| Istilah teknis | Padanan bisnis (ID) | Penjelasan singkat | Dipakai di UI |
|---|---|---|---|
| Approval Workflow | Alur Persetujuan | Proses voting untuk perubahan kontrak yang diajukan engineer/user | Persetujuan |
| Approver | Pemberi Persetujuan | User yang punya hak vote untuk menyetujui perubahan | Pemberi Persetujuan |
| Vote | Suara | Tindakan approve/reject di sebuah usulan perubahan | Suara |
| Pending Changes | Perubahan Menunggu | Usulan yang belum mendapat semua persetujuan | Menunggu Persetujuan |
| Proposed Changes | Usulan Perubahan | Detail perubahan yang sedang menunggu vote | Usulan Perubahan |

## E. Teknis Stack

| Istilah teknis | Padanan bisnis (ID) | Penjelasan singkat | Dipakai di UI |
|---|---|---|---|
| Endpoint / API | Antarmuka Sistem | Alamat URL yang bisa dipanggil sistem lain untuk berinteraksi dengan BeeScout | (jarang di UI, di docs developer) |
| Reverse Proxy | Penjaga Lalu Lintas | Komponen yang menerima request masuk dan meneruskan ke service yang tepat (Nginx) | (tidak di UI) |
| Container | Kontainer | "Kotak" terisolasi tempat aplikasi berjalan (Docker) | (tidak di UI) |
| Migration | Migrasi Skema | Skrip untuk mengubah struktur database tanpa kehilangan data | (tidak di UI, di dev docs) |
| Pydantic Model | Model Validasi | Definisi struktur data di backend yang otomatis memvalidasi input | (tidak di UI) |
| YAML | YAML | Format file untuk konfigurasi/data yang mudah dibaca manusia | YAML (untuk import) |

## F. Atribut Kolom (Column Flags)

> Label kolom-kolom ini muncul di form Data Contract (Step 3 — Struktur Data). UI menampilkan istilah Inggris (konvensi industri data) + tooltip ⓘ dengan penjelasan ID di bawah. Sinkron dengan `frontend-admin/src/lib/field-help.ts`.

| Istilah teknis | Padanan bisnis (ID) | Penjelasan singkat | Dipakai di UI |
|---|---|---|---|
| Primary Key (`is_primary`) | Kunci Utama | Kolom kunci utama. Nilainya unik (tidak ada duplikat) dan tidak boleh kosong | Primary Key (+ tooltip ID) |
| Nullable (`is_nullable`) | Boleh Kosong | Kolom boleh kosong saat data dikirim | Nullable (+ tooltip ID) |
| Data PII (`is_pii`) | Data Pribadi | *Personal Identifiable Information* — kolom berisi data pribadi yang harus dilindungi (nama, NIK, email, dll) | Data PII (+ tooltip ID) |
| Mandatory (`is_mandatory`) | Wajib | Kolom harus diisi saat data dikirim ke kontrak. Jika kosong, data ditolak | Wajib (+ tooltip ID) |
| Partition Key (`is_partition`) | Kunci Partisi | Kolom dipakai untuk membagi data ke beberapa bagian (umumnya berdasar tanggal/region) agar query lebih cepat | Partition (+ tooltip ID) |
| Clustered (`is_clustered`) | Pengelompokan Storage | Kolom yang dipakai mengelompokkan data berdekatan di storage agar query yang memfilter kolom ini lebih efisien | Clustered (+ tooltip ID) |
| Audit (`is_audit`) | Kolom Audit | Kolom yang mencatat jejak perubahan (siapa, kapan). Umumnya: created_at, updated_at, created_by | Audit (+ tooltip ID) |

---

## Aturan saat menulis UI

Saat menulis label/teks yang dilihat persona pengguna:

1. **Default ke padanan bisnis** — gunakan kolom "Dipakai di UI"
2. **Boleh pakai istilah teknis** jika persona target adalah Mas Dimas atau Pak Bambang (mis. di halaman Service Account, OK pakai "JWT", "API key")
3. **Konsisten lintas halaman** — kalau di satu tempat pakai "Pengelola Data", di tempat lain jangan tiba-tiba "Steward"
4. **Tooltip untuk istilah baru** — jika harus pakai istilah teknis ke persona bisnis, beri tooltip

## Aturan saat menulis dokumentasi

- **Dokumen di `docs/`** boleh pakai istilah teknis bila konteksnya jelas (mis. `architecture.mmd`)
- **Dokumen yang dibaca semua kontributor** (`README.md`, `CONTRIBUTING.md`) — pakai padanan bisnis di intro, istilah teknis di section technical
- **CLAUDE.md** — pakai istilah teknis (audiensnya AI/developer)

## Menambah / merevisi entri

Glosarium hidup. Saat menemukan istilah baru yang sering muncul atau pasangan ID yang lebih natural:

1. Buka PR kecil dengan judul `docs(glossary): ...`
2. Sertakan: istilah, padanan, penjelasan, dan minimal 1 contoh tempat istilah itu muncul

---

## English Summary

This glossary maps technical terms (in code, API, docs) to natural Indonesian business terms (used in UI). Use the "Dipakai di UI" column when writing user-facing labels. Technical docs may keep technical terms; user-facing UI defaults to business terms with consistent translation across pages.
