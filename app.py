import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Mi Wallet BTC", layout="wide")
db_file = 'historial_btc.csv'

def obtener_precio_btc():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        response = requests.get(url)
        return float(response.json()['price'])
    except:
        return 0.0

def cargar_datos():
    if os.path.exists(db_file):
        return pd.read_csv(db_file)
    return pd.DataFrame(columns=['Fecha', 'Tipo', 'Precio_USD', 'Monto_BTC'])

# --- CÁLCULOS ---
df = cargar_datos()
precio_actual = obtener_precio_btc()

# Totales
compras_df = df[df['Tipo']=='Compra']
retiros_df = df[df['Tipo']=='Retiro']

total_btc = compras_df['Monto_BTC'].sum() - retiros_df['Monto_BTC'].sum()
inversion_total = (compras_df['Precio_USD'] * compras_df['Monto_BTC']).sum()
promedio = inversion_total / compras_df['Monto_BTC'].sum() if not compras_df.empty else 0

# Valor Actual y Ganancias
valor_actual_wallet = total_btc * precio_actual
ganancia_usd = valor_actual_wallet - (total_btc * promedio) if total_btc > 0 else 0
porcentaje = ((precio_actual - promedio) / promedio * 100) if promedio > 0 else 0

# --- INTERFAZ VISUAL ---
st.title("📊 Mi Centro de Mando BTC")

# Fila 1: Métricas Principales
m1, m2, m3 = st.columns(3)
m1.metric("Saldo en Wallet", f"{total_btc:.8f} BTC")
m2.metric("Precio Promedio", f"${promedio:,.2f}")
m3.metric("Inversión Total", f"${inversion_total:,.2f}")

# Fila 2: Rendimiento en Vivo
st.divider()
st.subheader(f"🚀 Rendimiento en Vivo (BTC: ${precio_actual:,.2f})")
c1, c2, c3 = st.columns(3)

color = "normal" if ganancia_usd >= 0 else "inverse"
c1.metric("Valor Actual Wallet", f"${valor_actual_wallet:,.2f}")
c2.metric("Ganancia/Pérdida USD", f"${ganancia_usd:,.2f}", delta=f"${ganancia_usd:,.2f}")
c3.metric("Rendimiento %", f"{porcentaje:.2f}%", delta=f"{porcentaje:.2f}%")

if st.button("🔄 Actualizar Precio"):
    st.rerun()

st.divider()

# --- SIDEBAR Y TABLA ---
with st.sidebar:
    st.header("Registrar Operación")
    tipo = st.selectbox("Tipo", ["Compra", "Retiro"])
    fecha = st.date_input("Fecha", datetime.now())
    # Sugerimos el precio actual para facilitar el registro
    precio_input = st.number_input("Precio USD", value=precio_actual, format="%.2f")
    monto_input = st.number_input("Monto BTC", min_value=0.0, format="%.8f")
    
    if st.button("Guardar Registro"):
        nueva_fila = pd.DataFrame([[fecha, tipo, precio_input, monto_input]], columns=df.columns)
        df = pd.concat([df, nueva_fila], ignore_index=True)
        df.to_csv(db_file, index=False)
        st.success("¡Registro exitoso!")
        st.rerun()

st.subheader("Historial Completo")
st.dataframe(df, use_container_width=True)
