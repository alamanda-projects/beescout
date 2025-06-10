# Data Contract Standard

## Executive Summary

Dokumen ini akan menjelaskan beberapa hal penting terkait pembuatan Data Contract. Halaman ini akan mulai dari contoh YAML dan akan diikuti oleh beberapa penjelasan mendetil terkait setiap kolom yang ada.

## Table of Content

- [Executive Summary](./README.md#executive-summary)
- [Table of Content](./README.md#table-of-content)
- [Data Contract YAML Demographics](./README.md#data-contract-yaml-demographics)
  - [General Section](./README.md#general-section)
  - [Metadata Section](./README.md#metadata-section)
    - [Contoh Metadata Section](./README.md#contoh-metadata-section)
  - [Model Section](./README.md#model-section)
    - [Contoh Model Section](./README.md#contoh-model-section)
  - [Ports Section](./README.md#ports-section)
    - [Contoh Ports Section](./README.md#contoh-ports-section)
  - [Examples Section](./README.md#examples-section)
    - [Contoh Examples Section](./README.md#contoh-examples-section)

## Data Contract YAML Demographics

```
standard_version: 0.4.0
contract_number: {{random string}}

metadata:
    ...

model:
    ...

ports:
    ...

examples:
    ...
```

Data Contract akan terbagi menjadi beberapa bagian utama. Setiap bagian akan dijelaskan pada beberapa bagian dibawah ini.

---

### General Section

<!-- This field presenting version of standard Data Contract. this standard_version follow semantic versioning that you can read more about it at this [https://semver.org](https://semver.org). -->

Field ini menggambarkan standar versi dari Data Contract_. _Standard versioning_ yang diterapkan akan mengikuti standar **_semantic versioning_** yang dapat dibaca lebih lanjut pada https://semver.org.

| Field            | Required | Definitions                                                                                |
| ---------------- | -------- | ------------------------------------------------------------------------------------------ |
| standard_version | YES      | Standar versi yang digunakan untuk membangun Data Contract. Mengikuti semantic versioning. |
| contract_number  | YES      | Pengidentifikasi unik (NanoID)                                                             |

penjelasan ringkas mengenai Semantic Versioning 2.0.0 :

```
Given a version number MAJOR.MINOR.PATCH, increment the:

1. MAJOR version when you make incompatible API changes
2. MINOR version when you add functionality in a backward compatible manner
4. PATCH version when you make backward compatible bug fixes

Additional labels for pre-release and build metadata are available as extensions to the MAJOR.MINOR.PATCH format.
```

---

### Metadata Section

<!-- This section contains metadata information about the contract. This metadata section were contains : -->

Bagian ini berisikan informasi metadata dari Data Contract. Bagian ini mempunyai beberapa informasi terkait dengan :

- Deskripsi / penjelasan
- Kualitas Data
- SLAs (_Service Level Agreements_)
- Pemangku kepentingan (_Stakeholders_)

| Field                                            | Required | Definitions                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ------------------------------------------------ | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| metadata.version                                 | YES      | Versi kontrak data ini mencerminkan evolusinya sendiri dan mengikuti [Semantic Versioning](https://semver.org)                                                                                                                                                                                                                                                                                                                                       |
| metadata.type                                    | YES      | Jenis produk data (_data product_) [csv, bigquery view, tables, json, dll.]                                                                                                                                                                                                                                                                                                                                                                          |
| metadata.name                                    | YES      | Nama dataset / produk data (_data product_)                                                                                                                                                                                                                                                                                                                                                                                                          |
| metadata.owner                                   | YES      | Pemilik dataset / produk data (_data product_) (bisa nama tim, sistem, atau produk)                                                                                                                                                                                                                                                                                                                                                                  |
| metadata.consumption_mode                        | NO       | Tujuan konsumsi bisa berupa [Analytical, Operational]                                                                                                                                                                                                                                                                                                                                                                                                |
| metadata.description.purpose                     | YES      | Tujuan dataset / produk data (_data product_)                                                                                                                                                                                                                                                                                                                                                                                                        |
| metadata.description.usage                       | YES      | Menjelaskan untuk penggunaan apa dataset digunakan [Private, Public]                                                                                                                                                                                                                                                                                                                                                                                 |
| metadata.consumer.name                           | YES      | Nama tim, sistem atau _consumer apps_ produk data (_data product_)                                                                                                                                                                                                                                                                                                                                                                                   |
| metadata.consumer.use_case                       | YES      | Deskripsi singkat use case yang dapat dijalankan dengan dataset ini.                                                                                                                                                                                                                                                                                                                                                                                 |
| metadata.stakeholders.name                       | YES      | Berisikan nama untuk mengidentifikasi pemilik produk data (_data product_) atau individu yang bertanggung jawab atas produk ini, termasuk _Product Owner, Product Manager_, atau anggota tim lain.                                                                                                                                                                                                                                                   |
| metadata.stakeholders.email                      | YES      | Berisikan email untuk mengidentifikasi pemilik produk data (_data product_) atau individu yang bertanggung jawab atas produk ini, termasuk _Product Owner, Product Manager_, atau anggota tim lain.                                                                                                                                                                                                                                                  |
| metadata.stakeholders.role                       | YES      | [*owner* -> yang memiliki otoritas penuh terkait dataset; *producer* -> yang memproduksi data, seperti DBA, *Tech lead*, *Data Engineer*, *Analytics Engineer*, *HoE (Head of Engineering)* atau siapa saja yang memiliki kemampuan teknis terkait penyajian data, *consumer* -> yang akan menggunakan dataset; *reviewer* -> yang memiliki kemampuan sebagai reviewer (untuk keperluan tata kelola), seperti Data Governance, GRC, Security] |
| metadata.stakeholders.date_in                    | YES      | Tanggal dan waktu ketika pemangku kepentingan (_stakeholders_) ditetapkan sebagai pemangku kepentingan.                                                                                                                                                                                                                                                                                                                                              |
| metadata.stakeholders.date_out                   | NO       | Tanggal dan waktu ketika pemangku kepentingan (_stakeholders_) dikeluarkan dari daftar pemangku kepentingan.                                                                                                                                                                                                                                                                                                                                         |
| metadata.quality.code                            | NO       | Nama (_code name_) proses pemeriksaan kualitas data                                                                                                                                                                                                                                                                                                                                                                                                  |
| metadata.quality.code.description                | NO       | Deskripsi tentang proses pemeriksaan kualitas data                                                                                                                                                                                                                                                                                                                                                                                                   |
| metadata.quality.code.dimension                  | NO       | Prinsip kualitas data [*Completeness, Validity, Uniqueness, Accuracy, Timeliness, Consistency*]                                                                                                                                                                                                                                                                                                                                                      |
| metadata.quality.code.impact                     | NO       | Dampak dari proses atau kegiatan pemeriksaan kualitas data akan [Operational, Analytical]                                                                                                                                                                                                                                                                                                                                                            |
| metadata.quality.code.custom_properties.property | NO       | Nama properti khusus yang dibuat untuk mendukung "_rules_" pemeriksaan kualitas data                                                                                                                                                                                                                                                                                                                                                                 |
| metadata.quality.code.custom_properties.value    | NO       | Nilai dari properti khusus                                                                                                                                                                                                                                                                                                                                                                                                                           |
| metadata.sla.availability_start                  | YES      | Menunjukkan waktu ketersediaan pipa data yang bergantung kepada nilai unit: 'd' menunjukkan hari dalam sebulan, sedangkan 'h' menunjukkan waktu dalam hari.                                                                                                                                                                                                                                                                                          |
| metadata.sla.availability_end                    | YES      | Menunjukkan waktu kapan pipa data tidak tersedia yang bergantung kepada nilai unit: 'd' menunjukkan hari dalam sebulan, sedangkan 'h' menunjukkan waktu dalam hari.                                                                                                                                                                                                                                                                                  |
| metadata.sla.availability_unit                   | YES      | Unit ini bisa 'h' -> jam atau 'd' -> hari                                                                                                                                                                                                                                                                                                                                                                                                            |
| metadata.sla.frequency                           | YES      | Frekuensi menjalankan pipeline data (berdasarkan skenario proses batching). Untuk skenario proses stream, Anda dapat mengisi bidang ini dengan 0                                                                                                                                                                                                                                                                                                     |
| metadata.sla.frequency_unit                      | YES      | Unit ini bisa berupa 'm' -> menit, 'h' -> jam atau 'd' -> hari                                                                                                                                                                                                                                                                                                                                                                                       |
| metadata.sla.frequency_cron                      | NO       | Anda dapat mengisi kolom ini dengan perintah cron. Untuk informasi lebih lanjut -> [crontab.guru](!https://crontab.guru/)                                                                                                                                                                                                                                                                                                                            |
| metadata.sla.retention                           | YES      | Periode retensi data                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| metadata.sla.retention_unit                      | YES      | Unit periode retensi data                                                                                                                                                                                                                                                                                                                                                                                                                            |
| metadata.sla.effective_date                      | YES      | Waktu efektif _Data Contract_ dapat digunakan                                                                                                                                                                                                                                                                                                                                                                                                        |
| metadata.sla.end_of_contract                     | YES      | Waktu ketika _Data Contract_ telah berakhir                                                                                                                                                                                                                                                                                                                                                                                                          |
| metadata.prev_contract                           | NO       | contract_number sebelumnya, kolom ini dapat mengidentifikasi bahwa Data Contract ini merupakan versi update dari contract sebelumnya                                                                                                                                                                                                                                                                                                                 |
| metadata.contract_reference                      | NO       | Referensi contract, kolom ini dapat berupa sebuah no tiket permintaan data atau yang semisal                                                                                                                                                                                                                                                                                                                                                         |
| metadata.contract_reference.number               | NO       | Nomor referensi contract, kolom ini dapat berupa sebuah no tiket permintaan data atau yang semisal                                                                                                                                                                                                                                                                                                                                                   |
| metadata.contract_reference.type                 | NO       | Tipe referensi, contoh "layanan data", "surat permohonan data" atau semisal                                                                                                                                                                                                                                                                                                                                                                          |

#### Contoh _Metadata Section_

```
metadata:
  version: 1.0.1
  type: CSV
  name: customer list
  owner: marketing division
  consumption_mode: Analytical # [Analytical, Transactional]
  description:
    purpose: This dataset will be used to combine with others dataset for specific use case. # purpose of this dataset.
    usage: private # explains the use of datasets for certain purposes [private, public]
  consumer:
    - name: data analyst
      use_case: combine the dataset to transactional data, the results are obtained to find out a person's purchasing history.
    - name: analytic engineer
      use_case: enrich the customer datasets.
  stakeholders:
    - name: John Doe
      email: john.doe@mail.me
      role: owner # [owner, producer, consumer, reviewer]
      date_in: 2023-08-13T16:07:54+07:00
      date_out: null
    - name: Jean Doe
      email: jean.doe@mail.me
      role: consumer # [owner, producer, consumer, reviewer]
      date_in: 2023-08-13T16:07:54+07:00
      date_out: 2023-09-16T16:07:54+07:00
    - name: Fulanah
      email: fulanah@mail.me
      role: consumer # [owner, producer, consumer, reviewer]
      date_in: 2023-09-16T16:07:54+07:00
      date_out: null
  quality:
    - code: count_check
      description: ensure the dataset is in accordance with the agreed volume range
      dimension: completeness
      impact: operational
      custom_properties:
        - property: field_condition
          value: is_nullable=false
        - property: field_condition
          value: is_audit=true
    - code: distinct_check
      description: ensure there is no duplicate data
      dimension: completeness
      impact: operational
      custom_properties:
        - property: field_name
          value: uid
        - property: field_name
          value: name
        - property: field_name
          value: join_date
    - code: pii_check
      description: ensure PII was masking
      dimension: completeness
      impact: operational
      custom_properties:
        - property: field_name
          value: name
  sla:
    availability_start: 6
    availability_end: 18
    availability_unit: h
    frequency: 4
    frequency_unit: h
    frequency_cron: 0 0/6 * * *
    retention: 1
    retention_unit: y
    effective_date: 2023-08-13T16:07:54+07:00
    end_of_contract: 2025-08-13T16:07:54+07:00
  prev_contract: 4oxinOpVbBefG
  contract_reference:
    - number: 240785ED2D134204
      type: Layanan Data
    - number: TM.03.01/C.ll/3322/2024
      type: Surat Permohonan Data
```

### Model Section

Bagian ini menunjukkan _"schema"_ atau model data dari dataset, bagian ini akan berisi informasi-informasi berikut :

- nama kolom/field
- tipe kolom/field
- deskripsi kolom/field
- dan informasi tambahan lainnya

| Field                                    | Required | Definitions                                                                                          |
| ---------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------- |
| model.column                             | YES      | Menunjukkan nama kolom                                                                               |
| model.business_name                      | NO       | Menunjukkan nama kolom dalam perspektif bisnis                                                       |
| model.logical_type                       | YES      | Tipe data [cth. "string"]                                                                            |
| model.physical_type                      | YES      | Tipe data secara fisik [cth. varchar(25)]                                                            |
| model.is_primary                         | YES      | Menunjukkan apakah data merupakan kunci kolom utama atau tidak [true, false]                         |
| model.is_nullable                        | YES      | Menunjukkan apakah data dapat bernilai null atau tidak [true, false]                                 |
| model.is_partition                       | YES      | Menunjukkan apakah data dipartisi atau tidak [true, false]                                           |
| model.is_clustered                       | YES      | Menunjukkan apakah data dikelompokkan atau tidak [true, false]                                       |
| model.is_pii                             | YES      | Menunjukkan apakah data merupakan PII (Personally Identifiable Information) atau tidak [true, false] |
| model.is_audit                           | YES      | Menunjukkan apakah data dapat digunakan untuk audit atau tidak [true, false]                         |
| model.is_mandatory                       | YES      | Menunjukkan apakah data wajib diisi atau tidak [true, false]                                         |
| model.description                        | YES      | Merepresentasikan tujuan, makna, atau informasi lain tentang kolom, dapat berupa catatan sederhana   |
| model.quality.code                       | NO       | Menunjukkan nama kode untuk proses pemeriksaan kualitas data                                         |
| model.quality.description                | NO       | Deskripsi untuk proses pemeriksaan kualitas data                                                     |
| model.quality.dimension                  | NO       | Menunjukkan Dimensi Kualitas Data [Kelengkapan, Validitas, Akurasi, dll.]                            |
| model.quality.impact                     | NO       | Menunjukkan dampak jika proses pemeriksaan kualitas data dilakukan atau tidak                        |
| model.quality.custom_properties.property | NO       | Properti tambahan yang diperlukan untuk eksekusi aturan                                              |
| model.quality.custom_properties.value    | NO       | Nilai untuk properti tambahan                                                                        |
| model.sample_value                       | NO       | Contoh dataset                                                                                       |
| model.tags                               | NO       | Tag                                                                                                  |

#### Contoh _Model Section_

```
model:
  - column: uid
    business_name: User ID
    logical_type: string
    physical_type: varchar(36)
    is_primary: true
    is_nullable: false
    is_partition: true
    is_clustered: false
    is_pii: true
    is_audit: false
    is_mandatory: true
    description: User identifier column, this column is required and must be unique value
    quality:
      - code: null_check
        description: ensure that the column rows are complete according to the expected number of rows
        dimension: completeness
        impact: operational
        custom_properties:
          - property: compare_to
            value: total dataset row
          - property: comparison_type
            value: equal to
      - code: format_check
        description: ensure the value does not exceed the agreed nomenclature limits
        dimension: validity
        impact: operational
        custom_properties:
          - property: length
            value: 36
    sample_value:
      - 4d60b9fe-3311-4edb-986a-5f93c79c61ac
      - 386acf0e-5ed2-48d4-99b5-af5683207bd2
    tags:
      - tag1
      - tag2
```

### Ports Section

Bagian ini menunjukkan bagian _"ports"_ dari Data Contract, seperti yang anda ketahui bahwa _"ports"_ pada Data Contract dapat merepresentasikan sebuah "Data Access Points", Kanal Komunikasi (_Channel Communications_) atau dapat pula berisi informasi detil konfigurasi untuk dapat mengkonsumsi dataset tersebut.

| Field                     | Required | Definitions                                                  |
| ------------------------- | -------- | ------------------------------------------------------------ |
| ports.object              | YES      | Menunjukkan tipe dari kanal(_channel_) [source, destination] |
| ports.properties.property | YES      | Menunjukkan _property_ dari _object_                         |
| ports.properties.value    | YES      | Menunjukkan nilai dari _property_                            |

#### Contoh _Ports Section_

```
ports:
  - object: source
    properties:
      - property: type
        value: s3
      - property: location
        value: s3://path/to/object
  - object: destination
    properties:
      - property: type
        value: bigquery
      - property: project
        value: project_name
      - property: dataset
        value: dataset_name
```

### Examples Section

Bagian ini berisi contoh-contoh (dalam bentuk fisik) yang dapat mewakili bentuk fisik dari data-data yang terdapat didalam dataset.

| Field         | Required | Definitions                                            |
| ------------- | -------- | ------------------------------------------------------ |
| examples.type | NO       | Menunjukkan tipe dari _examples_                       |
| examples.data | NO       | Berisi contoh dataset, dapat berupa data-data _dummy_. |

#### Contoh _Examples Section_

```
examples:
  type: csv
  data: |-
    uid;name;join_date;updated_at;updated_by;created_at;created_by;deleted_at;deleted_by
    4d60b9fe-3311-4edb-986a-5f93c79c61ac;Hani Perkasa;2022-01-08;2023-08-13T16:07:54+07:00;admin;2023-08-13T16:07:54+07:00;admin;;
    386acf0e-5ed2-48d4-99b5-af5683207bd2;H4ni Nurchairil;2020-03-17;2023-08-13T16:07:54+07:00;;2023-08-13T16:07:54+07:00;admin;2023-08-14T16:07:54+07:00;admin
    ecc4992b-10fc-4621-9378-999a78a00804;Fulanah;;2021-08-13T16:07:54+07:00;admin;2023-08-13T16:07:54+07:00;admin;;
```
