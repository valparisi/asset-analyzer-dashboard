import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from fredapi import Fred
from itertools import combinations
import os
import json
from extraction import extract_data
from matplotlib.animation import FuncAnimation
import matplotlib
matplotlib.use('Agg') 


def run_analysis(cryptos_base, start_date, end_date):
    """
    Analyse les données pour une liste variable de cryptomonnaies.
    
    Parameters:
    -----------
    cryptos_base : list
        Liste des tickers (sans le suffixe -USD)
    start_date : str
        Date de début au format YYYY-MM-DD
    end_date : str
        Date de fin au format YYYY-MM-DD
    """
    if not 1 <= len(cryptos_base) <= 8:
        raise ValueError("Le nombre de tickers doit être entre 1 et 8")

    # Ajout du suffixe -USD aux tickers
    cryptos_tickers = [f"{c}-USD" for c in cryptos_base]
    
    # Extraction des données
    data = extract_data(cryptos_tickers, start_date, end_date)
    
    # Calcul des rendements quotidiens
    daily_returns = pd.DataFrame()
    for ticker in cryptos_tickers:
        col = f"Close_{ticker}"
        if col in data.columns:
            daily_returns[ticker] = data[col].pct_change()
    
    # Matrice de corrélation (seulement si plus d'un ticker)
    if len(cryptos_tickers) > 1:
        correlation_matrix = daily_returns.corr()
        correlation_matrix.to_csv("output/matrice_correlation.csv")
        
        # Corrélations mobiles (seulement si plus d'un ticker)
        crypto_pairs = list(combinations(cryptos_tickers, 2))
        rolling_correlations = pd.DataFrame(index=daily_returns.index)
        
        for crypto1, crypto2 in crypto_pairs:
            col_name = f"{crypto1}/{crypto2}"
            rolling_correlations[col_name] = (
                daily_returns[crypto1].rolling(window=30)
                .corr(daily_returns[crypto2])
            )
    
    print("Rendements quotidiens :")
    print(daily_returns.head())

    plt.figure(figsize=(8, 6))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt='.2f', linewidths=0.5)
    plt.title("Matrice de corrélation des rendements quotidiens")
    plt.savefig("output/matrice_correlation.png")
    plt.close()

    rolling_windows = [30, 90]

    fig, axes = plt.subplots(nrows=len(crypto_pairs), ncols=1, figsize=(14, 4 * len(crypto_pairs)), sharex=True)
    if len(crypto_pairs) == 1:
        axes = [axes]

    for idx, (c1, c2) in enumerate(crypto_pairs):
        ax = axes[idx]
        for window in rolling_windows:
            rolling_corr = daily_returns[c1].rolling(window).corr(daily_returns[c2])
            ax.plot(rolling_corr.index, rolling_corr, label=f"{window} jours")
        ax.set_title(f"Corrélation mobile : {c1} vs {c2}")
        ax.axhline(0, linestyle='--', color='black', linewidth=1)
        ax.set_ylabel("Corrélation")
        ax.legend()
        ax.grid(True)

    plt.xlabel("Date")
    plt.tight_layout()
    fig.savefig("output/correlations_rolling_windows.png")

    # Taux sans risque
    fred = Fred(api_key='8aa2c471919918432841991cb0453e92')
    risk_free_rate_annual_pct = fred.get_series('GS10').iloc[-1]
    risk_free_rate_annual = risk_free_rate_annual_pct / 100

    risk_free_rate_fix = 0.03
    risk_free_rate_daily_fix = risk_free_rate_fix / 252

    print("\nTaux sans risque annuel fixe :", risk_free_rate_fix)
    print("\nTaux sans risque journalier (fixe) :", risk_free_rate_daily_fix)

    risk_free_rate_daily = risk_free_rate_annual / 252
    print("\nTaux sans risque annuel :", risk_free_rate_annual)
    print("\nTaux sans risque journalier :", risk_free_rate_daily)

    risk_data = {
        "annual_rate": float(risk_free_rate_annual),
        "daily_rate": float(risk_free_rate_daily)
    }
    with open("output/risk_free.json", "w") as f:
        json.dump(risk_data, f)

    sharpe_ratios, sortino_ratios, calmar_ratios, total_returns = {}, {}, {}, {}
    confidence_level = 0.95
    var_values, cvar_values = {}, {}

    for ticker in cryptos_tickers:
        mean_daily = daily_returns[ticker].mean()
        std_daily = daily_returns[ticker].std()
        downside_std = daily_returns[ticker][daily_returns[ticker] < 0].std()

        close_column = f'Close_{ticker}'
        total_return = (data[close_column].iloc[-1] / data[close_column].iloc[0]) - 1
        total_returns[ticker] = total_return * 100

        sharpe_ratios[ticker] = ((mean_daily - risk_free_rate_daily) / std_daily * np.sqrt(252)) if std_daily != 0 else np.nan
        sortino_ratios[ticker] = ((mean_daily - risk_free_rate_daily) / downside_std * np.sqrt(252)) if downside_std != 0 else np.nan

        cumulative = (1 + daily_returns[ticker]).cumprod()
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak
        max_drawdown = drawdown.min()
        annual_return = (cumulative.iloc[-1] - 1) * 100
        calmar_ratios[ticker] = annual_return / abs(max_drawdown) if max_drawdown != 0 else np.nan

        sorted_returns = daily_returns[ticker].dropna().sort_values()
        var_index = int((1 - confidence_level) * len(sorted_returns))
        var_values[ticker] = sorted_returns.iloc[var_index]
        cvar_values[ticker] = sorted_returns.iloc[:var_index].mean()

    df_ratios = pd.DataFrame({
        'Rendement Total (%)': total_returns,
        'Sharpe Ratio': sharpe_ratios,
        'Sortino Ratio': sortino_ratios,
        'Calmar Ratio': calmar_ratios,
        'VaR (95%)': var_values,
        'CVaR (95%)': cvar_values
    })
    df_ratios.index.name = 'Pairs' 

    generate_volatility_charts(data, cryptos_base)

    df_ratios.to_csv("output/rapport_ratios.csv")
    print("\nTableau des rendements et ratios de risque :")
    print(df_ratios.round(2).to_string())

    monthly_returns = daily_returns.resample('ME').apply(lambda x: (1 + x).prod() - 1)
    annual_returns = daily_returns.resample('YE').apply(lambda x: (1 + x).prod() - 1)

    annual_returns_transposed = annual_returns.T
    annual_returns_transposed.columns = annual_returns.index.year.astype(str)
    annual_returns_transposed.index.name = "Crypto"
    annual_returns_transposed = annual_returns_transposed.multiply(100).round(2)
    annual_returns_transposed.to_csv("output/annual_returns_transposed.csv")
    print("\nRendements annuels transposés :")
    print(annual_returns_transposed)

    monthly_returns.index = monthly_returns.index.strftime('%b %Y')
    monthly_returns_transposed = monthly_returns.T
    monthly_returns_transposed.index.name = "Crypto"
    monthly_returns_transposed = monthly_returns_transposed.multiply(100).round(2)
    monthly_returns_transposed.to_csv("output/monthly_returns_all_cryptos.csv")
    print("\nRendements mensuels transposés (toutes cryptos) :")
    print(monthly_returns_transposed.head())

    # Graphique de performance relative
    normalized_prices = pd.DataFrame()
    for ticker in cryptos_tickers:
        close_column = f'Close_{ticker}'
        normalized_prices[ticker] = (data[close_column] / data[close_column].iloc[0] - 1) * 100

    fig, axes = plt.subplots(nrows=len(cryptos_tickers) + 1, ncols=1, 
                            figsize=(14, 3 * (len(cryptos_tickers) + 1)), 
                            gridspec_kw={'height_ratios': [2] + [1] * len(cryptos_tickers)})

    axes[0].set_title('Performance relative des cryptomonnaies (%)')
    for ticker in cryptos_tickers:
        axes[0].plot(normalized_prices.index, normalized_prices[ticker], label=ticker)
    axes[0].set_ylabel('Indice de prix normalisés (base 1000)')
    axes[0].axhline(0, color='black', linewidth=1, linestyle='--')
    axes[0].legend()
    axes[0].grid(True)

    for i, ticker in enumerate(cryptos_tickers):
        close_column = f'Close_{ticker}'
        axes[i + 1].plot(data.index, data[close_column], label=f'Price of {ticker}', color='tab:blue')
        axes[i + 1].set_ylabel('Price ($)')
        axes[i + 1].legend()
        axes[i + 1].grid(True)

    plt.tight_layout()
    fig.savefig('output/performance_relative_et_prix.png')

    #########################################################
    # Volatility

