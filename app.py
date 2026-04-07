import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Mi Wallet BTC", layout="wide")
db_file = 'historial_btc.csv'

# --- FUNCIONES DE APOYO ---
def obtener_precio_btc():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        response = requests.get(url, timeout=5)
        return float(response.json()['price'])
    except:
        return 0.0

def cargar_datos():
    if os.path.exists(db_file):
        df = pd.read_csv(db_file)
        # Aseguramos que la columna Fecha sea string para evitar errores de guardado
        df['Fecha'] = df['Fecha'].astype(str)
        return df
    return pd.DataFrame(columns=['Fecha', 'Tipo', 'Precio_USD', 'Monto_BTC'])

# --- CÁLCULOS PRINCIPALES ---
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

# --- DISEÑO DE LA INTERFAZ ---
st.title("📊 Mi Centro de Mando BTC")

# Métricas superiores
m1, m2, m3 = st.columns(3)
m1.metric("Saldo en Wallet", f"{total_btc:.8f} BTC")
m2.metric("Precio Promedio", f"${promedio:,.2f}")
m3.metric("Inversión Total", f"${inversion_total:,.2f}")

st.divider()

# Sección de Precio en Vivo
st.subheader(f"🚀 Mercado en Vivo (BTC: ${precio_actual:,.2f})")
c1, c2, c3 = st.columns(3)
c1.metric("Valor Actual ($)", f"${valor_actual_wallet:,.2f}")
c2.metric("Ganancia/Pérdida ($)", f"${ganancia_usd:,.2f}", delta=f"${ganancia_usd:,.2f}")
c3.metric("Rendimiento (%)", f"{porcentaje:.2f}%", delta=f"{porcentaje:.2f}%")

if st.button("🔄 Actualizar Precio Ahora"):
    st.rerun()

st.divider()

# --- BARRA LATERAL (ENTRADA DE DATOS) ---
with st.sidebar:
    st.header("📝 Registrar Operación")
    
    # Creamos un formulario que se limpia al hacer click en el botón
    with st.form("mi_formulario", clear_on_submit=True):
        tipo = st.selectbox("Tipo", ["Compra", "Retiro"])
        fecha = st.date_input("Fecha", datetime.now())
        precio_f = st.number_input("Precio USD", value=precio_actual, format="%.2f")
        monto_f = st.number_input("Monto BTC", min_value=0.0, format="%.8f", step=0.00000001)
        
        btn_guardar = st.form_submit_button("🚀 Guardar Registro")
        
        if btn_guardar:
            if monto_f > 0:
                nueva_fila = pd.DataFrame([[str(fecha), tipo, precio_f, monto_f]], columns=df.columns)
                df_final = pd.concat([df, nueva_fila], ignore_index=True)
                df_final.to_csv(db_file, index=False)
                st.success("✅ ¡Guardado!")
                st.rerun() # Recarga la app para mostrar los nuevos datos arriba
            else:
                st.error("El monto debe ser mayor a 0")

    st.divider()
    st.header("⚠️ Zona de Edición")
    if st.button("🗑️ Borrar última fila"):
        if not df.empty:
            df = df[:-1]
            df.to_csv(db_file, index=False)
            st.warning("Última fila eliminada")
            st.rerun()
        else:
            st.info("No hay datos")

# --- TABLA DE HISTORIAL ---
st.subheader("📜 Historial de Movimientos")
if not df.empty:
    # Mostramos el historial con lo más reciente arriba (índice invertido)
    st.dataframe(df.iloc[::-1], use_container_width=True)
else:
    st.info("Aún no tienes movimientos registrados.")
