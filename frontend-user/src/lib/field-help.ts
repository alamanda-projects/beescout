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

/**
 * Tipe Data Bisnis (`logical_type`) vs Tipe Data Teknis (`physical_type`).
 *
 * Field di form sengaja free-text agar sejalan dengan ODCS spec. Helper text
 * di bawah ini menampilkan contoh konkret + link anchor ke glossary supaya
 * Bu Retno (non-IT) dan Mbak Indah (Business Analyst) dapat memetakan istilah
 * bisnis ke tipe SQL yang sesuai.
 */
export const DATA_TYPE_HELP = {
  logical: {
    examples: 'Contoh: Tanggal, Nama, Jumlah Uang, Identifier, Status',
    tooltip:
      'Tipe Data Bisnis — istilah yang dipahami pengguna domain (mis. "Tanggal", "Nama", "Jumlah Uang"). Lihat docs/glossary.md (section "Mapping Tipe Bisnis ↔ Teknis") untuk daftar pemetaan.',
  },
  physical: {
    examples: 'Contoh: VARCHAR(255), DATE, DECIMAL(15,2), UUID, BOOLEAN',
    tooltip:
      'Tipe Data Teknis — tipe SQL/storage yang dipakai sistem (mis. VARCHAR(255), DATE, DECIMAL). Lihat docs/glossary.md (section "Mapping Tipe Bisnis ↔ Teknis") untuk daftar pemetaan.',
  },
} as const
