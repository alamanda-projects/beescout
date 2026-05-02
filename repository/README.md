# BeeScout - Data Contract Management System

## Overview

**BeeScout** adalah sebuah aplikasi _web-based_ yang berfungsi sebagai **Content Management System (CMS)** untuk mengelola **Data Contract** secara terpusat, sistematis, dan kolaboratif. Aplikasi ini membantu tim data, engineer, dan pemilik produk data (data product owner) untuk membuat, mengedit, meninjau, serta mempublikasikan kontrak data dengan lebih mudah dan terstruktur.

BeeScout dirancang untuk mendukung praktik **Data Mesh**, **Data Governance**, dan integrasi antar sistem berbasis kontrak (_contract-first approach_). 

## Key Features

- 🧾 **Create & Edit Data Contract**  
  Antarmuka grafis yang memudahkan pembuatan dan pengelolaan Data Contract, tanpa perlu menulis YAML/JSON secara manual.

- 🔍 **Versioning & Audit Trail**  
  Setiap perubahan kontrak terekam dan dapat ditelusuri, lengkap dengan metadata seperti waktu perubahan dan aktor.

- 👥 **Role-Based Access Control (RBAC)**  
  Hak akses dapat dikendalikan berdasarkan peran pengguna (admin, contributor, reviewer, dll).

- 📤 **Contract Publishing & API Access**  
  Kontrak dapat dipublikasikan secara eksplisit dan tersedia melalui REST API untuk diakses oleh pipeline, downstream systems, atau consumer data.

- 🛠️ **Integrasi CI/CD & Validation Tools**  
  Mendukung integrasi dengan tools seperti dbt, Great Expectations, Airflow, atau sistem ingestion lainnya.

- 🗳️ **Approval Workflow**  
  Mekanisme persetujuan untuk setiap perubahan kontrak yang diajukan oleh pengguna non-admin.

- 📚 **Rule Catalog**  
  Katalog terpusat untuk mendefinisikan aturan kualitas data standar organisasi.

## Screenshots

> 📸 Tangkapan layar akan ditambahkan pada rilis beta

## Use Case

- Menyediakan portal terpusat untuk dokumentasi dan penyebaran Data Contract.
- Menjamin konsistensi struktur dan kualitas kontrak data antar domain.
- Memberikan transparansi dan traceability dalam evolusi skema data.
- Mendukung pengelolaan lifecycle kontrak dari draft, review, sampai rilis.

## Tech Stack

- Backend: FastAPI
- Database: MongoDB
- Auth: JWT
- Deployment: Docker (Kubernetes-ready)

## Getting Started

1. Clone repositori ini:
    ```bash
    git clone https://github.com/alamanda-projects/beescout
    cd beescout
    ```

2. Jalankan aplikasi:
    ```bash
    make up
    ```

3. Akses aplikasi di http://app.localhost (atau port yang dikonfigurasi via Nginx)

## Dokumentasi Lebih Lengkap
Dokumentasi lengkap penggunaan dapat dilihat pada tautan berikut : [Dokumentasi Beescout](file/docs/readme.md)