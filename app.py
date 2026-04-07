import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Mi Wallet BTC", layout="wide")
db_file = 'historial_btc.csv'

# --- FUNCIÓN DE PRECIO (AHORA CON COINGECKO + BINANCE) ---
def obtener_precio_btc():
    # Intento 1: CoinGecko (Más estable para web)
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        return float(response.json()['bitcoin']['usd'])
    except:
        # Intento 2: Binance (Respaldo)
        try:
            url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
            response = requests.get(url, timeout=10)
            return float(response.json()['price'])
        except:
            return 0.0

def cargar_datos():
    if os.path.exists(db_file):
        df = pd.read_csv(db_file)
        df['Fecha'] = df['Fecha'].astype(str)
        return df
    return pd.DataFrame(columns=['Fecha', 'Tipo', 'Precio_USD', 'Monto_BTC'])

# --- INICIO DE DATOS ---
df = cargar_datos()

# BOTÓN DE ACTUALIZAR EN EL SIDEBAR PARA QUE SEA MÁS FUERTE
with st.sidebar:
    st.title("⚙️ Controles")
    if st.button("🔄 REFRESCAR PRECIO AHORA", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    precio_actual = obtener_precio_btc()
    
    # Si sigue fallando la conexión, dejamos que tú pongas el precio a mano
    if precio_actual == 0:
        st.warning("⚠️ No pude conectar con el mercado.")
        precio_actual = st.number_input("Introduce precio actual manualmente:", value=70000.0)

# --- CÁLCULOS ---
compras_df = df[df['Tipo']=='Compra']
retiros_df = df[df['Tipo']=='Retiro']

total_btc = compras_df['Monto_BTC'].sum() - retiros_df['Monto_BTC'].sum()
inversion_total = (compras_df['Precio_USD'] * compras_df['Monto_BTC']).sum()
promedio = inversion_total / compras_df['Monto_BTC'].sum() if not compras_df.empty else 0

valor_actual_wallet = total_btc * precio_actual
ganancia_usd = valor_actual_wallet - (total_btc * promedio) if total_btc > 0 else 0
porcentaje = ((precio_actual - promedio) / promedio * 100) if promedio > 0 else 0

# --- INTERFAZ ---
st.title("📊 Mi Centro de Mando BTC")

m1, m2, m3 = st.columns(3)
m1.metric("Saldo en Wallet", f"{total_btc:.8f} BTC")
m2.metric("Precio Promedio", f"${promedio:,.2f}")
m3.metric("Inversión Total", f"${inversion_total:,.2f}")

st.divider()

# RENDIMIENTO
st.subheader(f"🚀 Mercado en Vivo (Precio BTC: ${precio_actual:,.2f})")
c1, c2, c3 = st.columns(3)
color_delta = "normal" if ganancia_usd >= 0 else "inverse"

c1.metric("Valor Actual ($)", f"${valor_actual_wallet:,.2f}")
c2.metric("Ganancia/Pérdida ($)", f"${ganancia_usd:,.2f}", delta=f"${ganancia_usd:,.2f}", delta_color=color_delta)
c3.metric("Rendimiento (%)", f"{porcentaje:.2f}%", delta=f"{porcentaje:.2f}%", delta_color=color_delta)

st.divider()

# --- REGISTRO ---
with st.sidebar:
    st.header("📝 Nueva Operación")
    with st.form("registro_form", clear_on_submit=True):
        tipo = st.selectbox("Tipo", ["Compra", "Retiro"])
        fecha = st.date_input("Fecha", datetime.now())
        precio_f = st.number_input("Precio USD", value=precio_actual, format="%.2f")
        monto_f = st.number_input("Monto BTC", min_value=0.0, format="%.8f", step=0.00000001)
        
        if st.form_submit_button("🚀 Guardar Registro"):
            if monto_f > 0:
                nueva_fila = pd.DataFrame([[str(fecha), tipo, precio_f, monto_f]], columns=df.columns)
                df_final = pd.concat([df, nueva_fila], ignore_index=True)
                df_final.to_csv(db_file, index=False)
                st.rerun()

    if st.button("🗑️ Borrar última fila"):
        if not df.empty:
            df = df[:-1]
            df.to_csv(db_file, index=False)
            st.rerun()

# --- HISTORIAL ---
st.subheader("📜 Historial Detallado")
if not df.empty:
    st.dataframe(
        df.iloc[::-1], 
        use_container_width=True,
        column_config={
            "Monto_BTC": st.column_config.NumberColumn("Monto BTC", format="%.8f"),
            "Precio_USD": st.column_config.NumberColumn("Precio USD", format="$%.,2f")
        }
    )
