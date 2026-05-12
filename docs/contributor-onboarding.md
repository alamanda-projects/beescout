# Onboarding Kontributor — 30 Menit Pertama

> Selamat datang! 🐝 Halaman ini adalah **jalur cepat** untuk membuat kontribusi pertama Anda di BeeScout — apapun latar belakangnya.

Pilih jalur yang sesuai:

- 🟢 **[Saya bukan developer (PM, Bisnis, Analis)](#-jalur-1-non-developer--commander-path)** — alur natural, tidak perlu install apa-apa
- 🔵 **[Saya developer / engineer](#-jalur-2-developer--architect-path)** — fork, jalankan lokal, kirim PR
- 🟡 **[Saya pakai AI (Claude Code dsb)](#-jalur-3-ai-driven-path)** — biarkan AI yang menulis kode, Anda jadi pengarah

---

## 🟢 Jalur 1: Non-Developer — "Commander Path"

**Cocok untuk**: Product Manager, Business Owner, Data Analyst, UX Designer, Domain Expert.

**Yang Anda butuhkan**: hanya akun GitHub. Tidak perlu install apapun.

### Langkah 1 — Pahami persona BeeScout (5 menit)

Buka [docs/personas.md](personas.md). BeeScout punya 4 persona pengguna:

- **Pak Bambang** (Root) — keamanan & infrastruktur
- **Bu Retno** (Admin/Steward) — kualitas & tata kelola data
- **Mas Dimas** (Developer) — integrasi pipeline teknis
- **Mbak Indah** (User/Analyst) — analisis & laporan bisnis

Setiap fitur di BeeScout dirancang untuk satu/beberapa persona. Saat Anda mengusulkan ide, sebut persona yang terdampak — itu shortcut paling cepat agar dipahami.

### Langkah 2 — Cari masalah yang ingin Anda angkat (10 menit)

Pikirkan satu hal yang menurut Anda **kurang ideal** di pengelolaan data contract di organisasi atau pekerjaan Anda. Contoh:

- *"Saat saya butuh tahu kontrak data mana yang akan expired, saya harus scroll satu per satu — tidak ada peringatan."*
- *"Halaman tambah kontrak punya 4 langkah, terlalu panjang untuk kontrak sederhana."*
- *"Istilah 'physical type' membingungkan untuk analis bisnis."*

Tidak harus ide besar. Friction kecil yang Anda alami sehari-hari justru valid karena **Anda yang merasakannya**.

### Langkah 3 — Buka issue dengan template "Ide Bisnis" (10 menit)

1. Buka https://github.com/alamanda-projects/beescout/issues/new/choose
2. Pilih **💡 Ide Bisnis / Business Idea**
3. Isi field-nya:
   - **Persona terdampak** — pilih dari dropdown
   - **Apa masalah yang ingin diselesaikan?** — bahasa natural, tidak perlu teknis
   - **Bagaimana keadaan ideal setelah masalah ini diselesaikan?** — gambaran sederhana
   - **Bagaimana kita tahu solusinya berhasil?** — kriteria sukses dari sudut pandang user
4. Submit

### Langkah 4 — Ikuti diskusi (5 menit)

Maintainer akan baca, mungkin tanya klarifikasi, mungkin minta contoh kasus konkret. Itu normal — semakin spesifik, semakin mudah implementasinya.

### Apa yang terjadi setelah issue Anda di-merge ke roadmap?

- Kalau ada developer/AI yang tertarik mengambil → mereka akan implementasi
- Anda bisa diundang me-review hasilnya dari sudut pandang persona
- Kalau Anda ingin sekalian kasih input desain (mockup di Figma, sketsa di kertas, narasi alur), itu sangat dihargai

---

## 🔵 Jalur 2: Developer — "Architect Path"

**Cocok untuk**: Backend / Frontend developer, DevOps, Data Engineer.

**Yang Anda butuhkan**: Docker Desktop, Git, akun GitHub, editor pilihan.

### Langkah 1 — Setup lokal (10 menit)

```bash
# 1. Fork via GitHub UI, lalu clone fork Anda
git clone https://github.com/<username-anda>/beescout.git
cd beescout

# 2. Copy file env
cp .env.example .env
# Edit .env — minimal ganti MONGODB_PASS dan JWT secret (lihat komentar di file)

# 3. Tambah ke /etc/hosts (sekali saja)
echo "127.0.0.1 app.localhost admin.localhost" | sudo tee -a /etc/hosts

# 4. Jalankan
make dev   # mode hot-reload — backend di :8888, admin :3001, user :3000
```

Buka http://app.localhost (user) dan http://admin.localhost (admin). Detail lengkap di [getting-started.md](../getting-started.md).

### Langkah 2 — Baca konvensi kode (5 menit)

Wajib baca cepat: [CLAUDE.md](../CLAUDE.md) — gotchas yang sudah pernah menggigit kontributor sebelumnya (RHF nested arrays, FastAPI 422, dll). Mengabaikan ini = waktu hilang debugging hal yang sudah didokumentasikan.

### Langkah 3 — Pilih issue "good first issue" atau ambil "Next" dari roadmap (5 menit)

- Lihat [issues](https://github.com/alamanda-projects/beescout/issues) dengan label `good-first-issue`
- Atau pilih dari [ROADMAP.md](../ROADMAP.md) section "Next" — comment `"Saya ambil ini"` di issue terkait

### Langkah 4 — Implementasikan + test (10 menit untuk task kecil)

```bash
# Buat branch
git checkout -b feat/nama-fitur-singkat

# Edit file...

# Test
make test           # backend + frontend
docker compose build <service>  # validasi TypeScript & build

# Commit dengan pesan jelas
git commit -m "feat: tambah filter expired di Data Contract list"
```

### Langkah 5 — Buka PR

```bash
git push origin feat/nama-fitur-singkat
```

Buka GitHub UI, klik "Compare & pull request". PR template akan otomatis muncul — isi dengan jujur, terutama section **AI Usage Disclosure**.

Reviewer akan datang dari [CODEOWNERS](../CODEOWNERS). Setelah approved, di-merge ke `main`.

---

## 🟡 Jalur 3: AI-Driven — "Komandan + AI"

**Cocok untuk**: kontributor yang ingin pakai Claude Code (atau AI lain) untuk menulis kode dari spec — baik Anda technical atau tidak.

**Yang Anda butuhkan**: setup lokal seperti Jalur 2, plus akses ke AI agent pilihan.

### Bagaimana cara kerjanya

1. **Anda buka issue** seperti Jalur 1 (Business Idea atau Tech Proposal)
2. **Setup lokal** seperti Jalur 2
3. **Beri instruksi natural** ke AI agent. Contoh ke Claude Code:
   > *"Baca CLAUDE.md dan ROADMAP.md. Lalu kerjakan issue #42 — tambah filter "tampilkan hanya yang expired" di halaman Data Contract admin. Pastikan ikut konvensi RHF dan stringify error 422 sesuai panduan."*
4. **AI akan eksekusi**, Anda jadi **reviewer + operator**
5. **Anda baca diff sebelum commit**. Tidak paham satu baris? tanya AI atau googling. Jangan commit yang tidak Anda paham.
6. **Buka PR**, di **AI Usage Disclosure** centang **AI-driven** dengan jujur

### Aturan main saat pakai AI

✅ **Boleh dan disambut**:
- Pakai AI untuk seluruh implementasi
- Pakai AI untuk refactor, debugging, dan menulis test
- Bertanya ke AI sambil belajar konvensi proyek

❌ **Dilarang**:
- Commit kode yang Anda sendiri tidak paham isinya
- Spam PR auto-generated tanpa baca diff
- Menyembunyikan bahwa Anda pakai AI (selalu disclose)

Detail lengkap di [CONTRIBUTING.md — Cara Berkolaborasi dengan AI](../CONTRIBUTING.md#cara-berkolaborasi-dengan-ai).

---

## Setelah Kontribusi Pertama

Selamat! 🎉

Apa yang terjadi selanjutnya:

- Nama Anda muncul di [GitHub contributor graph](https://github.com/alamanda-projects/beescout/graphs/contributors)
- Bila kontribusi Anda konsisten, Anda akan diundang naik ke **Trusted Contributor** ([GOVERNANCE.md](../GOVERNANCE.md))
- Anda bisa membantu review PR baru dari kontributor lain — itu kontribusi berharga juga

**Untuk kontribusi berikutnya yang scope-nya lebih besar**: baca [docs/sdlc.md](sdlc.md) — alur 7 tahap lengkap dengan Definition of Ready/Done dan strategi pengujian per layer.

## Bantuan Saat Stuck

| Saat | Pergi ke |
|---|---|
| Tidak tahu masalah/ide saya valid atau bukan | [GitHub Discussions](https://github.com/alamanda-projects/beescout/discussions) — tanya dulu sebelum buka issue |
| Setup lokal error | [getting-started.md — Troubleshooting](../getting-started.md), atau [CLAUDE.md](../CLAUDE.md) section "Common Troubleshooting" |
| Tidak yakin konvensi kode | Cari pola serupa di codebase, atau tanya di issue/PR |
| AI menghasilkan kode aneh | [CLAUDE.md](../CLAUDE.md) — kalau AI Anda ikuti panduan ini, kualitas seharusnya konsisten |
| Pertanyaan keamanan | Jangan post publik. Lihat [SECURITY.md](../SECURITY.md) |

---

## English Summary

Three contribution paths: **Non-developer** (open issues via business-idea template, no install needed), **Developer** (fork → make dev → ship PR), **AI-driven** (instruct Claude Code or similar, review & disclose). The first contribution should fit in 30 minutes regardless of path. After that, follow [GOVERNANCE.md](../GOVERNANCE.md) to grow into a Trusted Contributor and eventually Maintainer.
