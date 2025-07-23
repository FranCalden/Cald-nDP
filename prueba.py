import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- LOGIN ---
def cargar_usuarios():
    url = "https://raw.githubusercontent.com/FranCalden/Cald-nDP/main/usuarios.xlsx"
    df = pd.read_excel(url)
    df.columns = df.columns.str.lower().str.strip()
    return df

def verificar(usuario, clave, df):
    if usuario in df['usuario'].values:
        clave_real = df[df['usuario'] == usuario]['contraseña'].values[0]
        return str(clave) == str(clave_real)
    return False

def registrar_activo(usuario):
    archivo = "usuarios_activos.csv"
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nuevo = pd.DataFrame([[usuario, ahora]], columns=["usuario", "hora"])
    try:
        df = pd.read_csv(archivo)
        df = df[df['usuario'] != usuario]
        df = pd.concat([df, nuevo], ignore_index=True)
    except:
        df = nuevo
    df.to_csv(archivo, index=False)

# --- Control de sesión ---
if 'logueado' not in st.session_state:
    st.session_state.logueado = False
    st.session_state.usuario = ""

if not st.session_state.logueado:
    st.set_page_config(page_title="LOCAL DASHBOARD - CALDÉN", layout="wide", page_icon="🚛")
    st.title("🔐 Acceso al Dashboard")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        df_usuarios = cargar_usuarios()
        if verificar(u, p, df_usuarios):
            st.session_state.logueado = True
            st.session_state.usuario = u
            registrar_activo(u)
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")
    st.stop()

# --- Configuración del dashboard ---
st.set_page_config(page_title="DEMO DASHBOARD - CALDÉN", layout="wide", page_icon="🚛")

# --- Cargar datos originales ---
url_excel = "https://raw.githubusercontent.com/FranCalden/Cald-nDP/main/WGCP143.xlsx"
df_original = pd.read_excel(url_excel)

# --- Preprocesamiento ---
df_original.columns = df_original.columns.str.strip().str.lower()
df_original.rename(columns={
    'patente': 'dominio',
    'caracteristicas': 'tipo',
    'modelo': 'modelo',
    'estado': 'estado',
    'fecha guia': 'fecha_guia'
}, inplace=True)

df_original['fecha_guia'] = pd.to_datetime(df_original['fecha_guia'], errors='coerce')
df_original['modelo'] = pd.to_numeric(df_original['modelo'], errors='coerce')
df_original['tipo'] = df_original['tipo'].fillna('No especificado')

# --- Clonar para aplicar filtros y crear columnas derivadas ---
hoy = datetime.now()
df = df_original.copy()

# Columnas derivadas
df['tipo_limpio'] = df['tipo'].str.extract(r'^(.*?)-')
df['tipo_limpio'] = df['tipo_limpio'].fillna(df['tipo'])
df['antiguedad'] = hoy.year - df['modelo']

# --- Filtros laterales ---
with st.sidebar:
    st.image("icono/calden.ico", width=64)
    st.markdown("## 🚛 Caldén Control - Vehículos")
    st.markdown("Monitoreo y análisis de flota según actividad, tipo, modelo y estado.")
    st.markdown("---")

    with st.expander("🗕️ Filtro por inactividad", expanded=True):
        dias_inactividad = st.radio(
            "Mostrar vehículos sin movimiento por:",
            [0, 30, 60],
            format_func=lambda x: f"Más de {x} días" if x > 0 else "Todos"
        )

    with st.expander("🚗 Filtro por tipo de vehículo", expanded=True):
        tipos_disponibles = sorted(df['tipo'].dropna().unique())
        tipos_especiales = ['BAL', 'BAT', 'CHA', 'DOB', 'HID', 'KON', 'MAR', 'SIM']
        default_tipo = [op for op in tipos_disponibles if any(op.startswith(prefijo) for prefijo in tipos_especiales)]
        if not default_tipo:
            default_tipo = tipos_disponibles

        tipos_seleccionados = st.multiselect(
            "Seleccioná uno o más tipos:",
            tipos_disponibles,
            default=default_tipo
        )

    with st.expander("🛠️ Filtro por año de modelo", expanded=False):
        años_disponibles = sorted(df['modelo'].dropna().unique(), reverse=True)
        años_seleccionados = st.multiselect(
            "Seleccioná uno o más modelos:",
            años_disponibles,
            default=años_disponibles
        )

    st.markdown("---")
    busqueda_dominio = st.text_input("🔍 Buscar por dominio (patente)")

    st.markdown("---")
    st.metric("📦 Total general (sin filtros)", len(df_original))

    st.markdown("---")
    st.markdown(f"👤 Usuario conectado: **{st.session_state.usuario}**")

    try:
        df_activos = pd.read_csv("usuarios_activos.csv")
        df_activos['hora'] = pd.to_datetime(df_activos['hora'])
        ahora = datetime.now()
        conectados = df_activos[df_activos['hora'] > ahora - timedelta(minutes=30)]
        otros = conectados[conectados['usuario'] != st.session_state.usuario]

        st.markdown("### 🟢 Otros conectados")
        for u in otros['usuario'].unique():
            st.markdown(f"- {u}")
        if otros.empty:
            st.markdown("*Nadie más conectado*")
    except:
        st.markdown("*No se pudo leer usuarios activos*")

