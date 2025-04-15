import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from fredapi import Fred
from itertools import combinations
import os
import json
from extraction import extract_data

import matplotlib
matplotlib.use('Agg') 


def run_analysis():
    cryptos_base = ['BTC', 'ETH', 'SOL', 'BNB']
    cryptos_tickers = [f"{c}-USD" for c in cryptos_base]
    start_date = "2020-04-10"
    end_date = "2025-03-31"

    data = extract_data(cryptos_base, start_date, end_date, save_csv=True)
    data.index = pd.to_datetime(data.index)

    print(data.head())

    daily_returns = pd.DataFrame()
    os.makedirs("output", exist_ok=True)

    for ticker in cryptos_tickers:
        close_column = f'Close_{ticker}'
        daily_returns[ticker] = data[close_column].pct_change()

    print("Rendements quotidiens :")
    print(daily_returns.head())

    # Matrice de corrélation
    correlation_matrix = daily_returns.corr()
    print("\nMatrice de corrélation des rendements quotidiens :")
    print(correlation_matrix.round(2))

    plt.figure(figsize=(8, 6))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt='.2f', linewidths=0.5)
    plt.title("Matrice de corrélation des rendements quotidiens")
    plt.savefig("output/matrice_correlation.png")
    plt.close()
    correlation_matrix.to_csv("output/matrice_correlation.csv")

    rolling_windows = [30, 90]
    crypto_pairs = list(combinations(cryptos_tickers, 2))

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

    fig, axes = plt.subplots(nrows=5, ncols=1, figsize=(14, 12), gridspec_kw={'height_ratios': [2, 1, 1, 1, 1]})

    axes[0].set_title('Performance relative des cryptomonnaies (%)')
    for ticker in cryptos_tickers:
        axes[0].plot(normalized_prices.index, normalized_prices[ticker], label=ticker)
    axes[0].set_ylabel('Indice de prix normalisés (base 1000)')
    axes[0].axhline(0, color='black', linewidth=1, linestyle='--')
    axes[0].legend()
    axes[0].grid(True)

    for i, ticker in enumerate(cryptos_tickers):
        close_column = f'Close_{ticker}'
        axes[i + 1].plot(data.index, data[close_column], label=f'Prix de {ticker}', color='tab:blue')
        axes[i + 1].set_ylabel('Prix ($)')
        axes[i + 1].legend()
        axes[i + 1].grid(True)

    plt.tight_layout()
    fig.savefig('output/performance_relative_et_prix.png')


# ---------------------------------------------------
# Permet d'exécuter le fichier seul en debug
if __name__ == "__main__":
    run_analysis()