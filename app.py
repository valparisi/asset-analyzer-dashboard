from flask import Flask, request, render_template_string
from extraction import extract_data
from analyze import run_analysis
from generate import generate_report
from datetime import date

app = Flask(__name__)

@app.route('/')
def home():
    # Définir une date de début par défaut (par exemple, 1er janvier 2023)
    default_start_date = "2022-01-01"
    # Définir une date de fin par défaut (par exemple, aujourd'hui)
    default_end_date = date.today().strftime("%Y-%m-%d")
    
    # Liste étendue des tickers disponibles
    available_tickers = [
        {"value": "BTC", "text": "Bitcoin (BTC)"},
        {"value": "ETH", "text": "Ethereum (ETH)"},
        {"value": "BNB", "text": "Binance Coin (BNB)"},
        {"value": "SOL", "text": "Solana (SOL)"},
        {"value": "ADA", "text": "Cardano (ADA)"},
        {"value": "XRP", "text": "Ripple (XRP)"},
        {"value": "DOT", "text": "Polkadot (DOT)"},
        {"value": "DOGE", "text": "Dogecoin (DOGE)"},
        {"value": "AVAX", "text": "Avalanche (AVAX)"},
        {"value": "MATIC", "text": "Polygon (MATIC)"},
        {"value": "LINK", "text": "Chainlink (LINK)"},
        {"value": "UNI", "text": "Uniswap (UNI)"}
    ]
    
    template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Crypto Report</title>

        <!-- Fonts & Icons -->
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/select2@4.0.13/dist/css/select2.min.css" rel="stylesheet" />

        <style>
            :root {
                --bg-dark: #0f111a;
                --bg-light: #f4f6fa;
                --text-dark: #f8f9fa;
                --text-light: #121212;
                --primary: #00b4fc;
                --input-dark: #1f2233;
                --input-light: #eaeaea;
                --card-dark: rgba(255, 255, 255, 0.05);
                --card-light: #ffffff;
            }

            body {
                font-family: 'Inter', sans-serif;
                background-color: var(--bg-dark);
                color: var(--text-dark);
                transition: background-color 0.3s, color 0.3s;
            }

            body.light-mode {
                background-color: var(--bg-light);
                color: var(--text-light);
            }

            .container {
                max-width: 600px;
                margin: 60px auto;
                background: var(--card-dark);
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }

            body.light-mode .container {
                background: var(--card-light);
            }

            h1 {
                text-align: center;
                margin-bottom: 30px;
            }

            .form-label {
                font-weight: 600;
                margin-bottom: 0.5rem;
                display: block;
            }

            .form-control, .select2-container--default .select2-selection--multiple {
                border: none;
                border-radius: 10px;
                padding: 10px;
                background-color: var(--input-dark);
                color: var(--text-dark);
                width: 100% !important;
                box-sizing: border-box;
            }

            body.light-mode .form-control,
            body.light-mode .select2-container--default .select2-selection--multiple {
                background-color: var(--input-light);
                color: var(--text-light);
            }

            .btn {
                background-color: var(--primary);
                color: white;
                border: none;
                padding: 12px;
                width: 100%;
                border-radius: 10px;
                font-weight: 600;
                font-size: 16px;
                cursor: pointer;
                margin-top: 15px;
            }

            .btn:hover {
                background-color: #009cd6;
            }

            .select2-selection__choice {
                background-color: var(--primary) !important;
                color: white !important;
                border: none !important;
                padding: 5px 10px !important;
                border-radius: 15px !important;
                font-size: 13px;
            }

            /* Style dropdown list in dark mode */
            .select2-container--default .select2-results > .select2-results__options {
                background-color: var(--input-dark);
                color: var(--text-dark);
            }

            body.light-mode .select2-container--default .select2-results > .select2-results__options {
                background-color: var(--input-light);
                color: var(--text-light);
            }

            .select2-container--default .select2-results__option--highlighted[aria-selected] {
                background-color: var(--primary);
                color: white;
            }

            .mode-toggle {
                position: fixed;
                top: 20px;
                right: 25px;
                background: none;
                border: none;
                font-size: 1.8rem;
                color: var(--primary);
                cursor: pointer;
                z-index: 999;
            }
        </style>
    </head>
    <body class="dark-mode">
        <button class="mode-toggle" id="toggle-mode-btn" title="Change theme">
            <i class="bi bi-moon-stars-fill" id="toggle-icon"></i>
        </button>

        <div class="container">
            <h1>📈 Crypto Report</h1>
            <form action="/generate" method="post">
                <div class="form-group">
                    <label class="form-label" for="tickers">Choose your tickers (1 to 8):</label>
                    <select name="tickers[]" id="tickers" multiple="multiple" class="form-control">
                        {% for ticker in available_tickers %}
                        <option value="{{ ticker.value }}">{{ ticker.text }}</option>
                        {% endfor %}
                    </select>
                </div>

                <div class="form-group">
                    <label class="form-label" for="start_date">Start date:</label>
                    <input type="date" name="start_date" id="start_date" class="form-control" required value="{{default_start_date}}">
                </div>
                <div class="form-group">
                    <label class="form-label" for="end_date">End date:</label>
                    <input type="date" name="end_date" id="end_date" class="form-control" required value="{{default_end_date}}">
                </div>

                <button type="submit" class="btn">Generate Report</button>
            </form>
        </div>

        <!-- Scripts -->
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/select2@4.0.13/dist/css/select2.min.css"></script>
        <script src="https://cdn.jsdelivr.net/npm/select2@4.0.13/dist/js/select2.min.js"></script>
        <script>
            $(document).ready(function() {
                $('#tickers').select2({
                    placeholder: "Select 1 to 8 tickers",
                    width: '100%',
                    tags: false,
                    maximumSelectionLength: 8
                });
            });

            const toggleBtn = document.getElementById('toggle-mode-btn');
            const icon = document.getElementById('toggle-icon');

            toggleBtn.addEventListener('click', () => {
                document.body.classList.toggle('light-mode');
                if (document.body.classList.contains('light-mode')) {
                    icon.classList.remove('bi-moon-stars-fill');
                    icon.classList.add('bi-sun-fill');
                } else {
                    icon.classList.remove('bi-sun-fill');
                    icon.classList.add('bi-moon-stars-fill');
                }
            });
        </script>
    </body>
    </html>
    '''
    
    return render_template_string(template, 
                                default_start_date=default_start_date, 
                                default_end_date=default_end_date,
                                available_tickers=available_tickers)





@app.route('/generate', methods=['POST'])
def generate():
    # Récupération des tickers, date de début et de fin depuis le formulaire
    tickers = request.form.getlist('tickers[]')  # récupère la liste exacte sélectionnée
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    # 1. Extraction des données selon les tickers
    df = extract_data(tickers, start_date, end_date)

    # 2. Analyse des données extraites
    # On passe maintenant les tickers et les dates à run_analysis
    analysis_results = run_analysis(tickers, start_date, end_date)  # passer ces valeurs dans la fonction

    # 3. Génération du rapport personnalisé
    # Supposons que `analysis_results` contienne les informations nécessaires pour générer le rapport
    html_report = generate_report(analysis_results, tickers=tickers)

    return render_template_string(html_report)


if __name__ == "__main__":
    app.run(debug=True)