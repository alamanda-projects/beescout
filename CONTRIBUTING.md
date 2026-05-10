# Contributing to BeeScout

## Paradigma Baru: Open Source Native AI

BeeScout bukan sekadar proyek Open Source biasa. Proyek ini dibangun dengan filosofi **AI-Native**, di mana pengembangan utamanya dibantu oleh AI Agent (**Claude Code**). Hal ini menciptakan peluang unik bagi siapa pun untuk berkontribusi, terlepas dari apakah mereka bisa menulis kode (coding) atau tidak.

### Visi Kontribusi Inklusif
Kami percaya bahwa inovasi terbaik datang dari kolaborasi antara ahli domain (produk, UX, analis data) dan teknologi. Di BeeScout, **non-coder** dapat berkontribusi secara langsung pada fungsionalitas sistem dengan "memerintah" AI untuk mengeksekusi visi mereka.

---

## Bagaimana Cara Berkontribusi?

Terdapat dua jalur utama untuk berkontribusi, tergantung pada latar belakang Anda:

### 1. Jalur Ahli Domain (Product, UX, Business) — "The Commander"
Jika Anda adalah seorang Product Manager, UX Designer, atau Business Analyst, fokuslah pada **Problem Solving** dan **User Experience**. Anda tidak perlu pusing dengan sintaksis bahasa pemrograman.

- **Definisi Masalah:** Buat Issue yang sangat detail mengenai problem yang ingin diselesaikan. Gunakan persona seperti **Mbak Indah (User)** atau **Mas Dimas (Developer)** untuk mendeskripsikan kebutuhan.
- **Instruksi Bahasa Alami:** Berikan instruksi seperti: *"Saya ingin tombol 'Approve' hanya muncul jika status kontrak adalah 'Pending' dan user yang login adalah Pak Bambang."*
- **Validasi Logika:** Review hasil kerja AI. Apakah alurnya sudah sesuai dengan kebutuhan bisnis? Apakah teks di UI sudah "Indonesia banget"?
- **Dokumentasi & Schema:** Perbarui `data-contract/examples/` atau dokumen panduan agar mencerminkan aturan bisnis yang baru.

### 2. Jalur Pengembang (Coder) — "The Architect"
Sebagai developer, peran Anda bergeser menjadi "Arsitek" yang memastikan kode yang dihasilkan AI tetap berkualitas tinggi, aman, dan efisien.

- **Code Review:** Tinjau Pull Request (PR) yang dihasilkan oleh kontributor (atau AI mereka). Pastikan mengikuti konvensi di [CLAUDE.md](CLAUDE.md).
- **Core Engine:** Fokus pada optimasi database, keamanan JWT, infrastruktur Docker, atau fitur kompleks yang membutuhkan sentuhan manusia.
- **Refactoring:** Jika AI mulai membuat kode yang repetitif, bantu merapikannya ke dalam komponen yang lebih modular.

---

## Alur Kerja Kontribusi

### 1. Memahami Konteks
Bacalah [README.md](README.md) dan terutama [CLAUDE.md](CLAUDE.md). `CLAUDE.md` adalah "otak" proyek ini yang berisi aturan main bagi AI agar tidak melakukan kesalahan teknis.

### 2. Buka Issue Dulu (untuk perubahan non-trivial)

Pilih template yang sesuai:

| Template | Untuk siapa | Kapan dipakai |
|---|---|---|
| [💡 Ide Bisnis](.github/ISSUE_TEMPLATE/business-idea.yml) | PM, Business Owner, Analis | Tahu masalahnya, tidak harus tahu teknisnya |
| [🐛 Bug Report](.github/ISSUE_TEMPLATE/bug-report.yml) | Siapa saja | Sesuatu rusak / tidak sesuai harapan |
| [🏗️ Tech Proposal](.github/ISSUE_TEMPLATE/tech-proposal.yml) | Developer / arsitek | Sudah punya rencana implementasi |

Untuk **kerentanan keamanan** — jangan buka issue publik, lihat [SECURITY.md](SECURITY.md).

### 3. Fork dan Clone
```bash
git clone https://github.com/alamanda-projects/beescout.git
cd beescout
```

