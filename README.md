# IS Buddies

## Run with XAMPP on Windows

1. Start **MySQL** from the XAMPP Control Panel.
2. Open a terminal in this project folder and install the Python packages:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Seed the regular product and supplier catalog:

   ```powershell
   python seed_db.py
   ```

   To also load clearly labeled fictional customers and historical sales for testing, run:

   ```powershell
   python seed_db.py --demo
   ```

   Demo records are added once and do not change product stock.
4. Start the Flask website:

   ```powershell
   python run.py
   ```

5. Visit <http://127.0.0.1:5000>.

Use the Flask command above rather than VS Code Live Server; Flask must render the
Jinja templates and connect to MySQL. The database is created automatically
using the settings in `config.py` (XAMPP's default MySQL user is `root` with an
empty password). Set `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, or `DB_NAME`
in the terminal environment if your XAMPP configuration differs.
