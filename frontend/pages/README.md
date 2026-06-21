# Frontend pages

This directory is reserved for page-level Streamlit modules.

In the current demo version, the page rendering functions are kept in `frontend/app.py` to keep the project stable and easy to run. The implemented pages include:

- Home dashboard
- Sales forecast
- Sales analysis
- Inventory warning
- System description

If the project is expanded later, the functions in `app.py` can be split into independent files in this directory, such as `home_page.py`, `forecast_page.py`, `analysis_page.py`, and `inventory_page.py`.
