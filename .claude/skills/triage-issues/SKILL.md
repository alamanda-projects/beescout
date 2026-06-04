---
name: triage-issues
description: Urutkan / prioritaskan open issues & PRs BeeScout dari yang paling critical. Pakai saat user minta "urutkan issue dari critical", "ada apa saja yang open", "mana yang harus dikerjakan dulu", atau "ada lagi yang perlu di-merge".
---

# Triage & prioritaskan issue/PR

## 1. Tarik data

```bash
gh issue list --state open --limit 100 --json number,title,labels --jq '.[] | "#\(.number)\t[\(.labels|map(.name)|join(","))]\t\(.title)"'
gh pr list --state open --json number,title,headRefName,mergeable,reviewDecision --jq '.[] | "#\(.number) [\(.mergeable)] \(.headRefName) — \(.title)"'
```

Untuk issue ambigu, baca body singkat + cek "blocked by / nunggu #X" dan apakah ada ADR/audit yang sudah memutuskannya. Cek juga fase mana yang sudah merged (`gh pr list --state merged --search "#N"`).

## 2. Klasifikasi (urutan prioritas)

Repo ini **tidak** punya label `priority:*` — turunkan dari sifat masalah, bukan tebak:

1. 🔴 **Bug / integritas data aktif** — ada user ter-block atau data bisa korup (mis. visibilitas kontrak, validasi yang bisa di-bypass). Tertinggi.
2. 🟠 **Integritas data & sedang berjalan** — cross-cutting validation, strict-compliance; apalagi kalau sudah ada PR/branch jalan.
3. 🟡 **Refactor terjadwal / dependency chain** — tech-proposal yang sudah diputuskan (ADR), tinggal eksekusi; perhatikan gating ("PR-A live ≥1 deploy", backup, dll).
4. 🟢 **Fitur baru tanpa yang ter-block** — interop/converter, nice-to-have.

Naikkan prioritas bila: ada PR terbuka yang tinggal merge, atau issue jadi blocker issue lain. Turunkan bila: blocked oleh issue lain yang belum jalan.

## 3. Output

Daftar terurut dengan: nomor (link `https://github.com/<owner>/<repo>/issues/N`), satu kalimat alasan, dan status fase bila relevan ("Phase 1 merged, sisa Phase 3"). Tutup dengan **satu rekomendasi langkah berikutnya** yang konkret.

Selalu sebutkan kalau ranking diturunkan dari sifat masalah (bukan label resmi), supaya transparan.
