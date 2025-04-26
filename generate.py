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

def generate_report(analysis_results, tickers):
    """
    Génère le rapport en fonction du nombre de tickers sélectionnés.
    
    Parameters:
    -----------
    analysis_results : dict
        Résultats de l'analyse
    tickers : list
        Liste des tickers analysés
    """
    # Chargement des fichiers nécessaires
    df_ratios = load_csv_file('output/rapport_ratios.csv')
    data = pd.read_csv('output/rendements_cryptos.csv', index_col='Date', parse_dates=True)
    
    # Adaptation des graphiques au nombre de tickers
    if len(tickers) > 1:
        monthly_returns_all_cryptos = load_csv_file('output/monthly_returns_all_cryptos.csv')
        annual_returns_transposed = load_csv_file('output/annual_returns_transposed.csv')
        
        # Génération des heatmaps seulement si plus d'un ticker
        img_annual_heatmap = generate_heatmap(
            annual_returns_transposed.set_index("Crypto"),
            "Annual Returns (%)"
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
    else:
        img_annual_heatmap_base64 = ""
        monthly_heatmaps_json = ""

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
    normalized_prices = pd.DataFrame()
    cryptos_tickers = [f"{c}-USD" for c in tickers]  # Ajout du suffixe -USD
    for ticker in cryptos_tickers:
        close_column = f"Close_{ticker}"
        if close_column in data.columns:
            normalized_prices[ticker] = (data[close_column] / data[close_column].iloc[0] - 1) * 100

    # Images
    img_performance_base64 = image_to_base64('output/performance_relative_et_prix.png')
    img_corr_mobile_base64 = image_to_base64('output/correlations_rolling_windows.png')
    img_corr_base64 = image_to_base64('output/matrice_correlation.png')
    # Images de volatilité
    img_vol_hist = image_to_base64('output/volatilite_historique.png')
    img_vol_mobile = image_to_base64('output/volatilite_mobile.png')
    
    # Chargement des données de volatilité
    vol_table = pd.read_csv('output/volatilite_table.csv', index_col=0)
    vol_table_html = vol_table.to_html(
        classes='volatility-table',
        float_format=lambda x: '{:.2f}%'.format(x)
    )

    # Créer une copie du DataFrame avec un index commençant à 1
    df_ratios = df_ratios.copy()
    df_ratios.index = range(1, len(df_ratios) + 1)

    df_ratios_html = df_ratios.to_html(
        classes='ratios-table', 
        float_format=lambda x: '{:.2f}'.format(x) if pd.notnull(x) else '', 
        index=True
    )

    # Adaptation du template HTML en fonction du nombre de tickers
    correlation_section = ""
    if len(tickers) > 1:
        correlation_section = f"""
            <h2>Correlation Analysis</h2>
            <p>Here is the correlation matrix and rolling correlations between the selected cryptocurrencies:</p>
            <img src="data:image/png;base64,{img_corr_base64}" alt="Correlation Heatmap">
            <img src="data:image/png;base64,{img_corr_mobile_base64}" alt="Rolling Correlation">
        """

    html_report = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Cryptocurrency Analysis Report</title>
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
                max-width: 95%;
                height: auto;
                margin: 20px auto;
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
            .ratios-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                background-color: #1e1e1e;
                border-radius: 8px;
                overflow: hidden;
            }}
            .ratios-table th {{
                background-color: #2a2a2a;
                color: #1fa2ff;
                padding: 12px 15px;
                text-align: center;
                border: 1px solid #2e2e2e;
                font-weight: bold;
            }}
            .ratios-table th:first-child,
            .ratios-table td:first-child {{
                min-width: initial;
                white-space: initial;
                padding-right: 15px;
            }}
            .ratios-table th:nth-child(2),
            .ratios-table td:nth-child(2) {{
                min-width: 140px;
                white-space: nowrap;
                padding-right: 20px;
            }}
            .ratios-table td {{
                padding: 12px 15px;
                text-align: right;
                border: 1px solid #2e2e2e;
                color: #f1f1f1;
            }}            
            .ratios-table tr:hover {{
                background-color: #2a2a2a;
            }}            
            .ratios-section {{
                margin: 40px 0;
                padding: 20px;
                background-color: #1e1e1e;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .volatility-table-container {{
                margin-top: 20px;
                padding: 15px;
                background-color: #1e1e1e;
                border-radius: 8px;
            }}
            .volatility-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 10px 0;
            }}
            .volatility-table th {{
                background-color: #2a2a2a;
                color: #1fa2ff;
                padding: 12px;
                text-align: left;
            }}
            .volatility-table td {{
                padding: 10px;
                border-bottom: 1px solid #2e2e2e;
            }}
            
            /* Style pour les graphiques de prix individuels */
            .price-charts {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }}
            
            .price-chart {{
                background-color: #1e1e1e;
                padding: 15px;
                border-radius: 8px;
            }}
            
            /* Ajustement pour les tableaux avec plus de données */
            .table-container {{
                overflow-x: auto;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Cryptocurrency Analysis Report</h1>
            
            <h2 style="color: #1fa2ff;">Risk-Free Rate</h2>
            <ul style="list-style-type: none; padding-left: 0;">
              <li><strong>Annual risk-free rate:</strong> {risk_data['annual_rate'] * 100:.2f}%</li>
              <li><strong>Daily risk-free rate:</strong> {risk_data['daily_rate'] * 100:.4f}%</li>
            </ul>

            <h2>Performance and Risk Ratios</h2>
            <div class="ratios-section">
                <p>This table presents the main performance and risk indicators for each cryptocurrency:</p>
                {df_ratios_html}
            </div>

            <h2>Annual Returns</h2>
            <p>Here is a heatmap showing the annual returns (%) of different cryptocurrencies:</p>
            <img src="data:image/png;base64,{img_annual_heatmap_base64}" alt="Annual Returns Heatmap">

            <h2>Monthly Returns</h2>
            <p>Heatmap of monthly returns (%) by year:</p>
            <img id="monthlyHeatmap" src="" alt="Monthly Returns Heatmap">
            <div class="nav-buttons">
                <button onclick="prevYear()">⬅️ Previous Year</button>
                <button onclick="nextYear()">Next Year ➡️</button>
            </div>

            <h2>Relative Performance of Cryptocurrencies</h2>
            <p>Here is the relative performance chart of cryptocurrencies over the analysis period:</p>
            <img src="data:image/png;base64,{img_performance_base64}" alt="Relative Performance">

            {correlation_section}

            <h2>Volatility Analysis</h2>
            <div class="volatility-section">
                <p>This section presents the volatility analysis of cryptocurrencies using two complementary approaches.</p>
                
                <div class="volatility-card">
                    <h3>Historical Volatility</h3>
                    <p>Comparison of annualized historical volatility between different cryptocurrencies.</p>
                    <img src="data:image/png;base64,{img_vol_hist}" alt="Historical Volatility">
                </div>

                <div class="volatility-card">
                    <h3>Rolling Volatility</h3>
                    <p>Evolution of volatility over a 30-day rolling window.</p>
                    <img src="data:image/png;base64,{img_vol_mobile}" alt="Rolling Volatility">
                </div>
            </div>
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
   