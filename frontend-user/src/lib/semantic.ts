/**
 * Normalisasi blok `semantic` per kolom (#162 / ADR-0009) sebelum submit.
 *
 * Form selalu menghasilkan string kosong untuk field yang tidak diisi. Tanpa
 * pembersihan ini, kontrak akan menyimpan `semantic: { entity: '', ... }` —
 * blok yang secara teknis ada tapi tidak bermakna, dan ikut terbawa ke export
 * ODCS. Kembar dengan frontend-admin/src/lib/semantic.ts — ubah keduanya.
 *
 * @returns objek berisi hanya field yang terisi, atau `undefined` bila kosong
 *   seluruhnya (kolom tanpa makna bisnis tidak menumbuhkan blok semantic).
 */
export type SemanticInput = {
  entity?: string
  concept?: string
  canonical?: boolean
  glossary?: string
  classification?: string
}

export function normalizeSemantic(semantic?: SemanticInput): SemanticInput | undefined {
  if (!semantic) return undefined

  const entity = semantic.entity?.trim() || undefined
  const concept = semantic.concept?.trim() || undefined
  const glossary = semantic.glossary?.trim() || undefined
  const classification = semantic.classification?.trim() || undefined
  // `canonical: false` adalah pernyataan eksplisit "bukan acuan utama", tapi
  // hanya bermakna bila kolom punya identitas semantik. Tanpa field lain yang
  // terisi, checkbox yang tidak pernah disentuh tidak boleh bikin blok muncul.
  const hasIdentity = Boolean(entity || concept || glossary || classification)
  if (!hasIdentity) return undefined

  return {
    ...(entity ? { entity } : {}),
    ...(concept ? { concept } : {}),
    ...(semantic.canonical ? { canonical: true } : {}),
    ...(glossary ? { glossary } : {}),
    ...(classification ? { classification } : {}),
  }
}
