import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- Configuración del dashboard ---
st.set_page_config(page_title="Dashboard DEMO - Caldén", layout="wide", page_icon="🚛")

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
    st.markdown("## 🚛 Don Pedro - Vehículos")
    st.markdown("Monitoreo y análisis de flota según actividad, tipo, modelo y estado.")
    st.markdown("---")

    with st.expander("📅 Filtro por inactividad", expanded=True):
        dias_inactividad = st.radio(
            "Mostrar vehículos sin movimiento por:",
            [0, 30, 60],
            format_func=lambda x: f"Más de {x} días" if x > 0 else "Todos"
        )

    with st.expander("🚗 Filtro por tipo de vehículo", expanded=True):
        tipos_disponibles = sorted(df['tipo'].dropna().unique())
        default_tipo = [op for op in tipos_disponibles if "camion" in op.lower()]
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

    # 🔍 Búsqueda por dominio (patente)
    st.markdown("---")
    busqueda_dominio = st.text_input("🔍 Buscar por dominio (patente)")

    # Total general
    st.markdown("---")
    st.sidebar.metric("📦 Total general (sin filtros)", len(df_original))

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

# 1. Total activos
activos = df_original[~df_original['estado'].str.lower().isin(['baja', 'fuera de servicio', 'inactivo'])]
total_activos = len(activos)

# 2. Sin movimiento > 30 días
sin_mov_30 = df[df['fecha_guia'] < hoy - timedelta(days=30)].shape[0]

# 3. Sin movimiento > 180 días
sin_mov_180 = df[df['fecha_guia'] < hoy - timedelta(days=180)].shape[0]

# 4. Promedio antigüedad
prom_antig = df['antiguedad'].mean()

# 5. >10 años
mayores_10 = df[df['antiguedad'] > 10].shape[0]

# 6. Estado crítico
criticos = df[df['estado'].str.contains("revisar|vencida", case=False, na=False)].shape[0]

# 7. % por tipo
camiones = df[df['tipo_limpio'].str.lower().str.contains("camion")].shape[0]
porcentaje_camiones = (camiones / len(df) * 100) if len(df) > 0 else 0

# 8. Modelo recientes (2023+)
nuevos = df[df['modelo'] >= 2023].shape[0]

# 9. Sin fecha guía
sin_fecha = df['fecha_guia'].isna().sum()

# 10. Comparativa filtrado
total_filtrado = len(df)
total_general = len(df_original)

# Primera fila
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("✅ Activos", total_activos)
with k2:
    st.metric("🕒 Sin mov. > 30 días", sin_mov_30)
with k3:
    st.metric("⛔️ Sin mov. > 180 días", sin_mov_180)
with k4:
    st.metric("📅 Prom. antigüedad", f"{prom_antig:.1f} años")
with k5:
    st.metric("🚨 >10 años", mayores_10)

# Segunda fila
k6, k7, k8, k9, k10 = st.columns(5)
with k6:
    st.metric("⚠️ Críticos", criticos)
with k7:
    st.metric("🚛 % Camiones", f"{porcentaje_camiones:.0f}%")
with k8:
    st.metric("🆕 2023+", nuevos)
with k9:
    st.metric("❓ Sin fecha guía", sin_fecha)
with k10:
    st.metric("🔍 Filtrados", f"{total_filtrado} / {total_general}")

# --- Gráficos de torta ---
with st.expander("📊 Distribuciones", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        fig_tipo = px.pie(df, names='tipo_limpio', title="Distribución por tipo de vehículo")
        fig_tipo.update_layout(width=500, height=500)
        st.plotly_chart(fig_tipo, use_container_width=True)
    with col2:
        fig_estado = px.pie(df, names='estado', title="Distribución por estado")
        fig_estado.update_layout(width=500, height=500)
        st.plotly_chart(fig_estado, use_container_width=True)

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

# --- Mapa (si hay coordenadas) ---
st.markdown("---")
with st.expander("🗺 Mapa Interactivo (si hay coordenadas)", expanded=False):
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
        "📥 Exportar CSV",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name=f"vehiculos_filtrados_{hoy.strftime('%Y%m%d')}.csv",
        mime='text/csv'
    )

st.caption("Desarrollado por Caldén Sistemas")