# --- Aplicar filtros ---
df = df[df['modelo'].isin(años_seleccionados)]
df = df[df['tipo'].isin(tipos_seleccionados)]

if busqueda_dominio:
    df = df[df['dominio'].str.contains(busqueda_dominio, case=False, na=False)]

if dias_inactividad > 0:
    df = df[df['fecha_guia'] < (hoy - timedelta(days=dias_inactividad))]

# --- Título principal ---
st.title("📊 Dashboard General de Vehículos")
st.markdown("---")

# --- KPIs visuales ---
st.markdown("### 📈 Indicadores clave")

# KPI: Total vehículos
total_vehiculos = len(df_original)

# KPI: % camiones de tipo especial
camiones_especiales = ['BAL', 'BAT', 'CHA', 'DOB', 'HID', 'KON', 'MAR', 'SIM']
df_original['tipo_limpio'] = df_original['tipo'].str.extract(r'^(.*?)-')
df_original['tipo_limpio'] = df_original['tipo_limpio'].fillna(df_original['tipo'])
camiones_df = df_original[df_original['tipo_limpio'].isin(camiones_especiales)]
porcentaje_camiones = (len(camiones_df) / total_vehiculos * 100) if total_vehiculos > 0 else 0

# KPI: 2023 o más
nuevos = df_original[df_original['modelo'] >= 2023].shape[0]

# Otros KPIs
df_original['antiguedad'] = hoy.year - df_original['modelo']
df_original['antiguedad'] = df_original['antiguedad'].replace([float('inf'), -float('inf')], pd.NA)
prom_antig = df_original['antiguedad'].dropna().mean()
mayores_10 = df_original[df_original['antiguedad'] > 10].shape[0]
criticos = df_original[df_original['estado'].str.contains("revisar|vencida", case=False, na=False)].shape[0]
sin_mov_30 = df_original[df_original['fecha_guia'] < hoy - timedelta(days=30)].shape[0]
sin_mov_180 = df_original[df_original['fecha_guia'] < hoy - timedelta(days=180)].shape[0]
sin_fecha = df_original['fecha_guia'].isna().sum()
total_filtrado = len(df)
total_general = len(df_original)

# --- KPIs ---
# Calcular porcentajes
porc_sin_mov_30 = (sin_mov_30 / total_vehiculos * 100) if total_vehiculos > 0 else 0
porc_sin_mov_180 = (sin_mov_180 / total_vehiculos * 100) if total_vehiculos > 0 else 0
porc_mayores_10 = (mayores_10 / total_vehiculos * 100) if total_vehiculos > 0 else 0
porc_criticos = (criticos / total_vehiculos * 100) if total_vehiculos > 0 else 0
porc_sin_fecha = (sin_fecha / total_vehiculos * 100) if total_vehiculos > 0 else 0


k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("📦 Total vehículos", total_vehiculos)
k2.metric("🕒 Sin mov. > 30 días", f"{porc_sin_mov_30:.0f}% ({sin_mov_30})")
k3.metric("⛔️ Sin mov. > 180 días", f"{porc_sin_mov_180:.0f}% ({sin_mov_180})")
k4.metric("🗕 Prom. antigüedad", f"{prom_antig:.1f} años")
k5.metric("🚨 >10 años", f"{porc_mayores_10:.0f}% ({mayores_10})")

porc_nuevos = (nuevos / total_vehiculos * 100) if total_vehiculos > 0 else 0

# Segunda fila de KPIs
k6, k7, k8, k9 = st.columns(4)
k6.metric("⚠️ Críticos", f"{porc_criticos:.0f}% ({criticos})")
k7.metric("🚛 % Camiones", f"{porcentaje_camiones:.0f}%")
k8.metric("🆕 2023+", f"{porc_nuevos:.0f}% ({nuevos})")
k9.metric("❓ Sin fecha guía", f"{porc_sin_fecha:.0f}% ({sin_fecha})")


