# BeeScout standard ↔ ODCS — Pemetaan & Perbedaan

> Standar acuan BeeScout adalah dokumen di [`/data-contract/`](../README.md). [ODCS (Open Data Contract Standard)](https://github.com/bitol-io/open-data-contract-standard) adalah **referensi industri yang menginspirasi BeeScout, bukan otoritas yang diikuti langsung.** Dokumen ini memetakan perbedaan field-by-field supaya kontributor tidak salah anggap.

## Ringkasan tingkat tinggi

| Aspek | BeeScout | ODCS (v3.1+) |
|---|---|---|
| Versioning spec | `standard_version` (semver) — internal, lihat [`docs/README.md`](README.md) | `apiVersion`, `kind` |
| Identifier kontrak | `contract_number` (NanoID-style) | `id` (UUID) |
| Filosofi | Bahasa Indonesia di field user-facing, struktur eksplisit per-section | Bahasa Inggris, struktur generik |
| Stakeholders | `metadata.stakeholders[]` dengan role enum **closed** (`owner`, `producer`, `consumer`, `reviewer`) | `team.members[]` dengan `role` field **bebas string** (tidak ada enum) |
| Tim konsumen | `metadata.consumer[]` first-class (dengan `use_case`) | **Tidak ada** — diturunkan dari `team.members` ber-role |
| Schema/kolom | `model[]` flat (column-level) | `schema[]` dengan objects & properties hierarkis |
| Koneksi data | `ports[]` (source/destination + properties bebas) | `servers[]` dengan type discriminator (snowflake/bigquery/s3/dst) |
| Contoh data | `examples` inline (csv/json string) | `properties[*].examples` per kolom |

## Pemetaan per section

### 1. Top-level

| BeeScout | ODCS | Kategori | Catatan |
|---|---|---|---|
| `standard_version` | `apiVersion` + `kind` | Overlap | BeeScout: 1 string semver; ODCS: 2 field (mis. `v3.0.0` + `DataContract`) |
| `contract_number` | `id` | Overlap | NanoID vs UUID; keduanya unique identifier |
| `metadata` | (tidak ada section explicit) | BeeScout-specific | ODCS taruh sebagian besar metadata di top-level langsung |
| `model[]` | `schema[]` | Overlap (struktur beda) | Lihat section Model |
| `ports[]` | `servers[]` | Overlap (struktur beda) | Lihat section Ports |
| `examples` | `properties[*].examples` | Overlap (lokasi beda) | BeeScout: 1 blok terpisah, biasanya csv string; ODCS: array per kolom |
| — | `name`, `version`, `status`, `tenant`, `tags`, `domain` (top-level) | ODCS-specific | Di BeeScout sebagian ada di bawah `metadata` (`name`, `version`); `tenant`/`domain` tidak ada |
| — | `description` (top-level) | ODCS-specific | BeeScout: `metadata.description.{purpose, usage}` lebih struktur |

### 2. Metadata

#### Identifikasi & ownership

| BeeScout | ODCS | Kategori | Catatan |
|---|---|---|---|
| `metadata.version` | `version` (top-level) | Overlap (lokasi beda) | Kontrak-sendiri versioning |
| `metadata.type` | `kind` atau via `servers[].type` | Overlap | BeeScout: CSV/BigQuery/dll di metadata; ODCS: di server |
| `metadata.name` | `name` (top-level) | Overlap | — |
| `metadata.owner` | (via `team.members[role=owner]`) | Overlap (derive-based di ODCS) | BeeScout: string nama tim; ODCS: derive dari team |
| `metadata.consumption_mode` | — | BeeScout-specific | `Analytical` vs `Operational`; ODCS tidak punya |

#### Description

| BeeScout | ODCS | Kategori | Catatan |
|---|---|---|---|
| `metadata.description.purpose` | `description.purpose` | Overlap | — |
| `metadata.description.usage` | `description.usage` | Overlap | — |

#### Consumer (documentary — first-class di BeeScout)

| BeeScout | ODCS | Kategori | Catatan |
|---|---|---|---|
| `metadata.consumer[].name` | — | **BeeScout-specific** | ODCS tidak punya field tim konsumen first-class |
| `metadata.consumer[].use_case` | — | **BeeScout-specific** | Field documentary penting (lihat [ADR-0007](../../docs/adr/0007-consumer-producer-representation.md)). ODCS hanya bisa simpan via `customProperties` |

> Lihat [ADR-0007](../../docs/adr/0007-consumer-producer-representation.md): di BeeScout, `consumer[]` murni documentary; access-control derive dari `stakeholders[role=consumer]`.

#### Stakeholders

| BeeScout | ODCS | Kategori | Catatan |
|---|---|---|---|
| `metadata.stakeholders[].name` | `team.members[].name` | Overlap | — |
| `metadata.stakeholders[].email` | `team.members[].username` | Overlap (semantik beda) | BeeScout: email opsional; ODCS: `username` (bisa berisi email) wajib |
| `metadata.stakeholders[].role` | `team.members[].role` | **Overlap (enum vs free)** | BeeScout: closed enum `[owner, producer, consumer, reviewer]`; ODCS: free string (mis. "data steward", "owner") |
| `metadata.stakeholders[].username` | `team.members[].username` | Overlap | BeeScout: link ke `dgrusr.username` (akun login); ODCS: identifier user |
| `metadata.stakeholders[].date_in/date_out` | `team.members[].dateIn/dateOut` | Overlap | Mostly aligned |
| — | `team.members[].replacedByUsername` | ODCS-specific | Suksesi member |
| — | `team.id`, `team.name`, `team.description` | ODCS-specific (v3.1+) | ODCS membungkus members dengan team metadata |

> **Trade-off enum vs free**: BeeScout sengaja closed enum supaya UI dropdown & approval workflow (lihat [ADR-0005](../../docs/adr/0005-approval-owner-replaces-steward.md)) bisa derive dengan deterministik. Trade-off: kurang fleksibel.

#### Quality (dataset-level)

| BeeScout | ODCS | Kategori | Catatan |
|---|---|---|---|
| `metadata.quality[].code` | `quality[].metric` atau `quality[].id` | Overlap | BeeScout: nama check; ODCS: metric name |
| `metadata.quality[].description` | `quality[].description` (di `customProperties`?) | Overlap | — |
| `metadata.quality[].dimension` | `quality[].dimension` | Overlap (enum berbeda) | BeeScout: `[completeness, validity, accuracy]` (lihat CLAUDE.md); ODCS: 7 dimensi (accuracy, completeness, conformity, consistency, coverage, timeliness, uniqueness) |
| `metadata.quality[].impact` | `quality[].businessImpact` | Overlap (nama beda) | BeeScout: enum `[operational, financial, regulatory, reputational]` (lihat [ADR-0003](../../docs/adr/0003-impact-severity-split.md)); ODCS: bebas |
| `metadata.quality[].severity` | `quality[].severity` | Overlap | BeeScout: `[low, medium, high]`; ODCS: bebas |
| `metadata.quality[].custom_properties[]` | `quality[].arguments` (object) | Overlap (struktur beda) | BeeScout: list of {property, value}; ODCS: object dict |
| — | `quality[].type` (`library`/`text`/`sql`/`custom`) | ODCS-specific | BeeScout tidak punya rule type discriminator |
| — | `quality[].operator`, `quality[].unit` | ODCS-specific | DSL evaluasi yang tidak ada di BeeScout |

#### SLA

| BeeScout | ODCS | Kategori | Catatan |
|---|---|---|---|
| `metadata.sla.availability_start/end/unit` | `serviceLevelAgreements[*]` (free struktur) | Overlap (struktur beda) | BeeScout: 3 field eksplisit; ODCS: list properties bebas |
| `metadata.sla.frequency` + `frequency_unit` | `serviceLevelAgreements[*]` | Overlap (struktur beda) | — |
| `metadata.sla.frequency_cron` | — | BeeScout-specific | Standar crontab |
| `metadata.sla.retention` + `retention_unit` | `serviceLevelAgreements[*]` retention | Overlap | — |
| `metadata.sla.effective_date` | `serviceLevelAgreements[*]` | Overlap | Lihat [#103](https://github.com/alamanda-projects/beescout/issues/103) — revisi naming/grouping diusulkan |
| `metadata.sla.end_of_contract` | `serviceLevelAgreements[*]` | Overlap | Lihat #103 |

> **Open question (#103)**: `effective_date` & `end_of_contract` di BeeScout sebaiknya dipindah dari `sla.*` ke top-level metadata (lifecycle, bukan SLA). Keputusan opsi A/B/C pending maintainer.

#### Lifecycle kontrak

| BeeScout | ODCS | Kategori | Catatan |
|---|---|---|---|
| `metadata.prev_contract` | `authoritativeDefinitions[]` (mungkin) | Overlap (lemah) | BeeScout: identifier kontrak sebelumnya |
| `metadata.contract_reference[]` (`{number, type}`) | `authoritativeDefinitions[]` | Overlap (struktur beda) | Lebih granular di BeeScout |

### 3. Model (schema kolom)

| BeeScout `model[].*` | ODCS `schema[*].properties[*].*` | Kategori | Catatan |
|---|---|---|---|
| `column` | `name` | Overlap | — |
| `business_name` | `businessName` | Overlap | Naming convention beda (snake vs camel) |
| `logical_type` | `logicalType` | Overlap (enum beda) | BeeScout: "Tipe Data Bisnis" (string/date/dst); ODCS: enum `[string, date, timestamp, time, number, integer, object, array, boolean]` |
| `physical_type` | `physicalType` | Overlap | Mostly aligned (bebas string SQL type) |
| `description` | `description` | Overlap | — |
| `is_primary` | `primaryKey` | Overlap | — |
| `is_nullable` | `required` (inverted!) | Overlap (semantik invert) | BeeScout: nullable=true; ODCS: required=false |
| `is_partition` | `partitioned` | Overlap | — |
| `is_clustered` | — | BeeScout-specific | ODCS tidak punya clustering flag |
| `is_pii` | `classification` (sebagian) | Overlap (lemah) | BeeScout: boolean PII; ODCS: enum `[confidential, restricted, public]` |
| `is_audit` | — | BeeScout-specific | Flag audit kolom |
| `is_mandatory` | `required` | Overlap (mungkin duplikatif dengan is_nullable) | Redundansi internal BeeScout |
| `sample_value[]` | `examples[]` | Overlap | — |
| `tags[]` | `tags[]` | Overlap | — |
| `quality[]` | `quality[]` (property-level) | Overlap | Strukturnya mirip metadata.quality |
| — | `id`, `physicalName`, `unique`, `primaryKeyPosition`, `partitionKeyPosition`, `encryptedName`, `transformSourceObjects`, `transformLogic`, `transformDescription`, `criticalDataElement`, `items`, `logicalTypeOptions` | ODCS-specific | ODCS jauh lebih kaya untuk metadata kolom |

> ODCS punya konsep **object → properties** hierarkis (mis. table → columns); BeeScout flat. Migrasi ODCS dengan multi-object schema perlu strategi flatten atau warning.

### 4. Ports / Servers

| BeeScout `ports[].*` | ODCS `servers[].*` | Kategori | Catatan |
|---|---|---|---|
| `object` (`source` / `destination`) | (tidak setara — ODCS tidak bedakan in/out) | **BeeScout-specific** | ODCS server = endpoint untuk akses data, bukan flow direction |
| `properties[].{property, value}` | type-specific fields (host, port, dataset, dst) | Overlap (struktur beda) | BeeScout: list k-v bebas; ODCS: schema strict per type |
| — | `server`, `type` (discriminator), `environment`, `roles`, `customProperties`, `id`, `description` | ODCS-specific | Type discriminator wajib di ODCS; tidak ada di BeeScout |

> Konsep `object: source/destination` di BeeScout tidak punya ekuivalen ODCS — ini perlu mapping eksplisit di converter (lihat #100, #101).

### 5. Examples

| BeeScout `examples` | ODCS | Kategori | Catatan |
|---|---|---|---|
| `examples.type` | — | BeeScout-specific | csv/json discriminator |
| `examples.data` | `properties[*].examples[]` | Overlap (lokasi beda) | BeeScout: 1 blok untuk dataset; ODCS: array per kolom |

## Field ODCS yang tidak ada di BeeScout

| ODCS top-level | Catatan |
|---|---|
| `apiVersion` | Disatukan dengan `kind` jadi `standard_version` di BeeScout |
| `kind` | Implicit di BeeScout (semua dokumen = data contract) |
| `status` | Lifecycle status (`draft`, `production`, dst) — BeeScout pakai `approval_status` (proses-level, bukan kontrak-level) |
| `tenant` | Multi-tenancy isolation — BeeScout pakai `data_domain` per user |
| `tags` | Top-level — BeeScout hanya per-kolom |
| `domain` | Domain klasifikasi — BeeScout punya `metadata.owner` (lebih lemah) |
| `dataProduct` | Deprecated di ODCS |
| `authoritativeDefinitions` | Link reference ke spec eksternal — BeeScout pakai `contract_reference` |
| `serviceLevelAgreements` | Struktur SLA bebas — BeeScout fixed schema di `metadata.sla` |
| `support` | Comms channel (slack/email/dst) untuk kontrak — BeeScout tidak punya |
| `price` | Cost/pricing info — BeeScout tidak punya |
| `customProperties` (top-level & per element) | Escape hatch untuk extension — BeeScout pakai approach struktur eksplisit |

## Field BeeScout yang tidak ada di ODCS

| BeeScout | Catatan |
|---|---|
| `contract_number` (NanoID) | ODCS pakai UUID di `id` |
| `metadata.consumer[]` (first-class) | Lihat [ADR-0007](../../docs/adr/0007-consumer-producer-representation.md) — kept as documentary |
| `metadata.consumption_mode` | Analytical vs Operational classification |
| `metadata.sla.frequency_cron` | Standar crontab string |
| `metadata.prev_contract` | Versi sebelumnya |
| `metadata.contract_reference[]` (struktur `{number, type}`) | ODCS pakai `authoritativeDefinitions` lebih bebas |
| `model[].is_clustered`, `is_audit` | Tidak ada di ODCS |
| `ports[].object` (`source`/`destination`) | ODCS tidak bedakan in/out |
| `examples` (top-level block) | ODCS examples per-kolom |

## Rationale divergensi yang disengaja

BeeScout sengaja berbeda dari ODCS pada beberapa hal — biasanya karena pertimbangan UX/audit/lokalisasi:

1. **`stakeholders[].role` enum closed** — supaya dropdown UI deterministik & approval workflow (ADR-0005) bisa derive approver per peran.
2. **`metadata.consumer[]` first-class** — `use_case` per tim adalah info audit penting yang tidak bisa di-replace dengan team.members generik (ADR-0007).
3. **`metadata.sla.*` fixed schema** — Bu Retno (persona non-IT) butuh form berlabel jelas, bukan free struktur.
4. **`ports[].object` source/destination** — eksplisit untuk lineage; ODCS lebih generic karena fokus ke discovery.
5. **`metadata.consumption_mode`** — distingsi Analytical vs Operational dipakai untuk SLA expectations berbeda.

Divergensi yang **bukan disengaja** (technical debt, calon harmonisasi):

- `is_nullable` vs `is_mandatory` (potensial redundan)
- `metadata.sla.effective_date` / `end_of_contract` naming asimetris (lihat #103)
- `model[].sample_value` vs ODCS `examples` (sengaja-disengaja perlu konfirmasi)

## Open questions

- Apakah `dimension` quality di BeeScout sebaiknya di-extend ke 7 ODCS dimensions, atau tetap di 3? Lihat [CLAUDE.md → Quality dimensions](../../CLAUDE.md).
- Mapping `ports[].object` saat export ke ODCS: drop (lossy) atau encode di `customProperties`?
- Mapping `stakeholders[].role: reviewer` ke ODCS: keep as-is (free string) atau map ke "data steward"?

Diskusi lebih lanjut akan masuk ke ADR khusus saat issue [#100](https://github.com/alamanda-projects/beescout/issues/100) / [#101](https://github.com/alamanda-projects/beescout/issues/101) (converter) di-eksekusi.

## Referensi

- [BeeScout standard](README.md) — sumber otoritatif
- [`examples/full.yaml`](../examples/full.yaml) — contoh kanonik
- [ODCS v3 docs](https://github.com/bitol-io/open-data-contract-standard/tree/main/docs)
- [ADR-0007 — konsolidasi konsumen/produser](../../docs/adr/0007-consumer-producer-representation.md)
- [Issue #99](https://github.com/alamanda-projects/beescout/issues/99) — issue induk dokumen ini
