import yfinance as yf
import pandas as pd
import os

def extract_data(tickers, start_date, end_date, save_csv=True, csv_filename='rendements_cryptos.csv'):
    # ✅ S'assurer que les tickers sont bien formatés (ex: 'BTC' -> 'BTC-USD')
    tickers = [t.strip().upper() for t in tickers]
    tickers_yf = [f"{t}-USD" if not t.endswith("-USD") else t for t in tickers]

    # Télécharger les données
    data = yf.download(tickers_yf, start=start_date, end=end_date, group_by='ticker', auto_adjust=True)

    print("✅ Tickers demandés :", tickers)
    print("✅ Tickers envoyés à yfinance :", tickers_yf)
    print("✅ Période :", start_date, "→", end_date)

    # Aplatir les colonnes multi-index
    data.columns = [f'{col[1]}_{col[0]}' for col in data.columns]

    # Réorganiser les colonnes dans l’ordre : Close, High, Low, Open, Volume
    columns_order = []
    for ticker in tickers_yf:
        columns_order.extend([
            f'Close_{ticker}',
            f'High_{ticker}',
            f'Low_{ticker}',
            f'Open_{ticker}',
            f'Volume_{ticker}'
        ])
    data = data[columns_order]

    if save_csv:
    # Créer le dossier 'output' s’il n’existe pas
        os.makedirs("output", exist_ok=True)

    # Construire le chemin vers le fichier dans 'output'
    output_path = os.path.join("output", csv_filename)

    # Sauvegarder le CSV
    data.to_csv(output_path)

    print(f"[INFO] Données sauvegardées dans '{output_path}'")
    print("✅ Colonnes retournées :", data.columns.tolist())
    print("✅ Shape des données :", data.shape)

    return data

# Option : exécutable en ligne de commande
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickers", type=str, required=True, help="Tickers séparés par des virgules")
    parser.add_argument("--start", type=str, required=True, help="Date de début (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, required=True, help="Date de fin (YYYY-MM-DD)")
    args = parser.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",")]
    extract_data(tickers, args.start, args.end)

