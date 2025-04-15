import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import os
import json
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from io import BytesIO

# === Fonctions utilitaires ===

def plot_to_image(fig):
    img = BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    return img

def load_csv_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Le fichier {file_path} est introuvable.")
    return pd.read_csv(file_path)

def image_to_base64(img_path):
    if not os.path.exists(img_path):
        raise FileNotFoundError(f"Le fichier {img_path} est introuvable.")
    with open(img_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def generate_heatmap(df, title, figsize=(12, 6), cmap="RdYlGn", annot=True, vmin=-50, vmax=50):
    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(
        df, annot=annot, fmt=".2f", cmap=cmap,
        center=0, vmin=vmin, vmax=vmax,
        linewidths=0.5, cbar=True, ax=ax,
        cbar_kws={'ticks': [-50, -25, 0, 25, 50]}
    )
    if annot:
        for text in ax.texts:
            text.set_text(f"{text.get_text()}%")
    ax.set_title(title, fontsize=14)
    plt.xticks(rotation=45)
    plt.yticks(rotation=0)
    plt.tight_layout()
    return plot_to_image(fig)

# === Fonction principale ===

def generate_report(analysis_results):
    # Chargement des fichiers nécessaires
    correlation_matrix = load_csv_file('output/matrice_correlation.csv')
    df_ratios = load_csv_file('output/rapport_ratios.csv')
    data = pd.read_csv('output/rendements_cryptos.csv', index_col='Date', parse_dates=True)
    monthly_returns_all_cryptos = load_csv_file('output/monthly_returns_all_cryptos.csv')
    annual_returns_transposed = load_csv_file('output/annual_returns_transposed.csv')

    # Heatmap rendements annuels
    img_annual_heatmap = generate_heatmap(
        annual_returns_transposed.set_index("Crypto"),
        "Rendements Annuels (%)"
    )
    img_annual_heatmap_base64 = base64.b64encode(img_annual_heatmap.read()).decode('utf-8')

    # Heatmaps mensuelles
    monthly_returns_all_cryptos.set_index("Crypto", inplace=True)
    monthly_returns_by_year = {}
    for col in monthly_returns_all_cryptos.columns:
        parts = col.split(" ")
        if len(parts) >= 2:
            year = parts[1]
            monthly_returns_by_year.setdefault(year, []).append(col)
        else:
            monthly_returns_by_year.setdefault("Inconnu", []).append(col)

    monthly_heatmaps_base64 = {}
    for year, columns in monthly_returns_by_year.items():
        df_year = monthly_returns_all_cryptos[columns]
        img = generate_heatmap(
            df_year,
            f"Rendements Mensuels (%) - {year}"
        )
        monthly_heatmaps_base64[year] = base64.b64encode(img.read()).decode('utf-8')
    monthly_heatmaps_json = json.dumps(monthly_heatmaps_base64)

    # Taux sans risque
    with open("output/risk_free.json") as f:
        risk_data = json.load(f)
    risk_free_html = f"""
    <h2 style="color: #1fa2ff;">Taux Sans Risque</h2>
    <ul style="list-style-type: none; padding-left: 0;">
      <li><strong>Taux sans risque annuel :</strong> {risk_data['annual_rate'] * 100:.2f}%</li>
      <li><strong>Taux sans risque journalier :</strong> {risk_data['daily_rate'] * 100:.4f}%</li>
    </ul>
    """

    # Performance relative
    cryptos_tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD']
    normalized_prices = pd.DataFrame()
    for ticker in cryptos_tickers:
        close_column = f'Close_{ticker}'
        normalized_prices[ticker] = (data[close_column] / data[close_column].iloc[0] - 1) * 100

    # Images
    img_performance_base64 = image_to_base64('output/performance_relative_et_prix.png')
    img_corr_mobile_base64 = image_to_base64('output/correlations_rolling_windows.png')
    img_corr_base64 = image_to_base64('output/matrice_correlation.png')

    df_ratios_html = df_ratios.to_html(index=False, border=0)

    html_report = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Rapport d'Analyse des Cryptomonnaies</title>
        <style>
            body {{
                font-family: 'Roboto', sans-serif;
                margin: 30px;
                background-color: #121212;
                color: #e0e0e0;
            }}
            h1 {{
                text-align: center;
                color: #ffffff;
                font-size: 28px;
            }}
            h2 {{
                color: #1fa2ff;
                font-size: 22px;
                margin-top: 40px;
                border-bottom: 2px solid #1fa2ff;
                padding-bottom: 5px;
            }}
            p {{
                font-size: 16px;
                line-height: 1.6;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                background-color: #1e1e1e;
                border-radius: 8px;
                overflow: hidden;
            }}
            th, td {{
                padding: 12px 15px;
                text-align: center;
                border: 1px solid #2e2e2e;
                font-size: 14px;
                color: #f1f1f1;
            }}
            th {{
                background-color: #2a2a2a;
                color: #1fa2ff;
            }}
            img {{
                display: block;
                margin: 30px auto 10px;
                border-radius: 8px;
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.6);
                max-width: 90%;
                height: auto;
                background-color: #1e1e1e;
                padding: 10px;
            }}
            ul {{
                font-size: 16px;
            }}
            ul li {{
                margin: 8px 0;
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
            }}
            .nav-buttons {{
                text-align: center;
                margin: 20px 0;
            }}
            .nav-buttons button {{
                padding: 10px 20px;
                margin: 0 10px;
                font-size: 16px;
                border: none;
                background: linear-gradient(135deg, #1fa2ff, #12d8fa);
                color: #000;
                border-radius: 6px;
                cursor: pointer;
                font-weight: bold;
                transition: background 0.3s ease;
            }}
            .nav-buttons button:hover {{
                background: linear-gradient(135deg, #0d8ddb, #0bc6e3);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Rapport d'Analyse des Cryptomonnaies</h1>
            
            {risk_free_html}

            <h2>Rendements Annuels</h2>
            <p>Voici une heatmap illustrant les rendements annuels (en %) des différentes cryptomonnaies :</p>
            <img src="data:image/png;base64,{img_annual_heatmap_base64}" alt="Heatmap Rendements Annuels">

            <h2>Rendements Mensuels</h2>
            <p>Heatmap des rendements mensuels (en %) des cryptos, année par année :</p>
            <img id="monthlyHeatmap" src="" alt="Heatmap Rendements Mensuels">
            <div class="nav-buttons">
                <button onclick="prevYear()">⬅️ Année précédente</button>
                <button onclick="nextYear()">Année suivante ➡️</button>
            </div>

            <h2>Performance Relative des Cryptomonnaies</h2>
            <p>Voici le graphique de la performance relative des cryptomonnaies sur la période d'analyse :</p>
            <img src="data:image/png;base64,{img_performance_base64}" alt="Performance Relative">

            <h2>Corrélation Mobile</h2>
            <p>Voici la matrice de corrélation mobile des rendements quotidiens pour les cryptomonnaies analysées :</p>
            <img src="data:image/png;base64,{img_corr_mobile_base64}" alt="Corrélation Mobile">

            <h2>Heatmap de la Corrélation</h2>
            <p>Voici une visualisation de la matrice de corrélation sous forme de heatmap :</p>
            <img src="data:image/png;base64,{img_corr_base64}" alt="Heatmap de la Corrélation">
        </div>

        <script>
            const heatmaps = {monthly_heatmaps_json};
            const years = Object.keys(heatmaps).sort();
            const currentYear = new Date().getFullYear().toString();
            let currentIndex = years.indexOf(currentYear);
            if (currentIndex === -1) {{
                currentIndex = 0;
            }}
            function updateHeatmap() {{
                const year = years[currentIndex];
                document.getElementById("monthlyHeatmap").src = "data:image/png;base64," + heatmaps[year];
            }}
            function nextYear() {{
                if (currentIndex < years.length - 1) {{
                    currentIndex++;
                    updateHeatmap();
                }}
            }}
            function prevYear() {{
                if (currentIndex > 0) {{
                    currentIndex--;
                    updateHeatmap();
                }}
            }}
            // Afficher la première heatmap au chargement
            updateHeatmap();
        </script>
    </body>
    </html>
    """
    return html_report

# === Test autonome ===
if __name__ == "__main__":
    from analyze import run_analysis
    analysis_results = run_analysis()
    report_html = generate_report(analysis_results)
    with open("rapport.html", "w", encoding="utf-8") as f:
        f.write(report_html)
    print("Rapport généré dans 'rapport.html'")