import { z } from 'zod'

/**
 * Helper zod bersama untuk konsistensi validasi form (#114 Phase 2).
 *
 * Tujuan: pesan error Bahasa Indonesia yang seragam + format check yang
 * reusable, supaya tiap form tidak menulis ulang rule yang sama. Lihat
 * audit & rencana di docs/form-validation-audit.md.
 *
 * Helper bertambah seiring Phase 3: email (3a-i), username/password (3b/3e),
 * `requiredInt` (SLA #135), `cronField` (3a). Lihat audit doc untuk status.
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
 * Username: 3–50 karakter, hanya huruf & angka (tanpa spasi atau karakter
 * khusus apa pun — termasuk garis bawah). Dipakai saat membuat akun baru
 * (user create, setup root pertama).
 */
export const usernameField = () =>
  z.string()
    .min(3, 'Minimal 3 karakter')
    .max(50, 'Maksimal 50 karakter')
    .regex(/^[a-zA-Z0-9]+$/, 'Hanya huruf dan angka, tanpa karakter khusus')

/**
 * Password kuat: min 8 karakter dengan huruf besar, kecil, angka, dan
 * karakter khusus. Dipakai saat set password (user create, setup).
 */
export const strongPassword = (msg = 'Minimal 8 karakter') =>
  z.string()
    .min(8, msg)
    .regex(/[A-Z]/, 'Harus ada huruf besar')
    .regex(/[a-z]/, 'Harus ada huruf kecil')
    .regex(/[0-9]/, 'Harus ada angka')
    .regex(/[^A-Za-z0-9]/, 'Harus ada karakter khusus')

/**
 * Password opsional yang divalidasi kekuatan-nya HANYA bila diisi — untuk
 * form edit user (kosong = tidak mengubah password). Pakai refine supaya
 * field kosong lolos tanpa memicu rule strength.
 */
export const optionalStrongPassword = () =>
  z.string().refine(
    (v) => v === '' || strongPassword().safeParse(v).success,
    { message: 'Min. 8 karakter dengan huruf besar, kecil, angka, dan karakter khusus' },
  )

/**
 * Integer wajib untuk field numerik SLA (#102 PR-B slice 5).
 * String kosong atau undefined → error; angka bulat valid (termasuk 0) → lolos.
 * Menggunakan preprocess agar empty string dari <input type="number"> tidak
 * ter-coerce ke 0 secara silent.
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
