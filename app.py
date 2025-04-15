from flask import Flask, request, render_template_string
from extraction import extract_data
from analyze import run_analysis
from generate import generate_report

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <h1>Rapport Crypto Interactif</h1>
    <form action="/generate" method="post">
        <label>Tickers (séparés par des virgules):</label><br>
        <input type="text" name="tickers" value="BTC,ETH,BNB,SOL"><br><br>
        <label>Date début (YYYY-MM-DD):</label><br>
        <input type="text" name="start_date" value="2022-01-01"><br><br>
        <label>Date fin (YYYY-MM-DD):</label><br>
        <input type="text" name="end_date" value="2024-12-31"><br><br>
        <input type="submit" value="Générer le rapport">
    </form>
    '''

@app.route('/generate', methods=['POST'])
def generate():
    tickers = request.form['tickers'].replace(" ", "").split(',')
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    # 1. Extraire les données via extraction.py
    df = extract_data(tickers, start_date, end_date)

    # 2. Lancer l'analyse (run_analysis lit le CSV généré par extract_data)
    analysis_results = run_analysis()

    # 3. Générer le rapport HTML complet via generate_report.py
    html_report = generate_report(analysis_results)

    return render_template_string(html_report)

if __name__ == "__main__":
    app.run(debug=True)