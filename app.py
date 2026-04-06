import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURACIÓN DE LA APP ---
st.set_page_config(page_title="Mi Wallet BTC", layout="wide")
db_file = 'historial_btc.csv'

# Función para cargar datos
def cargar_datos():
    if os.path.exists(db_file):
        return pd.read_csv(db_file)
    return pd.DataFrame(columns=['Fecha', 'Tipo', 'Precio_USD', 'Monto_BTC'])

# --- LÓGICA DE CÁLCULOS ---
df = cargar_datos()
total_btc = df[df['Tipo']=='Compra']['Monto_BTC'].sum() - df[df['Tipo']=='Retiro']['Monto_BTC'].sum()
inversion_total = (df[df['Tipo']=='Compra']['Precio_USD'] * df[df['Tipo']=='Compra']['Monto_BTC']).sum()
promedio = inversion_total / df[df['Tipo']=='Compra']['Monto_BTC'].sum() if not df.empty else 0

# --- INTERFAZ VISUAL ---
st.title("📊 Control de Inversión Bitcoin")

col1, col2, col3 = st.columns(3)
col1.metric("Saldo en Wallet", f"{total_btc:.8f} BTC")
col2.metric("Inversión Total", f"${inversion_total:,.2f}")
col3.metric("Precio Promedio", f"${promedio:,.2f}")

st.divider()

# Formulario para nuevas entradas
with st.sidebar:
    st.header("Registrar Operación")
    tipo = st.selectbox("Tipo", ["Compra", "Retiro"])
    fecha = st.date_input("Fecha", datetime.now())
    precio = st.number_input("Precio USD", min_value=0.0, format="%.2f")
    monto = st.number_input("Monto BTC", min_value=0.0, format="%.8f")
    
    if st.button("Guardar Registro"):
        nueva_fila = pd.DataFrame([[fecha, tipo, precio, monto]], columns=df.columns)
        df = pd.concat([df, nueva_fila], ignore_index=True)
        df.to_csv(db_file, index=False)
        st.success("¡Guardado correctamente!")
        st.rerun()

# --- RESPALDO ---
st.subheader("Historial de Movimientos")
st.dataframe(df, use_container_width=True)

if not df.empty:
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Respaldo (Excel/CSV)",
        data=csv,
        file_name=f'respaldo_btc_{datetime.now().strftime("%Y%m%d")}.csv',
        mime='text/csv',
    )
