# Persona Pengguna BeeScout

> Dokumen ini adalah **single source of truth** untuk persona pengguna BeeScout.
> Setiap fitur, halaman, dan keputusan UX harus bisa dijawab: "ini untuk persona yang mana, dan menyelesaikan masalah apa?"
>
> Saat membuka issue/PR, sebutkan persona yang terdampak — itu shortcut paling cepat untuk reviewer memahami konteks Anda.

## Mengapa pakai persona?

Tanpa persona, fitur cenderung dirancang untuk "pengguna umum" yang tidak ada wujudnya. Dengan persona spesifik:

- **PM/Business** punya bahasa konkret untuk bilang "ini buat siapa"
- **Developer** tahu prioritas: kenyamanan Mas Dimas vs ketegasan kontrol Pak Bambang seringkali berlawanan — persona memaksa kita memilih
- **AI (Claude Code)** punya konteks user yang stabil saat menerjemahkan spec ke kode
- **Reviewer** bisa cepat menilai: "apakah perubahan ini benar-benar membantu Bu Retno, atau hanya bagus di teori?"

Empat persona di bawah dipilih karena mencerminkan **rentang tanggung jawab dan tingkat teknis** yang harus dilayani BeeScout. Bukan daftar tertutup — kalau ada persona kelima yang muncul dari kebutuhan nyata, dokumen ini akan diperluas.

---

## 1. Pak Bambang — Superadmin / Root

| Atribut | Detail |
|---|---|
| **Role di sistem** | `root` |
| **Akses** | Admin Frontend (admin.localhost) |
| **Latar belakang** | IT/Infrastructure manager, 10+ tahun pengalaman |
| **Tingkat teknis** | Tinggi (paham server, security, environment variables) |

**Tujuan utama**: Memastikan sistem aman, stabil, dan kredensial terjaga.

**Mindset**: *"Sistem ini harus aman. Tidak ada secret yang bocor. Setiap user tahu batas haknya."*

**Aktivitas khas**:
- Initial bootstrap (`/setup`) — hanya dia yang punya wewenang
- Mengelola user lintas role (CRUD, aktif/non-aktifkan)
- Konfigurasi environment variable, secret rotation
- Audit log (saat fitur tersedia)

**Kekhawatiran utama**:
- Kredensial atau service account key bocor
- User punya akses lebih dari yang seharusnya
- Sistem down karena perubahan tidak terkontrol

**Ketika fitur dirancang untuk Pak Bambang, prioritaskan**: kontrol, audit trail, kemampuan blocking yang cepat — *meski mengorbankan kenyamanan*.

---

## 2. Bu Retno — Admin / Data Steward

| Atribut | Detail |
|---|---|
| **Role di sistem** | `admin` |
| **Akses** | Admin Frontend |
| **Latar belakang** | Data Governance Lead, ex-Business Analyst |
| **Tingkat teknis** | Menengah (paham SQL, schema, tapi tidak coding sehari-hari) |

**Tujuan utama**: Menjaga kualitas data dan kepatuhan kontrak data lintas divisi.

**Mindset**: *"Setiap kontrak data harus valid, terstandar, dan punya akuntabilitas yang jelas."*

**Aktivitas khas**:
- CRUD Data Contract (buat, ubah, hapus)
- Mengelola Rule Catalog (aturan kualitas data reusable)
- Onboard user baru ke domain data tertentu
- Approve/reject perubahan kontrak yang diajukan engineer

**Kekhawatiran utama**:
- Kontrak yang tidak konsisten antar divisi
- User mengubah kontrak kritis tanpa review
- Aturan kualitas data berbeda-beda di tiap kontrak

**Ketika fitur dirancang untuk Bu Retno, prioritaskan**: standardisasi (template, dropdown, validasi), kemudahan review (diff yang jelas, history), dan dokumentasi kontekstual di UI.

---

## 3. Mas Dimas — Developer / Data Engineer

| Atribut | Detail |
|---|---|
| **Role di sistem** | `developer` |
| **Akses** | User Frontend (app.localhost) — mode `eng` |
| **Latar belakang** | Backend / Data Engineer, 3-5 tahun pengalaman |
| **Tingkat teknis** | Tinggi (coding sehari-hari, paham API, schema, container) |

**Tujuan utama**: Mengintegrasikan kontrak data yang **dikonsumsi timnya** ke dalam pipeline teknis.

**Mindset**: *"Saya butuh schema teknis yang presisi dan API endpoint yang stabil untuk kontrak yang dikonsumsi tim saya."*

> **Scope akses**: Sama dengan Mbak Indah — Mas Dimas melihat kontrak di mana **timnya tercantum sebagai consumer** di `metadata.consumer[]`. Tim adalah unit-nya; di dalam satu tim ada sisi teknis (Mas Dimas) dan sisi bisnis (Mbak Indah).
> Visi cross-team (lintas pipeline, lintas divisi) ada di tangan **Bu Retno** sebagai steward, bukan Mas Dimas.

