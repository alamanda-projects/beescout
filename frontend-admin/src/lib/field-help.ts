/**
 * Field help — kamus terjemahan singkat untuk istilah teknis yang muncul di form.
 *
 * Label utama tetap dalam Inggris (konvensi industri data). Tooltip berisi
 * penjelasan ringkas dalam Bahasa Indonesia untuk persona non-IT seperti
 * Bu Retno (Data Steward) dan Mbak Indah (Business Analyst).
 *
 * Sinkron dengan docs/glossary.md — saat menambah entri di sini, update
 * juga glossary agar dokumentasi dan UI sejajar.
 */

export type FieldHelp = {
  /** Penjelasan singkat dalam Bahasa Indonesia (tampil di tooltip) */
  description: string
}

export const COLUMN_FLAG_HELP: Record<string, FieldHelp> = {
  is_primary: {
    description:
      'Primary Key — kolom kunci utama. Nilainya unik (tidak ada duplikat) dan tidak boleh kosong.',
  },
  is_nullable: {
    description:
      'Nullable — kolom ini boleh kosong (tidak wajib diisi saat data dikirim).',
  },
  is_pii: {
    description:
      'PII (Personal Identifiable Information) — kolom berisi data pribadi yang harus dilindungi (nama, NIK, email, dll).',
  },
  is_mandatory: {
    description:
      'Wajib — kolom ini harus diisi saat data dikirim ke kontrak. Jika kosong, data ditolak.',
  },
  is_partition: {
    description:
      'Partition Key — kolom yang dipakai untuk membagi data ke beberapa bagian (umumnya berdasarkan tanggal atau region) agar query lebih cepat.',
  },
  is_clustered: {
    description:
      'Clustered — kolom yang dipakai untuk mengelompokkan data berdekatan di storage agar query yang memfilter kolom ini lebih efisien.',
  },
  is_audit: {
    description:
      'Audit — kolom yang mencatat jejak perubahan (siapa, kapan). Biasanya: created_at, updated_at, created_by.',
  },
}
