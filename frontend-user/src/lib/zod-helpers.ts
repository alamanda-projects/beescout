import { z } from 'zod'

/**
 * Helper zod bersama untuk konsistensi validasi form (#114 Phase 2).
 *
 * Tujuan: pesan error Bahasa Indonesia yang seragam + format check yang
 * reusable, supaya tiap form tidak menulis ulang rule yang sama. Lihat
 * audit & rencana di docs/form-validation-audit.md.
 *
 * Helper bertambah seiring Phase 3: email (3a-i), `requiredInt` (SLA #135),
 * `cronField` (3a). Lihat audit doc untuk status.
 */

/** String wajib diisi — pesan Bahasa Indonesia default. */
export const requiredString = (msg = 'Wajib diisi') => z.string().min(1, msg)

/**
 * Email opsional yang format-nya divalidasi HANYA bila diisi.
 *
 * - Kosong (`''`) → lolos (mandatory-kan terpisah bila spec menuntut, lihat
 *   #102 / audit doc).
 * - Diisi tapi bukan email valid (mis. `"abc"`) → ditolak dengan pesan jelas.
 *
 * Pakai `refine` (bukan `union`/`or`) supaya pesan error tetap spesifik —
 * union akan memunculkan pesan generic "Invalid input".
 */
export const emailField = () =>
  z.string().refine(
    (v) => v === '' || z.string().email().safeParse(v).success,
    { message: 'Format email tidak valid' },
  )

/**
 * Email wajib + format valid (#102 PR-B). Kosong → "Email wajib diisi";
 * diisi tapi bukan email valid → "Format email tidak valid".
 */
export const requiredEmailField = () =>
  z.string().min(1, 'Email wajib diisi').email('Format email tidak valid')

/**
 * Integer wajib untuk field numerik SLA (#102 PR-B slice 5).
 * String kosong atau undefined → error; angka bulat valid (termasuk 0) → lolos.
 */
export const requiredInt = (msg = 'Wajib diisi', min?: number, max?: number) =>
  z.preprocess(
    (v) => (v === '' || v == null ? undefined : Number(v)),
    z.number({ required_error: msg, invalid_type_error: msg })
      .int()
      .superRefine((n, ctx) => {
        if (min != null && n < min) ctx.addIssue({ code: z.ZodIssueCode.too_small, minimum: min, type: 'number', inclusive: true, message: `Min ${min}` })
        if (max != null && n > max) ctx.addIssue({ code: z.ZodIssueCode.too_big, maximum: max, type: 'number', inclusive: true, message: `Maks ${max}` })
      }),
  )

/**
 * Cron opsional yang sintaks-nya divalidasi HANYA bila diisi (#114 Phase 3a).
 * Crontab standar 5 field: menit jam tanggal bulan hari. Permissif — dukung
 * bintang, angka, range (`a-b`), list (`a,b`), dan step (slash). Kosong → lolos.
 * Sengaja tidak memvalidasi nama hari/bulan (MON/JAN) agar tidak memblok
 * kontrak legacy; cukup tangkap format yang jelas keliru.
 */
export const cronField = (msg = 'Format cron tidak valid (contoh: 0 6 * * *)') => {
  const part = /^(\*|\d+(-\d+)?)(\/\d+)?(,(\*|\d+(-\d+)?)(\/\d+)?)*$/
  return z.string().optional().refine(
    (v) => {
      if (!v || v.trim() === '') return true
      const fields = v.trim().split(/\s+/)
      return fields.length === 5 && fields.every((f) => part.test(f))
    },
    { message: msg },
  )
}

/**
 * Enum legacy-tolerant (#114). Menerima nilai dari `values` (kanonik) ATAU
 * dari `legacy` (nilai lama yang sudah tersimpan sebelum enum diperketat).
 * Nilai liar di luar keduanya ditolak.
 *
 * Pola ini menutup gap "field enum disimpan sebagai free string" tanpa
 * memblok edit kontrak pra-migrasi: input baru tetap dibatasi dropdown ke
 * nilai kanonik, sedangkan nilai legacy hanya lolos validasi (tidak
 * ditawarkan di UI). Lihat anti-pattern di skill resolve-issue & audit doc.
 *
 * - `required` (default true): kosong → error `emptyMsg`.
 * - `required: false`: kosong → lolos (untuk field enum opsional).
 */
export const enumField = (
  values: readonly string[],
  opts: { legacy?: readonly string[]; required?: boolean; emptyMsg?: string; invalidMsg?: string } = {},
) => {
  const { legacy = [], required = true, emptyMsg = 'Wajib dipilih', invalidMsg = 'Nilai tidak valid' } = opts
  const allowed = new Set<string>([...values, ...legacy])
  return z.string().superRefine((v, ctx) => {
    if (v == null || v === '') {
      if (required) ctx.addIssue({ code: z.ZodIssueCode.custom, message: emptyMsg })
      return
    }
    if (!allowed.has(v)) ctx.addIssue({ code: z.ZodIssueCode.custom, message: invalidMsg })
  })
}
