---
name: cleanup-branches
description: Bersihkan branch lokal yang sudah tidak relevan (sudah merged / remote-nya terhapus) dan sinkronkan main. Pakai saat user minta "bersihkan branch", "cleanup branch", atau setelah sebuah PR di-merge.
---

# Cleanup branches

## 1. Sinkron & prune

```bash
git checkout main && git pull --ff-only
git fetch --prune          # buang ref remote yang sudah dihapus di GitHub
```

## 2. Identifikasi yang stale

```bash
git branch -vv             # cari yang ber-tag ": gone" (remote sudah dihapus)
gh pr list --state open --json headRefName --jq '.[].headRefName'   # branch yang MASIH dipakai PR terbuka — JANGAN hapus
```

Branch aman dihapus = sudah merged ATAU remote-nya `gone`, DAN tidak ada di daftar PR terbuka.

## 3. Hapus

**Penting**: repo ini **squash-merge**, jadi `git branch -d` akan menolak ("not fully merged") walau PR sudah merged — karena squash bikin commit baru. Verifikasi PR memang MERGED lalu pakai `-D`:

```bash
gh pr view <N> --json state,mergedAt --jq '"[\(.state)] \(.mergedAt)"'   # pastikan MERGED
git branch -D <branch>
```

## 4. Konfirmasi

```bash
git branch -vv   # idealnya tinggal main (+ branch kerja yang masih hidup)
```

Laporkan ringkas: branch apa yang dihapus, apa yang tersisa, dan apakah ada PR terbuka. Jangan hapus branch yang masih punya PR terbuka.