### 4. Berinteraksi dengan Claude (Jika Anda memiliki akses)
Gunakan instruksi bahasa alami untuk melakukan perubahan. Contoh:
> *"Claude, tolong tambahkan field 'last_verified' di metadata kontrak dan tampilkan di halaman detail admin untuk Bu Retno."*

### 5. Pengujian (Wajib)
Semua kontribusi, baik dari manusia maupun AI, harus lolos uji:
- Backend: `make test-backend`
- Frontend: `make test-fe-admin` & `make test-fe-user`

### 6. Pull Request
PR template akan otomatis muncul. Pastikan mengisi:
- **Persona terdampak** + link ke issue
- **AI Usage Disclosure** (lihat section di bawah)
- **Bukti pengujian** (screenshot atau output `make test`)

---

## Cara Berkolaborasi dengan AI

BeeScout adalah proyek **AI-Native** — penggunaan AI **disambut**, bukan dilarang. Yang kami minta hanya transparansi, agar reviewer punya konteks yang tepat.

### Tiga level penggunaan AI

| Level | Maksud | Contoh |
|---|---|---|
| **Tidak menggunakan AI** | Ditulis manual sepenuhnya | Bug fix kecil yang Anda tahu persis perbaikannya |
| **AI-assisted** | AI bantu sebagian, Anda review tiap baris | Refactor dengan AI, lalu Anda baca diff sebelum commit |
| **AI-driven** | AI menulis sebagian besar, Anda jadi reviewer/operator | Claude Code menulis fitur dari spec issue |

### Kewajiban kontributor saat menggunakan AI

1. **Disclose di PR** — centang level yang sesuai di PR template
2. **Baca dan paham** kode yang dihasilkan AI sebelum commit. Jangan paste tanpa verifikasi.
3. **Bertanggung jawab atas hasil** — Anda yang menekan "submit", Anda yang akan ditanya saat review
4. **Tidak melanggar lisensi** — pastikan output AI tidak menyalin kode berlisensi tidak kompatibel (mis. GPL-2 untuk proyek AGPL-3 ini boleh, tapi proprietary tidak)

### Yang dilarang

- Mengirim PR yang Anda sendiri tidak paham isinya
- Membuat commit history palsu yang mengaburkan asal-usul AI
- Spam PR auto-generated tanpa konteks issue yang jelas

> Aturan ini **bukan untuk membatasi** — hanya memastikan kualitas tidak turun seiring volume kontribusi yang diaktifkan oleh AI.

---

## Etika Kontribusi (Code of Conduct)

Kami mengutamakan lingkungan yang **Ramah, Terbuka, dan Saling Menghargai**. Aturan lengkap di [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

Tiga prinsip inti:
1. **Hargai Ide:** Tidak ada ide yang terlalu "bodoh". Ide dari non-coder sama berharganya dengan kode dari developer senior.
2. **Komunikasi Sopan:** Gunakan bahasa yang membangun.
3. **Transparansi AI:** Lihat section *Cara Berkolaborasi dengan AI* di atas.

## Tata Kelola Proyek

Siapa membuat keputusan apa, dan bagaimana naik tier (Contributor → Trusted → Maintainer): lihat [GOVERNANCE.md](GOVERNANCE.md).

---

## Daftar Kontributor

| Nama | Peran | Spesialisasi |
|---|---|---|
| [Hani Perkasa](https://www.linkedin.com/in/haninp/) | Data Architect | System Design & Philosophy |
| [Ardhi Wahyudhi](https://www.linkedin.com/in/ardhi-wahyudhi/) | Data Engineer | Backend & Infrastructure |

---

## FAQ

**Q: Saya bukan programmer, apakah saya benar-benar bisa berkontribusi?**  
A: YA. Anda bisa berkontribusi pada penulisan spesifikasi, desain alur di Issue, atau memberikan feedback UX. Kami akan membantu menerjemahkannya menjadi kode melalui asistensi AI.

**Q: Mengapa struktur folder proyek ini sangat spesifik?**  
A: Struktur ini dirancang agar "AI-Friendly", memudahkan agen AI untuk memahami di mana letak logika bisnis, model data, dan komponen UI tanpa tersesat.