# --- Gráficos ---
# --- Gráficos de inactividad ---
st.markdown("---")
with st.expander("📊 Vehículos con inactividad 30 & 60 días", expanded=True):
    tipos_especiales = ['BAL', 'BAT', 'CHA', 'DOB', 'HID', 'KON', 'MAR', 'SIM']

    df_30 = df_original[df_original['fecha_guia'] < hoy - timedelta(days=30)]
    df_30 = df_30[df_30['tipo_limpio'].isin(tipos_especiales)]
    fig_30 = px.pie(df_30, names='tipo_limpio', title="🔸 Inactivos >30 días")

    df_60 = df_original[df_original['fecha_guia'] < hoy - timedelta(days=60)]
    df_60 = df_60[df_60['tipo_limpio'].isin(tipos_especiales)]
    fig_60 = px.pie(df_60, names='tipo_limpio', title="🔸 Inactivos >60 días")

    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_30, use_container_width=True)
    c2.plotly_chart(fig_60, use_container_width=True)

# --- Gráficos de distribución ---
st.markdown("---")
with st.expander("📊 Distribuciones", expanded=True):
    df_con_guia = df[df['tipo_limpio'].isin(tipos_especiales) & df['fecha_guia'].notna()]
    fig_con_guia = px.pie(df_con_guia, names='tipo_limpio', title="✅ Con guía (BAL, BAT, etc.)")

    df_sin_guia = df[df['tipo_limpio'].isin(tipos_especiales) & df['fecha_guia'].isna()]
    fig_sin_guia = px.pie(df_sin_guia, names='tipo_limpio', title="❌ Sin guía (BAL, BAT, etc.)")

    fig_estado = px.pie(df, names='estado', title="📋 Distribución por estado")

    col1, col2, col3 = st.columns(3)
    col1.plotly_chart(fig_con_guia, use_container_width=True)
    col2.plotly_chart(fig_sin_guia, use_container_width=True)
    col3.plotly_chart(fig_estado, use_container_width=True)

# --- Mantenimiento y vencimientos ---
st.markdown("---")
with st.expander("🔧 Mantenimiento y Vencimientos", expanded=True):
    mantenimiento_recomendado = df[df['antiguedad'] >= 10]
    vencimientos = df[df['fecha_guia'].isna() | (df['fecha_guia'] < hoy - timedelta(days=180))]
    estados_criticos = df[df['estado'].str.contains("revisar|vencida", case=False, na=False)]

    st.warning(f"🔧 {len(mantenimiento_recomendado)} vehículo(s) con más de 10 años de antigüedad.")
    st.dataframe(mantenimiento_recomendado[['dominio', 'modelo', 'tipo', 'estado', 'antiguedad']])

    st.info(f"📅 {len(vencimientos)} vehículo(s) con más de 180 días sin movimiento o sin fecha registrada.")
    st.dataframe(vencimientos[['dominio', 'modelo', 'tipo', 'estado', 'fecha_guia']])

    if not estados_criticos.empty:
        st.warning(f"⚠️ {len(estados_criticos)} vehículo(s) con estado crítico detectado.")
        st.dataframe(estados_criticos[['dominio', 'modelo', 'tipo', 'estado']])

# --- Mapa ---
st.markdown("---")
with st.expander("📽 Mapa Interactivo (si hay coordenadas)", expanded=False):
    if 'latitud' in df.columns and 'longitud' in df.columns:
        df['latitud'] = pd.to_numeric(df['latitud'], errors='coerce')
        df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce')
        df_mapa = df.dropna(subset=['latitud', 'longitud'])

        if df_mapa.empty:
            df['latitud'] = [-34.60 + i*0.01 for i in range(len(df))]
            df['longitud'] = [-58.38 + i*0.01 for i in range(len(df))]
            df_mapa = df.copy()

        fig_map = px.scatter_mapbox(
            df_mapa,
            lat="latitud",
            lon="longitud",
            color="estado",
            hover_name="dominio",
            hover_data=["tipo", "estado"],
            zoom=4,
            height=500
        )
        fig_map.update_layout(mapbox_style="open-street-map")
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("📍 Este archivo no tiene columnas de latitud y longitud.")

# --- Tabla final ---
st.markdown("---")
with st.expander("📋 Detalle General de Vehículos", expanded=False):
    st.markdown("Tabla completa de vehículos filtrados según inactividad, año de modelo y tipo seleccionado.")
    st.dataframe(df)
    st.download_button(
        "📅 Exportar CSV",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name=f"vehiculos_filtrados_{hoy.strftime('%Y%m%d')}.csv",
        mime='text/csv'
    )

st.caption("Desarrollado por Caldén Sistemas")