**Aktivitas khas**:
- Membaca detail teknis kontrak yang timnya konsumsi (schema, physical type, constraint)
- Generate Service Account Key untuk integrasi pipeline
- Mengajukan perubahan kontrak (pending approval ke admin/steward)
- Konsumsi API endpoint untuk validasi di CI/CD pipeline timnya

**Kekhawatiran utama**:
- Schema kontraknya berubah tanpa notifikasi → pipeline rusak
- Service Account expire saat tengah malam
- Dokumentasi technical type tidak match dengan implementasi

**Ketika fitur dirancang untuk Mas Dimas, prioritaskan**: presisi teknis (physical_type lengkap, constraint formal), API stability, version awareness, dan akses ke raw JSON/YAML — **dalam scope kontrak yang ditugaskan**.

**Bedanya Mas Dimas vs Mbak Indah**: tujuan & sudut pandang — bukan luas akses. Mas Dimas membaca dengan kacamata teknis (apa yang harus saya implementasikan?), Mbak Indah membaca dengan kacamata bisnis (apakah data ini bisa saya pakai?).

---

## 4. Mbak Indah — User / Business Analyst

| Atribut | Detail |
|---|---|
| **Role di sistem** | `user` |
| **Akses** | User Frontend — mode `biz` |
| **Latar belakang** | Business Analyst / Reporting, latar belakang bisnis (bukan IT) |
| **Tingkat teknis** | Rendah-Menengah (pakai Excel/SQL dasar, tidak coding) |

**Tujuan utama**: Memahami kontrak data yang **dikonsumsi timnya** untuk keperluan analisis dan laporan.

**Mindset**: *"Kontrak yang dikonsumsi tim saya datanya seperti apa? Bisa saya pakai untuk laporan bulanan? Apakah angkanya bisa dipercaya?"*

> **Scope akses**: Sama dengan Mas Dimas — Mbak Indah melihat kontrak di mana **timnya tercantum sebagai consumer** di `metadata.consumer[]`. Tim yang sama mencakup sisi teknis (Mas Dimas) dan sisi bisnis (Mbak Indah) — satu kontrak terlihat oleh keduanya, hanya kacamatanya yang berbeda.
> Discovery global ("apa saja data yang ada di organisasi?") **bukan** tanggung jawab Mbak Indah — itu domain Bu Retno yang melihat keseluruhan.

**Aktivitas khas**:
- Membaca kontrak data yang timnya konsumsi (deskripsi naratif, makna kolom)
- Mengecek SLA: "datanya update jam berapa? berapa lama disimpan?"
- Mengecek aturan kualitas: "kolom ini boleh kosong tidak?"
- Mengajukan perubahan deskripsi/aturan jika ada penyesuaian dari sisi bisnis

**Kekhawatiran utama**:
- Pakai data yang salah karena nama kolom membingungkan
- Laporan tiba-tiba kosong karena pipeline upstream rusak
- Tidak tahu siapa yang harus dihubungi saat ada pertanyaan

**Ketika fitur dirancang untuk Mbak Indah, prioritaskan**: bahasa bisnis (bukan istilah teknis), deskripsi naratif yang jelas, indikator visual untuk SLA & quality, dan kontak owner/steward yang mudah ditemukan.

---

## Cara memakai persona di kontribusi

### Saat membuka **Issue**

Sebut persona di awal description:

> "Saat ini **Bu Retno** harus scroll satu per satu untuk cari kontrak yang sudah expired..."

Issue template `business-idea.yml` punya dropdown persona — tinggal pilih.

### Saat membuka **Pull Request**

Di PR template, isi field **Persona terdampak**:

> Persona terdampak: **Mbak Indah** — fitur ini menambah filter "tampilkan hanya yang ada di domain saya" sehingga dia tidak bingung melihat data yang tidak relevan.

### Saat **review PR**

Reviewer berhak menanyakan:
- "Persona yang disebut di description benar terbantu? Bagaimana?"
- "Apakah perubahan ini bertentangan dengan kepentingan persona lain (mis. menambah kemudahan Mas Dimas tapi mengurangi kontrol Pak Bambang)?"

---

## Memperluas atau merevisi persona

Persona ini bukan dogma. Bila kebutuhan nyata menunjukkan persona kelima atau detail yang berubah, ajukan perubahan via **Tech Proposal** ([template](.github/ISSUE_TEMPLATE/tech-proposal.yml)) — bukan langsung edit dokumen ini.

Perubahan persona = perubahan filosofi produk, jadi butuh diskusi maintainer + tim.

---

## English Summary

BeeScout serves four user personas: **Pak Bambang** (Root, infra-focused), **Bu Retno** (Admin/Data Steward, governance), **Mas Dimas** (Developer, technical integration), **Mbak Indah** (Business Analyst, data discovery). Every feature should explicitly serve one or more personas. Issue and PR templates ask which personas are affected — this is the fastest way for reviewers to understand context.
