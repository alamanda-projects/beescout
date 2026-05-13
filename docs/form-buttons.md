# Frontend convention — Button type safety

> Cegah regresi bug "data tersimpan tanpa klik Simpan" (Issue #11).

## Aturan

**Setiap `<button>` di codebase harus memiliki atribut `type` eksplisit.**

```tsx
// ✓ benar
<button type="button" onClick={...}>Aksi</button>
<button type="submit">Simpan</button>

// ✗ salah — default HTML adalah type="submit"
<button onClick={...}>Aksi</button>
```

Berlaku juga untuk komponen shadcn `<Button>` saat dipakai sebagai submit:

```tsx
// ✓ benar untuk submit form
<Button type="submit">Simpan</Button>

// ✓ aman untuk aksi non-submit (Button.tsx default-nya type="button")
<Button onClick={...}>Aksi</Button>
```

## Kenapa

Spesifikasi HTML: `<button>` di dalam `<form>` tanpa `type` default-nya `type="submit"`.
Artinya tombol toggle / aksi internal (mode switcher, tab, accordion, hapus item) yang
dirender di dalam `<form>` akan diam-diam memicu form submit setiap kali diklik.

Insiden referensi: [Issue #11](https://github.com/alamanda-projects/beescout/issues/11) — klik tombol "Bisnis" / "Engineer" di section Struktur Data men-trigger save kontrak utama meskipun user belum klik "Simpan Kontrak".

## Defensive default

Komponen [shadcn Button](../frontend-admin/src/components/ui/button.tsx) men-default
type ke `"button"` jika consumer tidak menyediakannya. Submit button harus eksplisit
pakai `type="submit"`.

Pattern di `Button.tsx`:

```tsx
({ className, variant, size, asChild = false, type, ...props }, ref) => {
  const Comp = asChild ? Slot : 'button'
  const buttonType = asChild ? undefined : (type ?? 'button')
  return <Comp ... type={buttonType} {...props} />
}
```

`asChild` dikecualikan karena Slot meneruskan props ke child element (mis. `<Link>`)
yang bukan `<button>` HTML.

## Auto-enforcement

[`scripts/qa-form-buttons.sh`](../scripts/qa-form-buttons.sh) — scan semua `.tsx`
di kedua frontend dan fail jika menemukan:

1. Raw `<button>` tanpa atribut `type=`
2. `Button.tsx` yang tidak men-default `type="button"`

Script ini jalan di CI (`qa-form-buttons` job). PR akan diblok sampai pelanggaran
diperbaiki.

## Untuk reviewer

Saat review PR yang menyentuh form atau menambah tombol baru:

- [ ] Setiap `<button>` baru punya `type=` eksplisit
- [ ] Tombol "Simpan" yang sebenarnya pakai `type="submit"`, bukan rely pada default
- [ ] Jika menambah `<form>` baru, pastikan ada Enter-key guard (`onKeyDown`) bila form berisi banyak `<input>` non-submit
