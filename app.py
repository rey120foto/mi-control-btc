import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime
import time

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

# --- INICIALIZACIÓN DE ESTADO ---
if 'form_limpio' not in st.session_state:
    st.session_state.form_limpio = False

# --- CÁLCULOS ---
df = cargar_datos()
precio_actual = obtener_precio_btc()

compras_df = df[df['Tipo']=='Compra']
retiros_df = df[df['Tipo']=='Retiro']

total_btc = compras_df['Monto_BTC'].sum() - retiros_df['Monto_BTC'].sum()
inversion_total = (compras_df['Precio_USD'] * compras_df['Monto_BTC']).sum()
promedio = inversion_total / compras_df['Monto_BTC'].sum() if not compras_df.empty else 0

valor_actual_wallet = total_btc * precio_actual
ganancia_usd = valor_actual_wallet - (total_btc * promedio) if total_btc > 0 else 0
porcentaje = ((precio_actual - promedio) / promedio * 100) if promedio > 0 else 0

# --- INTERFAZ VISUAL ---
st.title("📊 Mi Centro de Mando BTC")

m1, m2, m3 = st.columns(3)
m1.metric("Saldo en Wallet", f"{total_btc:.8f} BTC")
m2.metric("Precio Promedio", f"${promedio:,.2f}")
m3.metric("Inversión Total", f"${inversion_total:,.2f}")

st.divider()
st.subheader(f"🚀 Rendimiento en Vivo (BTC: ${precio_actual:,.2f})")
c1, c2, c3 = st.columns(3)

c1.metric("Valor Actual Wallet", f"${valor_actual_wallet:,.2f}")
c2.metric("Ganancia/Pérdida USD", f"${ganancia_usd:,.2f}", delta=f"${ganancia_usd:,.2f}")
c3.metric("Rendimiento %", f"{porcentaje:.2f}%", delta=f"{porcentaje:.2f}%")

if st.button("🔄 Actualizar Precio y Datos"):
    st.rerun()

st.divider()

# --- SIDEBAR (REGISTRO) ---
with st.sidebar:
    st.header("📝 Nueva Operación")
    
    # Usamos una clave (key) para poder resetear los campos
    tipo = st.selectbox("Tipo", ["Compra", "Retiro"], key="tipo_input")
    fecha = st.date_input("Fecha", datetime.now(), key="fecha_input")
    precio_input = st.number_input("Precio USD", value=precio_actual, format="%.2f", key="precio_input")
    monto_input = st.number_input("Monto BTC", min_value=0.0, format="%.8f", step=0.00000001, key="monto_input")
    
    if st.button("🚀 Guardar Registro"):
        if monto_input > 0:
            nueva_fila = pd.DataFrame([[str(fecha), tipo, precio_input, monto_input]], columns=df.columns)
            df = pd.concat([df, nueva_fila], ignore_index=True)
            df.to_csv(db_file, index=False)
            
            # Feedback visual y reset
            st.success("✅ ¡Guardado exitosamente!")
            time.sleep(1) # Pausa breve para que el usuario vea el mensaje
            st.rerun() # Esto limpia los campos automáticamente
        else:
            st.error("El monto debe ser mayor a 0")

    st.divider()
    st.header("⚠️ Zona de Edición")
    if st.button("🗑️ Borrar última fila"):
        if not df.empty:
            df = df[:-1] # Elimina la última fila
            df.to_csv(db_file, index=False)
            st.warning("Última fila eliminada")
            time.sleep(1)
            st.rerun()
        else:
            st.info("No hay datos para borrar")

# --- TABLA DE HISTORIAL ---
st.subheader("📜 Historial de Movimientos")
if not df.empty:
    st.dataframe(df.sort_index(ascending=False), use_container_width=True) # Muestra lo más reciente arriba
else:
    st.info("Aún no tienes movimientos registrados.")
