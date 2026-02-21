# Sweater ERP

### Meek Sweater & Fashions Ltd.

A custom ERPNext application built for **sweater manufacturing
factories**, covering merchandising, sampling, production workflows, and
factory-specific ERP customizations.

Built on **ERPNext v15 / Frappe v15**.

------------------------------------------------------------------------

## 📌 System Requirements

-   Ubuntu 20.04 / 22.04 (Recommended)
-   Python 3.10+
-   Node.js 18+
-   Yarn
-   Redis
-   MariaDB / MySQL
-   Frappe Bench (Latest)

------------------------------------------------------------------------

## 🚀 ERPNext v15 Installation Guide

### 1️⃣ Initialize Frappe Bench

``` bash
bench init --frappe-branch version-15 frappe-bench
```

Bench directory path:

``` text
/home/[frappe-user]/frappe-bench
```

------------------------------------------------------------------------

### 2️⃣ Go to Frappe Bench Directory

``` bash
cd frappe-bench
```

------------------------------------------------------------------------

### 3️⃣ Fix User Directory Permissions

``` bash
chmod -R o+rx /home/[frappe-user]/
```

------------------------------------------------------------------------

### 4️⃣ Create a New Site

``` bash
bench new-site site1.local
```

------------------------------------------------------------------------

## 📦 Download Required Apps

### Payments App (Required)

``` bash
bench get-app payments
```

### ERPNext v15

``` bash
bench get-app --branch version-15 erpnext
```

### HRMS App (Optional)

``` bash
bench get-app hrms
```

Verify:

``` bash
bench version --format table
```

------------------------------------------------------------------------

## ⚙️ Install Apps

``` bash
bench --site site1.local install-app erpnext
bench --site site1.local install-app hrms
```

------------------------------------------------------------------------

## ⚙️ Install Specific Version Apps

``` bash
bench switch-to-branch version-15 frappe
bench switch-to-branch version-15 erpnext
bench switch-to-branch version-15 hrms
```

------------------------------------------------------------------------


## 🔄 Restore Existing Database (Optional)

``` bash
bench --site newsite.com restore \
sites/newsite.com/private/backups/your-database.sql.gz \
--force
```

Then:

``` bash
bench --site newsite.com migrate
bench restart
```

------------------------------------------------------------------------

## 🧵 Sweater App Installation

``` bash
bench get-app $URL_OF_THIS_REPO --branch develop
bench --site site1.local install-app sweater
```

------------------------------------------------------------------------

## 🧪 Development & Contribution

### Pre-commit

``` bash
cd apps/sweater
pre-commit install
```

Tools used: - ruff - eslint - prettier - pyupgrade

------------------------------------------------------------------------

## 🤖 CI

GitHub Actions: - CI (tests on develop) - Linters (Semgrep, pip-audit)

------------------------------------------------------------------------

## 📜 License

MIT License