def generate_volatility_charts(data, tickers):
    """
    Generates volatility analysis based on:
    1. Annualized historical volatility (barplot) with values at the end of bars
    2. Rolling volatility over 30 days
    
    Parameters:
    -----------
    data : pandas.DataFrame
        DataFrame containing OHLCV data
    tickers : list
        List of tickers to analyze
    """
    os.makedirs('output', exist_ok=True)

    vol_hist = {}
    vol_rolling = pd.DataFrame()
    ann_factor = 365**0.5
    window = 30

    # Volatility calculations
    for ticker in tickers:
        col = f"Close_{ticker}-USD"
        if col not in data.columns:
            continue
        returns = data[col].pct_change()
        vol_hist[ticker] = returns.std() * ann_factor * 100
        vol_rolling[ticker] = returns.rolling(window).std() * ann_factor * 100

    # Barplot (historical volatility) with values
    vol_hist_series = pd.Series(vol_hist).sort_values(ascending=True)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Create barplot
    bars = ax.barh(y=vol_hist_series.index, 
                   width=vol_hist_series.values,
                   color=sns.color_palette("coolwarm", len(vol_hist_series)))
    
    # Add values at the end of bars
    for bar in bars:
        width = bar.get_width()
        ax.text(width,                     # x position (end of bar)
                bar.get_y() + bar.get_height()/2,  # y position (middle of bar)
                f'{width:.1f}%',           # Text to display
                ha='left',                 # Horizontal alignment
                va='center',               # Vertical alignment
                fontsize=10,               # Font size
                fontweight='bold',         # Bold
                color='black',             # Text color
                bbox=dict(facecolor='white',  # White background
                         alpha=0.7,           # Semi-transparent
                         edgecolor='none',    # No border
                         pad=1))              # Padding
    
    # Customize graph
    ax.set_title("Annualized Historical Volatility (%)", pad=20, fontsize=12, fontweight='bold')
    ax.set_xlabel("Volatility (%)")
    
    # Add light grid
    ax.grid(True, axis='x', linestyle='--', alpha=0.3)
    
    # Adjust margins
    plt.margins(x=0.2)
    
    plt.tight_layout()
    plt.savefig('output/volatilite_historique.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Rolling volatility curves
    plt.figure(figsize=(12, 6))
    for ticker in vol_rolling.columns:
        plt.plot(vol_rolling.index, vol_rolling[ticker], label=ticker)
    plt.title("Evolution of 30-Day Rolling Annualized Volatility")
    plt.xlabel("Date")
    plt.ylabel("Volatility (%)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('output/volatilite_mobile.png')
    plt.close()
# ---------------------------------------------------
# Permet d'exécuter le fichier seul en debug
if __name__ == "__main__":
    run_analysis()