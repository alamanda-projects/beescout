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
