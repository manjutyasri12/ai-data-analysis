# Installation Steps

1. Open a terminal in `ai_data_project`.
2. Create or activate the virtual environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```
4. Apply database migrations:
   ```powershell
   python manage.py migrate
   ```
5. Start the server:
   ```powershell
   python manage.py runserver
   ```
6. Open `http://127.0.0.1:8000/`.

The platform supports CSV upload, preprocessing, statistics, Plotly visualizations, AutoML training, model downloads, and predictions from manual inputs or uploaded test CSV files.
