import streamlit as st
import pandas as pd
import numpy as np
import datetime
import sqlite3
import plotly.graph_objs as go
from streamlit_autorefresh import st_autorefresh
import requests

# Konfiguracja SQLite
DATABASE_PATH = 'data_dashboard.db'

def create_database():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS real_time_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Time DATETIME DEFAULT CURRENT_TIMESTAMP,
        Value REAL
    )
    ''')
    conn.commit()
    conn.close()

create_database()

# Twelve Data API Endpoint
TWELVE_DATA_URL = "https://api.twelvedata.com/price"
API_KEY = "391309a214aa4301a70f58e0660816e2"

# Stock Symbols
SYMBOLS = ["AAPL"]

# Maksymalna liczba punktów na wykresie
MAX_POINTS = 20

# Funkcja do generowania losowych danych
def generate_random_data():
    current_time = datetime.datetime.now()
    return pd.DataFrame({
        'Time': [current_time],
        'Value': [round(np.random.uniform(0, 100), 2)]
    })

# Funkcja do pobierania danych z bazy SQLite
def fetch_data_from_sql(query):
    conn = sqlite3.connect(DATABASE_PATH)
    data = pd.read_sql(query, conn)
    conn.close()
    return data

# Funkcja do zapisywania danych do SQLite
def save_data_to_sqlite(data):
    conn = sqlite3.connect(DATABASE_PATH)
    data.to_sql('real_time_data', conn, if_exists='append', index=False)
    conn.commit()
    conn.close()

# Funkcja do pobierania cen akcji
def get_stock_price(symbol):
    params = {
        "symbol": symbol,
        "apikey": API_KEY
    }
    response = requests.get(TWELVE_DATA_URL, params=params)
    data = response.json()
    return float(data.get("price", 0))  # Return price or 0 if missing

# Funkcja do inicjalizacji danych w `st.session_state`
def initialize_session_state():
    if "data_generated" not in st.session_state:
        st.session_state["data_generated"] = pd.DataFrame(columns=['Time', 'Value'])
    if "data_stock" not in st.session_state:
        st.session_state["data_stock"] = pd.DataFrame(columns=['Time', 'Value'])

# Inicjalizacja danych
initialize_session_state()

st.title("Real-Time Data Dashboard")

# Sekcja: Generated Data
generated_container = st.container()
with generated_container:
    st.header("Generated Data")

    # Generowanie nowych danych
    new_generated_row = generate_random_data()
    st.session_state["data_generated"] = pd.concat(
        [st.session_state["data_generated"], new_generated_row],
        ignore_index=True
    )

    # Utrzymanie ograniczonej liczby punktów
    if len(st.session_state["data_generated"]) > MAX_POINTS:
        st.session_state["data_generated"] = st.session_state["data_generated"].tail(MAX_POINTS)

    # Zapis nowych danych do bazy
    save_data_to_sqlite(new_generated_row)

    # Rysowanie wykresu
    fig_generated = go.Figure()
    fig_generated.add_trace(go.Scatter(
        x=st.session_state["data_generated"]['Time'],
        y=st.session_state["data_generated"]['Value'],
        mode='lines+markers',
        name='Generated Data'
    ))
    fig_generated.update_layout(
        title="Generated Data Visualization",
        xaxis_title="Time",
        yaxis_title="Value"
    )
    st.plotly_chart(fig_generated)

# Sekcja: Database Data
database_container = st.container()
with database_container:
    st.header("Database Data")

    data_db = fetch_data_from_sql("SELECT * FROM real_time_data")
    if len(data_db) > MAX_POINTS:
        data_db = data_db.tail(MAX_POINTS)

    fig_db = go.Figure()
    fig_db.add_trace(go.Scatter(
        x=data_db['Time'],
        y=data_db['Value'],
        mode='lines+markers',
        name='Database Data'
    ))
    fig_db.update_layout(
        title="Database Data Visualization",
        xaxis_title="Time",
        yaxis_title="Value"
    )
    st.plotly_chart(fig_db)

# Sekcja: Stock Data
stock_container = st.container()
with stock_container:
    st.header("Stock Data")

    current_time = datetime.datetime.now()
    for symbol in SYMBOLS:
        price = get_stock_price(symbol)
        new_stock_row = pd.DataFrame({
            'Time': [current_time],
            'Value': [price]
        })
        st.session_state["data_stock"] = pd.concat(
            [st.session_state["data_stock"], new_stock_row],
            ignore_index=True
        )

    # Utrzymanie ograniczonej liczby punktów
    if len(st.session_state["data_stock"]) > MAX_POINTS:
        st.session_state["data_stock"] = st.session_state["data_stock"].tail(MAX_POINTS)

    fig_stock = go.Figure()
    fig_stock.add_trace(go.Scatter(
        x=st.session_state["data_stock"]['Time'],
        y=st.session_state["data_stock"]['Value'],
        mode='lines+markers',
        name='Stock Price'
    ))
    fig_stock.update_layout(
        title="Stock Data Visualization",
        xaxis_title="Time",
        yaxis_title="Price"
    )
    st.plotly_chart(fig_stock)

# Automatyczne odświeżanie w tle
st_autorefresh(interval=1000, limit=None, key="data_refresh")
