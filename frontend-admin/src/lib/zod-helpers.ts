import { z } from 'zod'

/**
 * Helper zod bersama untuk konsistensi validasi form (#114 Phase 2).
 *
 * Tujuan: pesan error Bahasa Indonesia yang seragam + format check yang
 * reusable, supaya tiap form tidak menulis ulang rule yang sama. Lihat
 * audit & rencana di docs/form-validation-audit.md.
 *
 * Helper akan bertambah seiring Phase 3 (slug, username, strong password,
 * cron, dst). Saat ini baru `emailField` yang dipakai (Phase 3a-i).
 */

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
