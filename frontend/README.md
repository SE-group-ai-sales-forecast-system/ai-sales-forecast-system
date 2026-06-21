# Frontend module

This folder contains the Streamlit frontend application for the AI sales forecast system.

## Structure

```text
frontend/
├─ app.py                         # Streamlit main application
├─ pages/                         # Reserved page modules
│  └─ README.md
└─ assets/                        # Static resources and test evidence
   ├─ README.md
   └─ screenshots/                # Functional test screenshots
      ├─ TC01_api_docs_overview.png
      ├─ TC02_login_success.png
      ├─ TC03_lightgbm_prediction.png
      ├─ TC04_baseline_prediction.png
      ├─ TC05_sales_analysis_page.png
      ├─ TC06_inventory_warning_page.png
      ├─ TC07_inventory_shortage_highlight.png
      ├─ TC08_refresh_warning_data.png
      ├─ TC09_unauthenticated_prediction.png
      └─ TC10_backend_disconnected_error.png
```

## Run

Start the backend first, then run:

```bash
streamlit run frontend/app.py
```
