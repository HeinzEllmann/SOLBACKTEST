import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

# --- Telegram Kanal Eingabe ---
st.sidebar.header("Telegram Kanal hinzufügen")
telegram_input = st.sidebar.text_input("z. B. /@xyz_calls", value="/@")
if telegram_input and not telegram_input.startswith("/@"):
    st.sidebar.warning("Bitte beginne den Kanalnamen mit '/@'")
elif telegram_input.startswith("/@"):
    st.sidebar.success(f"Kanal gespeichert: {telegram_input}")

# --- Backtesting-Klasse ---
class SolanaStrategyBacktester:
    def __init__(self, data, sl=0.03, tp=0.05, tsl=0.02, split=True):
        self.data = data
        self.sl = sl
        self.tp = tp
        self.tsl = tsl
        self.split = split
        self.results = []

    def run(self):
        position_open = False
        entry_price = 0
        trailing_stop = 0

        for i in range(1, len(self.data)):
            row = self.data.iloc[i]
            if not position_open:
                entry_price = row['close']
                position_open = True
                trailing_stop = entry_price * (1 - self.tsl)
                continue

            high = row['high']
            low = row['low']

            if self.split and high >= entry_price * (1 + self.tp):
                self.results.append(self.tp)
                position_open = False
                continue

            if low <= entry_price * (1 - self.sl):
                self.results.append(-self.sl)
                position_open = False
                continue

            if high > entry_price:
                trailing_stop = max(trailing_stop, high * (1 - self.tsl))
            if low <= trailing_stop:
                profit = (low - entry_price) / entry_price
                self.results.append(profit)
                position_open = False

    def stats(self):
        total_return = sum(self.results)
        avg_return = np.mean(self.results) if self.results else 0
        win_rate = np.mean([1 if r > 0 else 0 for r in self.results]) if self.results else 0
        return {
            "Trades": len(self.results),
            "Total Return (%)": round(total_return * 100, 2),
            "Average Return (%)": round(avg_return * 100, 2),
            "Win Rate (%)": round(win_rate * 100, 2)
        }

    def plot(self):
        capital = np.cumsum(self.results)
        fig, ax = plt.subplots()
        ax.plot(capital)
        ax.set_title("Kapitalverlauf")
        ax.set_xlabel("Trade #")
        ax.set_ylabel("Kumulierte Rendite")
        ax.grid(True)
        st.pyplot(fig)

# --- Optimierung ---
def grid_optimization(df, sl_range, tp_range, tsl_range, split):
    records = []
    for sl in sl_range:
        for tp in tp_range:
            for tsl in tsl_range:
                tester = SolanaStrategyBacktester(df, sl, tp, tsl, split)
                tester.run()
                stats = tester.stats()
                records.append({
                    'SL': sl,
                    'TP': tp,
                    'TSL': tsl,
                    'Return': stats["Total Return (%)"]
                })
    return pd.DataFrame(records)

# --- Heatmap ---
def plot_heatmap(df_result, x_param, y_param):
    pivot = df_result.pivot(index=y_param, columns=x_param, values='Return')
    fig, ax = plt.subplots()
    c = ax.imshow(pivot, cmap='viridis', aspect='auto', origin='lower')
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([f"{x*100:.1f}%" for x in pivot.columns])
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels([f"{y*100:.1f}%" for y in pivot.index])
    ax.set_xlabel(f"{x_param} (%)")
    ax.set_ylabel(f"{y_param} (%)")
    fig.colorbar(
    c, ax=ax, label="Total Return (%)")
    st.pyplot(fig)
  # --- Excel-Export ---
def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Optimierung')
    output.seek(0)
    return output

# --- Streamlit App Start ---
st.set_page_config(layout="wide")
st.title("Solana Strategy Backtester")
st.markdown("**Teste. Optimiere. Gewinne.**")

uploaded_file = st.file_uploader("Lade OHLCV CSV-Datei hoch (Spalten: timestamp, open, high, low, close, volume)", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if not {'open', 'high', 'low', 'close', 'volume'}.issubset(df.columns):
        st.error("CSV muss Spalten wie 'open', 'high', 'low', 'close', 'volume' enthalten.")
    else:
        st.success("Daten erfolgreich geladen.")
        st.write("Vorschau:", df.head())

        st.header("1. Backtest")
        col1, col2, col3, col4 = st.columns(4)
        sl = col1.slider("Stop-Loss (%)", 0.5, 10.0, 2.0) / 100
        tp = col2.slider("Take-Profit (%)", 0.5, 15.0, 5.0) / 100
        tsl = col3.slider("Trailing Stop-Loss (%)", 0.1, 10.0, 1.5) / 100
        split = col4.checkbox("Split-Gewinne", value=True)

        if st.button("Backtest starten"):
            tester = SolanaStrategyBacktester(df, sl, tp, tsl, split)
            tester.run()
            st.subheader("Ergebnisse")
            st.write(tester.stats())
            tester.plot()

        st.markdown("---")
        st.header("2. Optimierung & Heatmap")

        with st.expander("Optimierungsparameter"):
            sl_min = st.number_input("SL min (%)", value=1.0) / 100
            sl_max = st.number_input("SL max (%)", value=5.0) / 100
            sl_step = st.number_input("SL Schrittweite (%)", value=1.0) / 100

            tp_min = st.number_input("TP min (%)", value=2.0) / 100
            tp_max = st.number_input("TP max (%)", value=10.0) / 100
            tp_step = st.number_input("TP Schrittweite (%)", value=2.0) / 100

            tsl_min = st.number_input("TSL min (%)", value=1.0) / 100
            tsl_max = st.number_input("TSL max (%)", value=3.0) / 100
            tsl_step = st.number_input("TSL Schrittweite (%)", value=1.0) / 100

        if st.button("Optimierung starten"):
            sl_range = np.round(np.arange(sl_min, sl_max + sl_step, sl_step), 4)
            tp_range = np.round(np.arange(tp_min, tp_max + tp_step, tp_step), 4)
            tsl_range = np.round(np.arange(tsl_min, tsl_max + tsl_step, tsl_step), 4)

            result_df = grid_optimization(df, sl_range, tp_range, tsl_range, split)
            best = result_df.sort_values("Return", ascending=False).head(1)

            st.subheader("Beste Kombination")
            st.write(best)

            st.subheader("Heatmap: SL vs. TP bei erstem TSL-Wert")
            filtered = result_df[result_df['TSL'] == tsl_range[0]]
            if not filtered.empty:
                plot_heatmap(filtered, 'TP', 'SL')
            else:
                st.warning("Keine Daten für gewählte Parameterkombination.")

            excel = convert_df_to_excel(result_df)
            st.download_button("Optimierungsergebnisse als Excel herunterladen",
                               data=excel,
                               file_name="solana_optimierung.xlsx")
