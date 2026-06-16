import sys
import mock
# Parche de compatibilidad visual para evitar fallos de renderizado
sys.modules["altair.vegalite.v4"] = mock.Mock()

from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import json
from fpdf import FPDF
import io
import requests
import base64

# ==============================================================================
# --- 1. PERSISTENCIA CLOUD BLINDADA (ENTORNO SEGURO) ---
# ==============================================================================
DB_FILE = "progreso_logistica.json"
LOGO, PAC = "Sello GTAE.png", "2026 02 01 - reforma pac logistica.xlsx"
URL_BASE_FAE = "https://almacenamiento.fae.mil.ec/index.php/apps/dashboard/"

GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", None)
GITHUB_REPO = st.secrets.get("GITHUB_REPO", None)

def empujar_cambios_a_github():
    """Sincroniza automáticamente el archivo JSON con el repositorio de GitHub."""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return
        
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DB_FILE}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    with open(DB_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        
    res = requests.get(url, headers=headers)
    sha = None
    if res.status_code == 200:
        sha = res.json().get("sha")
        
    content_base64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    
    payload = {
        "message": f"Sincronización Automática PAC - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "content": content_base64
    }
    if sha:
        payload["sha"] = sha
        
    requests.put(url, headers=headers, json=payload)

# Inicializar o cargar la base de datos
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try: st.session_state.avances = json.load(f)
        except: st.session_state.avances = {}
else:
    st.session_state.avances = {}

if "procesos_nuevos" not in st.session_state.avances:
    st.session_state.avances["procesos_nuevos"] = []

def proceso_esta_activo(idx, es_nuevo=False):
    clave = f"nuevo_estado_op_{idx}" if es_nuevo else f"estado_op_{idx}"
    return st.session_state.avances.get(clave, "ACTIVO") in ["ACTIVO", "🟢 ACTIVO"]

def guardar_base_datos(datos):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)
    empujar_cambios_a_github()

# --- SISTEMA DE OPERADORES Y CREDENCIALES ---
USR = {
    "gconteron": {"nom": "Geovanny Conterón", "pin": "121026", "rol": "admin"},
    "encargado": {"nom": "ENCARGADO DE PROCESOS", "pin": "2026", "rol": "supervisor"}
}

lista_base_inicial = [
    "SIN ASIGNAR", "ALBUJA L.", "BENAVIDES H.", "CAICEDO K.", "CAIZA J.", 
    "CALVOPIÑA F.", "CANDO R.", "CEVALLOS C.", "CONTERON G.", "CPAREDES H.", 
    "CRODRIGUEZ M.", "CUICHAN M.", "GODOY L.", "GOMEZ R.", "GUALOTUÑA J.", 
    "JACHO C.", "LOACHAMIN R.", "MALDONADO J.", "MULLO V.", "NARANJO J.", 
    "NIETO J.", "NIQUINGA I.", "REMACHE L.", "ROSAS J.", "SEVILLANO A.", 
    "SOCASI J.", "SPAREDES J.", "SRODRIGUEZ J.", "TAPIA J.", "TOAPANTA G.", 
    "VARGAS J.", "VELASCO J.", "VILLACRES A.", "YANEZ C."
]

if "lista_usuarios_gtae" not in st.session_state.avances:
    st.session_state.avances["lista_usuarios_gtae"] = sorted(list(set(lista_base_inicial)))
    guardar_base_datos(st.session_state.avances)
else:
    lista_combinada = list(set(st.session_state.avances["lista_usuarios_gtae"] + lista_base_inicial))
    st.session_state.avances["lista_usuarios_gtae"] = sorted(lista_combinada)

lista_admins_reales = st.session_state.avances["lista_usuarios_gtae"]

# Algoritmo de asignación de cuentas automáticas para operadores
for admin in lista_admins_reales:
    if admin != "SIN ASIGNAR":
        partes = admin.split()
        apellido_base = partes[0].replace(".", "").lower()
        
        if apellido_base not in USR:
            USR[apellido_base] = {"nom": admin, "pin": "2026", "rol": "user"}
        else:
            if USR[apellido_base]["nom"] != admin:
                if len(partes) > 1:
                    inicial_nombre = partes[1].replace(".", "").lower()
                    variante = f"{apellido_base}{inicial_nombre}"
                else:
                    variante = f"{apellido_base}2"
                
                contador = 2
                while variante in USR and USR[variante]["nom"] != admin:
                    variante = f"{apellido_base}{contador}"
                    contador += 1
                    
                USR[variante] = {"nom": admin, "pin": "2026", "rol": "user"}

# ==============================================================================
# --- 2. INYECCIÓN DE ESTILOS CSS INSTITUCIONALES ---
# ==============================================================================
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC !important; }
    
    .login-container-gtae {
        max-width: 380px;
        margin: 40px auto 10px auto !important;
        text-align: center;
    }
    
    .login-title-gtae {
        color: #0B2545 !important;
        font-size: 26px !important;
        font-weight: 800 !important;
        margin-top: 15px !important;
        margin-bottom: 25px !important;
        text-align: center;
    }

    div[data-testid="stTextInput"] {
        max-width: 380px !important;
        margin: 0 auto 15px auto !important;
    }

    div[data-testid="stButton"] button {
        max-width: 380px !important;
        margin: 10px auto 0 auto !important;
        background: #134074 !important;
        color: #FFFFFF !important; 
        border: 1px solid #134074 !important;
        border-radius: 6px !important; 
        font-weight: bold !important;
        width: 100% !important; 
        height: 44px;
        font-size: 15px !important;
        transition: all 0.3s ease;
    }
    div[data-testid="stButton"] button:hover { 
        background: #1E40AF !important; 
        border-color: #1E40AF !important; 
    }
    
    [data-testid="stSidebar"] { background-color: #0B2545 !important; min-width: 320px !important; }
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] h3 { 
        color: #FFFFFF !important; 
        font-weight: 700 !important; 
        font-size: 15px !important;
    }
    
    div[data-baseweb="select"] li span, div[data-baseweb="select"] div { color: #1E293B !important; }
    
    [data-testid="stSidebar"] button {
        background: #134074 !important;
        color: #FFFFFF !important; 
        border: 1px solid #134074 !important;
        border-radius: 6px !important; 
        font-weight: bold !important;
        width: 100% !important; 
        height: 42px; 
        transition: all 0.3s ease;
    }
    [data-testid="stSidebar"] button:hover { background: #1E40AF !important; border-color: #1E40AF !important; }
    
    div.metric-premium-card {
        background-color: #FFFFFF !important; 
        border-left: 6px solid #134074 !important; 
        padding: 18px !important;
        border-radius: 8px !important; 
        box-shadow: 0px 4px 15px rgba(0,0,0,0.06) !important; 
        margin-bottom: 12px !important;
    }
    
    .stExpander {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        box-shadow: 0px 3px 10px rgba(0,0,0,0.02) !important;
        margin-bottom: 12px !important;
    }
    
    .main-title-gtae {
        color: #0B2545 !important;
        font-size: 30px !important;
        font-weight: 800 !important;
        margin-bottom: 5px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- AUTENTICACIÓN INSTITUCIONAL ---
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.markdown('<div class="login-container-gtae">', unsafe_allow_html=True)
    if os.path.exists(LOGO):
        col_izq, col_centro, col_der = st.columns([1.2, 1, 1.2])
        with col_centro:
            st.image(LOGO, use_container_width=True)
            
    st.markdown('<div class="login-title-gtae">Acceso Sistema GTAE</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    u = st.text_input("Usuario:", key="input_user_login").strip().lower()
    p = st.text_input("PIN de Seguridad:", type="password", key="input_pin_login").strip()
    
    if st.button("Ingresar al Monitor Operativo", key="button_submit_login"):
        if u in USR and USR[u]["pin"] == p:
            st.session_state.user = USR[u]
            st.rerun()
        else:
            st.error("Credenciales incorrectas.")
            
    st.stop()

# ==============================================================================
# --- 3. CARGA DE RECURSOS DEL PAC ---
# ==============================================================================
@st.cache_data
def load_data():
    px = ["1. Certificación Pertenencia/Existencia (Anexo A/B)", "2. Informe Borrador y Control Previo", "3. Subsanación de observaciones", "4. Informe de Necesidad RESERVADO al Jefe CMP", "5. Estudio de Mercado (Min. 3 proformas - Anexo I)", "6. Suscripción de TDRs y parámetros de experiencia", "7. Solicitud de listado de oferentes a DIRCOP", "8. Autorización de Invitación por Jefe CMP", "9. Invitación por Correo Institucional (Anexo J)", "10. Entrega de TDRs contra manifestación de interés", "11. Informe de Inteligencia Protectiva (Oferentes)", "12. Evaluación de Comisión (Anexo N)", "13. Elaboración de Formulario de Requerimiento (Anexo P)", "14. Certificado de Cumplimiento y Presupuestaria", "15. Resolución de Inicio y Aprobación de Pliegos", "16. Adjudicación y Suscripción del Contrato"]
    inf = ["1. Certificación Pertenencia/Existencia", "2. Control Previo e Informe Borrador (DIRCOP)", "3. Informe de Necesidad RESERVADO al CAF", "4. Autorización de la Coordinación Adm. Financiera", "5. Invitación RESERVADA (RUC/CPC habilitado)", "6. Recepción de propuestas (Reglas de Participación)", "7. Informe de Inteligencia Protectiva", "8. Razón de Proformas (DIRCOP - Anexo S)", "9. Selección de Proveedor y Det. Presupuesto (Anexo Q)", "10. Formulario de Cumplimiento Etapa Preparatoria (Anexo T)", "11. Obtención de Certificación Presupuestaria", "12. Declaración Juramentada del Oferente (Anexo U)", "13. Elaboración de Orden de Compra sumillada", "14. Legalización por el CAF y Execution"]
    ext = ["1. Certificación Pertenencia/Existencia de bienes", "2. Revisión técnica/financiera del Informe Borrador", "3. Informe de Necesidad RESERVADO (Exclusividad)", "4. Estudio de Mercado con proformas vigentes", "5. Búsqueda y listado de proveedores internacionales", "6. Invitación formal por Mail Institucional (Anexo J)", "7. Evaluación Comisión Selección (Anexo O)", "8. Formulario de Requerimiento (Anexo P)", "9. Certificado de Cumplimiento y Presupuestaria", "10. Solicitud de inicio al Jefe CMP", "11. Resolución Fundamentada de Inicio", "12. Suscripción de Orden de Compra/Servicio", "13. Ejecución (Prácticas Internacionales)"]
    
    p1 = pd.read_excel(PAC, sheet_name='PUBLICADO', skiprows=3)
    p2 = pd.read_excel(PAC, sheet_name='RESERVADO', skiprows=4)
    pt = pd.concat([p1, p2], ignore_index=True).dropna(subset=['DETALLE DEL PRODUCTO (Descripción de la contratación)'])
    pt.columns = pt.columns.str.strip().str.upper()
    pt['COSTO TOTAL'] = pd.to_numeric(pt['COSTO TOTAL'].astype(str).str.replace(',', '').str.replace('$', ''), errors='coerce').fillna(0)
    
    return px, inf, ext, pt

px_s, inf_s, ext_s, df_pac = load_data()

# --- BARRA LATERAL ---
st.sidebar.image(LOGO if os.path.exists(LOGO) else None, width=100)
st.sidebar.markdown(f"### 👤 **Usuario:** {st.session_state.user['nom']}")
st.sidebar.markdown(f"### 🪖 **Rol:** {st.session_state.user['rol'].upper()}")

if GITHUB_TOKEN and GITHUB_REPO:
    st.sidebar.success("🔒 Almacenamiento Permanente Activado")
else:
    st.sidebar.warning("⚠️ Modo Local")

dep_sel = st.sidebar.selectbox("Visualizar Departamento:", ["LOGÍSTICA", "OPERACIONES", "OTRAS DEPENDENCIAS"])
cuat_sel = st.sidebar.radio("Seleccione Cuatrimestre:", ["C1", "C2", "C3"])
cuat_mapeo = {"C1": "1er Cuatrimestre", "C2": "2do Cuatrimestre", "C3": "3er Cuatrimestre"}
cuat_filtro_texto = cuat_mapeo[cuat_sel]

# ==============================================================================
# --- 4. ENGINE DE GENERACIÓN DE REPORTE PDF CON FILTRADO DE SEGURIDAD ---
# ==============================================================================
def generar_pdf_oficial(inspector, df_items, cuat, avances, v_e_a, v_t_a, depto, rol_usuario, nombre_usuario):
    pdf = FPDF(orientation='L', unit='mm', format='A4') 
    pdf.add_page()
    
    if os.path.exists(LOGO): pdf.image(LOGO, 12, 10, 24)
    
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.set_font("Helvetica", '', 8)
    pdf.cell(0, 5, f"Fecha de reporte: {fecha_actual}", ln=True, align='R')
    
    pdf.set_font("Helvetica", 'B', 13); pdf.set_text_color(11, 37, 69)
    pdf.cell(0, 6, 'FUERZA AEREA ECUATORIANA', ln=True, align='C')
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(0, 5, 'GRUPO DE TRANSPORTE AEREO ESPECIAL (GTAE)', ln=True, align='C')
    pdf.cell(0, 5, f'DEPARTAMENTO DE {depto}', ln=True, align='C')
    pdf.ln(6)
    
    pdf.set_fill_color(11, 37, 69); pdf.set_text_color(255, 255, 255); pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(0, 8, f"REPORTE TECNICO DE EJECUCION PRESUPUESTARIA - {cuat.upper()}", 0, 1, 'C', True)
    pdf.ln(4)
    
    pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", 'B', 9)
    pdf.cell(0, 6, "1. CONSOLIDADO FINANCIERO DEL PERIOSO:", ln=True)
    pdf.set_font("Helvetica", '', 9); pdf.set_fill_color(245, 247, 250)
    pdf.cell(135, 7, f" Presupuesto Planificado Cuatrimestre: ${v_t_a:,.2f}", 1, 0, 'L', True)
    pdf.cell(142, 7, f" Devengado Real Cuatrimestre: ${v_e_a:,.2f}", 1, 1, 'L', True)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", 'B', 9)
    pdf.cell(0, 6, "2. DETALLE DE PROCESOS EN EJECUCION:", ln=True)
    
    pdf.set_fill_color(20, 50, 90); pdf.set_text_color(255, 255, 255); pdf.set_font("Helvetica", 'B', 8)
    pdf.cell(100, 6, "Objeto de Contratacion", 1, 0, 'C', True)
    pdf.cell(35, 6, "Administrador", 1, 0, 'C', True)
    pdf.cell(25, 6, "Monto Real", 1, 0, 'C', True)
    pdf.cell(57, 6, "Fase Actual", 1, 0, 'C', True)
    pdf.cell(60, 6, "Ubicacion / Nota de Seguimiento", 1, 1, 'C', True)
    
    pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", '', 7)
    col_desc_pdf = next((c for c in df_items.columns if "DETALLE" in c.upper()), None)
    
    if col_desc_pdf:
        for ix, r in df_items.iterrows():
            item_depto = avances.get(f"depto_{r.name}", "LOGÍSTICA")
            item_cuat = avances.get(f"cuat_{r.name}", "1er Cuatrimestre")
            
            v_gen = avances.get(f"eq_gen_{r.name}", "SIN ASIGNAR").upper().strip()
            v_seg = avances.get(f"eq_seg_{r.name}", "SIN ASIGNAR").upper().strip()
            v_adm = avances.get(f"eq_adm_{r.name}", "SIN ASIGNAR").upper().strip()
            u_nom = nombre_usuario.upper().strip()
            
            if rol_usuario not in ['admin', 'supervisor'] and u_nom not in [v_gen, v_seg, v_adm]:
                continue
                
            if item_depto == depto and item_cuat == cuat:
                if avances.get(f"estado_op_{r.name}", "ACTIVO") in ["ACTIVO", "🟢 ACTIVO"]:
                    obj_t = str(avances.get(f"name_{r.name}", r[col_desc_pdf]))[:60]
                    adm_t = str(v_adm)
                    monto_t = float(avances.get(f"monto_{r.name}", float(r['COSTO TOTAL'])))
                    fase_t = str(avances.get(f"s_{r.name}", "Pendiente"))[:35]
                    nota_t = str(avances.get(f"nota_{r.name}", "Sin novedad"))[:40]
                    
                    pdf.cell(100, 6, f" {obj_t}", 1, 0, 'L')
                    pdf.cell(35, 6, f" {adm_t}", 1, 0, 'C')
                    pdf.cell(25, 6, f" ${monto_t:,.2f}", 1, 0, 'R')
                    pdf.cell(57, 6, f" {fase_t}", 1, 0, 'L')
                    pdf.cell(60, 6, f" {nota_t}", 1, 1, 'L')

    for i, np in enumerate(avances.get("procesos_nuevos", [])):
        m_depto = avances.get(f"nuevo_depto_{i}", np.get('departamento', 'LOGÍSTICA'))
        m_cuat = avances.get(f"nuevo_cuat_{i}", np['cuatrimestre'])
        
        v_gen = avances.get(f"nuevo_eq_gen_{i}", "SIN ASIGNAR").upper().strip()
        v_seg = avances.get(f"nuevo_eq_seg_{i}", "SIN ASIGNAR").upper().strip()
        v_adm = avances.get(f"nuevo_eq_adm_{i}", "SIN ASIGNAR").upper().strip()
        u_nom = nombre_usuario.upper().strip()
        
        if rol_usuario not in ['admin', 'supervisor'] and u_nom not in [v_gen, v_seg, v_adm]:
            continue
            
        if m_depto == depto and m_cuat == cuat:
            if avances.get(f"nuevo_estado_op_{i}", "ACTIVO") in ["ACTIVO", "🟢 ACTIVO"]:
                obj_m = str(avances.get(f"nuevo_name_{i}", np['objeto']))[:60]
                adm_m = str(v_adm)
                monto_m = float(avances.get(f"nuevo_monto_{i}", float(np['monto'])))
                fase_m = str(avances.get(f"nuevo_s_{i}", "1. Certificación Pertenencia/Existencia"))[:35]
                nota_m = str(avances.get(f"nuevo_nota_{i}", "Sin novedad"))[:40]
                
                pdf.cell(100, 6, f" [MANUAL] {obj_m}", 1, 0, 'L')
                pdf.cell(35, 6, f" {adm_m}", 1, 0, 'C')
                pdf.cell(25, 6, f" ${monto_m:,.2f}", 1, 0, 'R')
                pdf.cell(57, 6, f" {fase_m}", 1, 0, 'L')
                pdf.cell(60, 6, f" {nota_m}", 1, 1, 'L')

    pdf.ln(12)
    pdf.set_font("Helvetica", 'B', 8)
    pdf.cell(135, 5, "ELABORADO POR:", 0, 0, 'L')
    pdf.cell(142, 5, "REVISADO Y APROBADO POR:", 0, 1, 'L')
    pdf.ln(10)
    pdf.cell(135, 4, "____________________________________", 0, 0, 'L')
    pdf.cell(142, 4, "____________________________________", 0, 1, 'L')
    pdf.cell(135, 4, f"Econ. {inspector}", 0, 0, 'L')
    pdf.cell(142, 4, f"JEFE DEL DEPARTAMENTO DE {depto} GTAE", 0, 1, 'L')
    
    return pdf.output(dest='S').encode('latin1', errors='ignore')

# ==============================================================================
# --- 5. MOTOR MATEMÁTICO ADAPTADO AL FILTRO DE SEGURIDAD POR OPERADOR ---
# ==============================================================================
df_visualizacion = df_pac.copy()

v_t_c, v_e_c = 0.0, 0.0
v_t_a, v_e_a = 0.0, 0.0

for idx, row in df_visualizacion.iterrows():
    depto_p = st.session_state.avances.get(f"depto_{row.name}", "LOGÍSTICA")
    cuat_p = st.session_state.avances.get(f"cuat_{row.name}", "1er Cuatrimestre")
    monto_p = float(st.session_state.avances.get(f"monto_{row.name}", float(row['COSTO TOTAL'])))
    avance_p = st.session_state.avances.get(f"s_{row.name}", "Pendiente")
    
    v_gen = st.session_state.avances.get(f"eq_gen_{row.name}", "SIN ASIGNAR").upper().strip()
    v_seg = st.session_state.avances.get(f"eq_seg_{row.name}", "SIN ASIGNAR").upper().strip()
    v_adm = st.session_state.avances.get(f"eq_adm_{row.name}", "SIN ASIGNAR").upper().strip()
    u_nom = st.session_state.user['nom'].upper().strip()
    
    if st.session_state.user['rol'] not in ['admin', 'supervisor'] and u_nom not in [v_gen, v_seg, v_adm]:
        continue
        
    if depto_p == dep_sel and proceso_esta_activo(row.name, es_nuevo=False):
        v_t_a += monto_p
        if "DEVENGADO" in str(avance_p).upper() or "FINALIZADO" in str(avance_p).upper():
            v_e_a += monto_p
            
        if cuat_p == cuat_filtro_texto:
            v_t_c += monto_p
            if "DEVENGADO" in str(avance_p).upper() or "FINALIZADO" in str(avance_p).upper():
                v_e_c += monto_p

for i, np in enumerate(st.session_state.avances["procesos_nuevos"]):
    depto_p = st.session_state.avances.get(f"nuevo_depto_{i}", np.get('departamento', 'LOGÍSTICA'))
    cuat_p = st.session_state.avances.get(f"nuevo_cuat_{i}", np['cuatrimestre'])
    monto_p = float(st.session_state.avances.get(f"nuevo_monto_{i}", float(np['monto'])))
    avance_p = st.session_state.avances.get(f"nuevo_s_{i}", "1. Certificación Pertenencia/Existencia")
    
    v_gen = st.session_state.avances.get(f"nuevo_eq_gen_{i}", "SIN ASIGNAR").upper().strip()
    v_seg = st.session_state.avances.get(f"nuevo_eq_seg_{i}", "SIN ASIGNAR").upper().strip()
    v_adm = st.session_state.avances.get(f"nuevo_eq_adm_{i}", "SIN ASIGNAR").upper().strip()
    u_nom = st.session_state.user['nom'].upper().strip()
    
    if st.session_state.user['rol'] not in ['admin', 'supervisor'] and u_nom not in [v_gen, v_seg, v_adm]:
        continue
        
    if depto_p == dep_sel and proceso_esta_activo(i, es_nuevo=True):
        v_t_a += monto_p
        if "DEVENGADO" in str(avance_p).upper() or "FINALIZADO" in str(avance_p).upper():
            v_e_a += monto_p
            
        if cuat_p == cuat_filtro_texto:
            v_t_c += monto_p
            if "DEVENGADO" in str(avance_p).upper() or "FINALIZADO" in str(avance_p).upper():
                v_e_c += monto_p

# ==============================================================================
# --- 6. PANEL CENTRAL GRÁFICO ---
# ==============================================================================
st.markdown('<div class="main-title-gtae">🛫 Monitor Operativo de Control Presupuestario GTAE</div>', unsafe_allow_html=True)
st.markdown(f"Módulo de gestión técnica — Departamento: **{dep_sel}**")
st.markdown("---")

tab_cuat, tab_anual = st.tabs([f"📊 Mis Métricas del Periodo ({cuat_filtro_texto})", "🌍 Mi Consolidado General Anual 2026"])

with tab_cuat:
    col_met_c, col_pie_c = st.columns([1, 1])
    with col_met_c:
        st.markdown('<div class="metric-premium-card">', unsafe_allow_html=True)
        st.metric(f"Planificado Asignado", f"${v_t_c:,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="metric-premium-card">', unsafe_allow_html=True)
        st.metric("Devengado Logrado", f"${v_e_c:,.2f}", delta=f"{((v_e_c/v_t_c)*100) if v_t_c > 0 else 0:.2f}% Ejecutado")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_pie_c:
        monto_pend_c = max(0.0, v_t_c - v_e_c)
        if v_t_c > 0:
            fig_c = go.Figure(data=[go.Pie(labels=['Devengado Asignado', 'Pendiente'], values=[v_e_c, monto_pend_c], hole=.4, marker=dict(colors=['#1E3A8A', '#EF4444']))])
            fig_c.update_layout(margin=dict(t=20, b=0, l=0, r=0), height=170, showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_c, use_container_width=True)
        else:
            st.info(f"No registra procesos asignados en este periodo.")

with tab_anual:
    col_met_a, col_pie_a = st.columns([1, 1])
    with col_met_a:
        st.markdown('<div class="metric-premium-card">', unsafe_allow_html=True)
        st.metric(f"Monto Anual Total Asignado", f"${v_t_a:,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="metric-premium-card">', unsafe_allow_html=True)
        st.metric("Total Devengado", f"${v_e_a:,.2f}", delta=f"{((v_e_a/v_t_a)*100) if v_t_a > 0 else 0:.2f}% Eficiencia Global")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_pie_a:
        monto_pend_a = max(0.0, v_t_a - v_e_a)
        if v_t_a > 0:
            fig_a = go.Figure(data=[go.Pie(labels=['Devengado', 'Pendiente Anual'], values=[v_e_a, monto_pend_a], hole=.4, marker=dict(colors=['#10B981', '#F59E0B']))])
            fig_a.update_layout(margin=dict(t=20, b=0, l=0, r=0), height=170, showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_a, use_container_width=True)
        else:
            st.info(f"No cuenta con fondos asignados bajo su responsabilidad para este año.")

# Panel de Administración Integrado (Solo Administradores/Supervisores manejan altas e inyección inicial)
if st.session_state.user['rol'] in ['admin', 'supervisor']:
    with st.expander("🛠️ Panel de Administración (Registrar Personal y Nuevos Procesos Extra-PAC)"):
        t_pers, t_proc = st.tabs(["👥 Gestión de Personal", "➕ Incluir Nuevo Proceso Manual"])
        with t_pers:
            col_lista, col_ingreso = st.columns([1, 1])
            with col_lista:
                st.markdown("### 📋 Personal registrado")
                st.dataframe({"Grado y Nombre Completo": lista_admins_reales}, use_container_width=True, hide_index=True)
            with col_ingreso:
                st.markdown("### ➕ Registrar Operador")
                with st.form("form_nuevo_usuario", clear_on_submit=True):
                    nuevo_nombre_raw = st.text_input("Grado y Apellido (Ej: SGOS. CONTERON G.):")
                    if st.form_submit_button("Dar de Alta"):
                        if nuevo_nombre_raw.strip():
                            st.session_state.avances["lista_usuarios_gtae"].append(nuevo_nombre_raw.upper().strip())
                            st.session_state.avances["lista_usuarios_gtae"] = sorted(list(set(st.session_state.avances["lista_usuarios_gtae"])))
                            guardar_base_datos(st.session_state.avances)
                            st.success("✅ Personal Registrado.")
                            st.rerun()
        with t_proc:
            st.markdown("### 📝 Datos del Nuevo Proceso Extra-PAC")
            with st.form("form_nuevo_proceso_manual", clear_on_submit=True):
                n_objeto = st.text_input("Objeto / Detalle de Contratación:")
                n_partida = st.text_input("Partida Presupuestaria:")
                n_monto = st.number_input("Costo Total Planificado (USD):", min_value=0.0, step=100.0, format="%.2f")
                n_tipo = st.selectbox("Tipo de Trámite:", ["ÍNFIMA CUANTÍA", "PUBLICACIÓN (PAC)", "EXTRANJERO / EXCLUSIVIDAD"])
                n_depto = st.selectbox("Asignar a Departamento:", ["LOGÍSTICA", "OPERACIONES", "OTRAS DEPENDENCIAS"])
                n_cuat = st.selectbox("Asignar a Cuatrimestre:", ["1er Cuatrimestre", "2do Cuatrimestre", "3er Cuatrimestre"])
                if st.form_submit_button("Inyectar Proceso en Monitor"):
                    if n_objeto.strip() and n_partida.strip():
                        st.session_state.avances["procesos_nuevos"].append({
                            "objeto": n_objeto.upper().strip(), 
                            "partida": n_partida.upper().strip(), 
                            "monto": n_monto, 
                            "tipo": n_tipo, 
                            "departamento": n_depto,
                            "cuatrimestre": n_cuat
                        })
                        guardar_base_datos(st.session_state.avances)
                        st.success("🚀 Proceso inyectado con éxito.")
                        st.rerun()

# ==============================================================================
# --- 7. DISPLAY DE FILTRADO Y EXPANDERS INTERACTIVOS (EDICIÓN PARA ENCARGADOS) ---
# ==============================================================================
st.markdown("---")
st.markdown("### 🔍 Buscador de Procesos en Ejecución")
query = st.text_input("", placeholder="Ej: Repuestos, Motores, Ferretería...", label_visibility="collapsed")

def sync_estado(k):
    st.session_state.avances[k] = st.session_state[k]
    guardar_base_datos(st.session_state.avances)

opciones_personal = [admin.upper().strip() for admin in lista_admins_reales]
if "SIN ASIGNAR" not in opciones_personal: opciones_personal.insert(0, "SIN ASIGNAR")

# --- A. DESPLIEGUE DE PROCESOS NUEVOS MANUALES ---
for i, np in enumerate(st.session_state.avances["procesos_nuevos"]):
    depto_p = st.session_state.avances.get(f"nuevo_depto_{i}", np.get('departamento', 'LOGÍSTICA'))
    cuat_p = st.session_state.avances.get(f"nuevo_cuat_{i}", np['cuatrimestre'])
    
    if depto_p != dep_sel: continue
    if query.strip():
        if query.lower() not in np['objeto'].lower(): continue
    else:
        if cuat_p != cuat_filtro_texto: continue
        
    v_gen = st.session_state.avances.get(f'nuevo_eq_gen_{i}', "SIN ASIGNAR").upper().strip()
    v_seg = st.session_state.avances.get(f'nuevo_eq_seg_{i}', "SIN ASIGNAR").upper().strip()
    v_adm = st.session_state.avances.get(f'nuevo_eq_adm_{i}', "SIN ASIGNAR").upper().strip()
    u_nom = st.session_state.user['nom'].upper().strip()
    
    if st.session_state.user['rol'] not in ['admin', 'supervisor'] and u_nom not in [v_gen, v_seg, v_adm]:
        continue
        
    es_activo = st.session_state.avances.get(f"nuevo_estado_op_{i}", "ACTIVO") in ["ACTIVO", "🟢 ACTIVO"]
    monto_t = float(st.session_state.avances.get(f"nuevo_monto_{i}", float(np['monto'])))
    puntos_fases = inf_s if "INFIMA" in np['tipo'] else (ext_s if "EXTRANJERO" in np['tipo'] else px_s)
    
    titulo = f"🔸 [MANUAL] {np['objeto']} - ${monto_t:,.2f} ({cuat_p})" if es_activo else f"❌ [ANULADO] {np['objeto']}"
    with st.expander(titulo):
        if st.session_state.user['rol'] in ['admin', 'supervisor']:
            st.radio("Estado Disponibilidad:", ["ACTIVO", "CANCELADO"], index=0 if es_activo else 1, key=f"nuevo_estado_op_{i}", on_change=sync_estado, args=(f"nuevo_estado_op_{i}",), horizontal=True)
        if es_activo:
            t1, t2, t3 = st.tabs(["📋 Detalles y Equipo", "📍 Avance", "📂 Expediente"])
            with t1:
                # Modificable por cualquier encargado con acceso al proceso
                st.text_input("Objeto:", value=st.session_state.avances.get(f"nuevo_name_{i}", np['objeto']), key=f"nuevo_name_{i}", on_change=sync_estado, args=(f"nuevo_name_{i}",))
                
                st.markdown("##### 💵 Control y Ejecución Financiera")
                c_asig, c_cert, c_comp, c_dev = st.columns(4)
                with c_asig:
                    val_asignado = st.number_input("Valor Asignado (Planificado):", value=monto_t, key=f"nuevo_monto_{i}", on_change=sync_estado, args=(f"nuevo_monto_{i}",), format="%.2f")
                with c_cert:
                    val_certificado = st.number_input("Valor Certificado:", value=float(st.session_state.avances.get(f"nuevo_val_cert_{i}", 0.0)), key=f"nuevo_val_cert_{i}", on_change=sync_estado, args=(f"nuevo_val_cert_{i}",), format="%.2f")
                with c_comp:
                    val_comprometido = st.number_input("Valor Comprometido:", value=float(st.session_state.avances.get(f"nuevo_val_comp_{i}", 0.0)), key=f"nuevo_val_comp_{i}", on_change=sync_estado, args=(f"nuevo_val_comp_{i}",), format="%.2f")
                with c_dev:
                    val_devengado = st.number_input("Valor Devengado:", value=float(st.session_state.avances.get(f"nuevo_val_dev_{i}", 0.0)), key=f"nuevo_val_dev_{i}", on_change=sync_estado, args=(f"nuevo_val_dev_{i}",), format="%.2f")
                
                saldo_pendiente = max(0.0, val_asignado - val_devengado)
                st.info(f"📊 **Saldo Pendiente (Planificado - Devengado):** ${saldo_pendiente:,.2f}")
                
                st.markdown("##### 📑 Trazabilidad de Documentos Oficiales")
                c_doc1, c_doc2, c_doc3, c_doc4 = st.columns(4)
                with c_doc1:
                    st.text_input("Nro. Certificación Presupuestaria:", value=st.session_state.avances.get(f"nuevo_doc_cert_{i}", ""), key=f"nuevo_doc_cert_{i}", on_change=sync_estado, args=(f"nuevo_doc_cert_{i}",), placeholder="Ej: CP-012")
                with c_doc2:
                    st.text_input("Nro. Compromiso de Pago:", value=st.session_state.avances.get(f"nuevo_doc_comp_{i}", ""), key=f"nuevo_doc_comp_{i}", on_change=sync_estado, args=(f"nuevo_doc_comp_{i}",), placeholder="Ej: CP-548")
                with c_doc3:
                    st.text_input("Nro. Orden de Gasto:", value=st.session_state.avances.get(f"nuevo_doc_gasto_{i}", ""), key=f"nuevo_doc_gasto_{i}", on_change=sync_estado, args=(f"nuevo_doc_gasto_{i}",), placeholder="Ej: OG-105")
                with c_doc4:
                    st.text_input("Nro. Transferencia / CUR:", value=st.session_state.avances.get(f"nuevo_doc_trans_{i}", ""), key=f"nuevo_doc_trans_{i}", on_change=sync_estado, args=(f"nuevo_doc_trans_{i}",), placeholder="Ej: SPI-98541")
                    
                st.markdown("##### 👥 Responsables del Proceso")
                cp, c1, c2, c3 = st.columns(4)
                with cp: st.text_input("Partida:", value=st.session_state.avances.get(f"nuevo_part_{i}", np['partida']), key=f"nuevo_part_{i}", on_change=sync_estado, args=(f"nuevo_part_{i}",))
                with c1: st.selectbox("Generar Necesidad:", opciones_personal, index=opciones_personal.index(v_gen) if v_gen in opciones_personal else 0, key=f"nuevo_eq_gen_{i}", on_change=sync_estado, args=(f"nuevo_eq_gen_{i}",))
                with c2: st.selectbox("Seguimiento FAE:", opciones_personal, index=opciones_personal.index(v_seg) if v_seg in opciones_personal else 0, key=f"nuevo_eq_seg_{i}", on_change=sync_estado, args=(f"nuevo_eq_seg_{i}",))
                with c3: st.selectbox("Administrador:", opciones_personal, index=opciones_personal.index(v_adm) if v_adm in opciones_personal else 0, key=f"nuevo_eq_adm_{i}", on_change=sync_estado, args=(f"nuevo_eq_adm_{i}",))
            with t2:
                st.select_slider("Fase actual:", options=puntos_fases, value=st.session_state.avances.get(f"nuevo_s_{i}", puntos_fases[0]), key=f"nuevo_s_{i}", on_change=sync_estado, args=(f"nuevo_s_{i}",))
                st.text_input("📍 Ubicación actual / Nota de Seguimiento:", value=st.session_state.avances.get(f"nuevo_nota_{i}", "Sin novedad"), key=f"nuevo_nota_{i}", on_change=sync_estado, args=(f"nuevo_nota_{i}",))
                
                if st.session_state.user['rol'] in ['admin', 'supervisor']:
                    st.selectbox("Mover Cuatrimestre:", ["1er Cuatrimestre", "2do Cuatrimestre", "3er Cuatrimestre"], index=["1er Cuatrimestre", "2do Cuatrimestre", "3er Cuatrimestre"].index(cuat_p), key=f"nuevo_cuat_{i}", on_change=sync_estado, args=(f"nuevo_cuat_{i}",))
                    st.selectbox("Reasignar Departamento:", ["LOGÍSTICA", "OPERACIONES", "OTRAS DEPENDENCIAS"], index=["LOGÍSTICA", "OPERACIONES", "OTRAS DEPENDENCIAS"].index(depto_p), key=f"nuevo_depto_{i}", on_change=sync_estado, args=(f"nuevo_depto_{i}",))
            with t3:
                link_guardado = st.session_state.avances.get(f"nuevo_lnk_nube_{i}", URL_BASE_FAE)
                st.text_input("URL Carpeta Específica:", value=link_guardado, key=f"nuevo_lnk_nube_{i}", on_change=sync_estado, args=(f"nuevo_lnk_nube_{i}",))
                st.link_button("📥 ABRIR EXPEDIENTE EN REPOSITORIO INSTITUCIONAL", url=link_guardado, use_container_width=True)

# --- B. DESPLIEGUE DE PROCESOS DEL PAC EXCEL ---
col_desc = next((c for c in df_visualizacion.columns if "DETALLE" in c.upper()), None)
if col_desc:
    df_f = df_visualizacion.copy()
    if query.strip():
        df_f = df_f[df_f[col_desc].str.contains(query, case=False, na=False)]

    for ix, r in df_f.iterrows():
        depto_p = st.session_state.avances.get(f"depto_{r.name}", "LOGÍSTICA")
        cuat_p = st.session_state.avances.get(f"cuat_{r.name}", "1er Cuatrimestre")
        
        if depto_p != dep_sel: continue
        if not query.strip():
            if cuat_p != cuat_filtro_texto: continue
            
        v_gen = st.session_state.avances.get(f"eq_gen_{r.name}", "SIN ASIGNAR").upper().strip()
        v_seg = st.session_state.avances.get(f"eq_seg_{r.name}", "SIN ASIGNAR").upper().strip()
        v_adm = st.session_state.avances.get(f"eq_adm_{r.name}", "SIN ASIGNAR").upper().strip()
        u_nom = st.session_state.user['nom'].upper().strip()
        
        if st.session_state.user['rol'] not in ['admin', 'supervisor'] and u_nom not in [v_gen, v_seg, v_adm]:
            continue
            
        proc_text = str(r.get('PROCEDIMIENTO SUGERERO (SON LOS PROCEDIMIENTOS DE CONTRATACIÓN)', '')).upper()
        puntos = inf_s if "INFIMA" in proc_text else (ext_s if "EXTRANJERO" in proc_text or "PEX" in proc_text else px_s)
        es_activo = st.session_state.avances.get(f"estado_op_{r.name}", "ACTIVO") in ["ACTIVO", "🟢 ACTIVO"]
        monto_tarjeta = float(st.session_state.avances.get(f"monto_{r.name}", float(r['COSTO TOTAL'])))
        
        titulo_tarjeta = f"🔹 {r[col_desc]} - ${monto_tarjeta:,.2f} ({cuat_p})" if es_activo else f"❌ [ANULADO] {r[col_desc]}"
        with st.expander(titulo_tarjeta):
            if st.session_state.user['rol'] in ['admin', 'supervisor']:
                st.radio("Planificación PAC:", ["ACTIVO", "CANCELADO / NO SE DA"], index=0 if es_activo else 1, key=f"estado_op_{r.name}", on_change=sync_estado, args=(f"estado_op_{r.name}",), horizontal=True)
            if es_activo:
                t1, t2, t3 = st.tabs(["📋 Detalles y Equipo", "📍 Avance", "📂 Expediente"])
                with t1:
                    # Campos completamente liberados para modificación directa de los encargados
                    st.text_input("Objeto de Contratación:", value=st.session_state.avances.get(f"name_{r.name}", str(r.get(col_desc, 'S/N'))), key=f"name_{r.name}", on_change=sync_estado, args=(f"name_{r.name}",))
                    
                    st.markdown("##### 💵 Control y Ejecución Financiera")
                    c_asig, c_cert, c_comp, c_dev = st.columns(4)
                    with c_asig:
                        val_asignado = st.number_input("Valor Asignado (Planificado):", value=monto_tarjeta, key=f"monto_{r.name}", on_change=sync_estado, args=(f"monto_{r.name}",), format="%.2f")
                    with c_cert:
                        val_certificado = st.number_input("Valor Certificado:", value=float(st.session_state.avances.get(f"val_cert_{r.name}", 0.0)), key=f"val_cert_{r.name}", on_change=sync_estado, args=(f"val_cert_{r.name}",), format="%.2f")
                    with c_comp:
                        val_comprometido = st.number_input("Valor Comprometido:", value=float(st.session_state.avances.get(f"val_comp_{r.name}", 0.0)), key=f"val_comp_{r.name}", on_change=sync_estado, args=(f"val_comp_{r.name}",), format="%.2f")
                    with c_dev:
                        val_devengado = st.number_input("Valor Devengado:", value=float(st.session_state.avances.get(f"val_dev_{r.name}", 0.0)), key=f"val_dev_{r.name}", on_change=sync_estado, args=(f"val_dev_{r.name}",), format="%.2f")
                    
                    saldo_pendiente = max(0.0, val_asignado - val_devengado)
                    st.info(f"📊 **Saldo Pendiente (Planificado - Devengado):** ${saldo_pendiente:,.2f}")
                    
                    st.markdown("##### 📑 Trazabilidad de Documentos Oficiales")
                    c_doc1, c_doc2, c_doc3, c_doc4 = st.columns(4)
                    with c_doc1:
                        st.text_input("Nro. Certificación Presupuestaria:", value=st.session_state.avances.get(f"doc_cert_{r.name}", ""), key=f"doc_cert_{r.name}", on_change=sync_estado, args=(f"doc_cert_{r.name}",), placeholder="Ej: CP-012")
                    with c_doc2:
                        st.text_input("Nro. Compromiso de Pago:", value=st.session_state.avances.get(f"doc_comp_{r.name}", ""), key=f"doc_comp_{r.name}", on_change=sync_estado, args=(f"doc_comp_{r.name}",), placeholder="Ej: CP-548")
                    with c_doc3:
                        st.text_input("Nro. Orden de Gasto:", value=st.session_state.avances.get(f"doc_gasto_{r.name}", ""), key=f"doc_gasto_{r.name}", on_change=sync_estado, args=(f"doc_gasto_{r.name}",), placeholder="Ej: OG-105")
                    with c_doc4:
                        st.text_input("Nro. Transferencia / CUR:", value=st.session_state.avances.get(f"doc_trans_{r.name}", ""), key=f"doc_trans_{r.name}", on_change=sync_estado, args=(f"doc_trans_{r.name}",), placeholder="Ej: SPI-98541")
                        
                    st.markdown("##### 👥 Responsables del Proceso")
                    cp, c1, c2, c3 = st.columns(4)
                    with cp: st.text_input("Partida:", value=st.session_state.avances.get(f"part_{r.name}", "S/N"), key=f"part_{r.name}", on_change=sync_estado, args=(f"part_{r.name}",))
                    with c1: st.selectbox("Generar Necesidad:", opciones_personal, index=opciones_personal.index(v_gen) if v_gen in opciones_personal else 0, key=f"eq_gen_{r.name}", on_change=sync_estado, args=(f"eq_gen_{r.name}",))
                    with c2: st.selectbox("Seguimiento FAE:", opciones_personal, index=opciones_personal.index(v_seg) if v_seg in opciones_personal else 0, key=f"eq_seg_{r.name}", on_change=sync_estado, args=(f"eq_seg_{r.name}",))
                    with c3: st.selectbox("Administrador:", opciones_personal, index=opciones_personal.index(v_adm) if v_adm in opciones_personal else 0, key=f"eq_adm_{r.name}", on_change=sync_estado, args=(f"eq_adm_{r.name}",))
                with t2:
                    st.select_slider("Fase:", options=puntos, value=st.session_state.avances.get(f"s_{r.name}", puntos[0]), key=f"s_{r.name}", on_change=sync_estado, args=(f"s_{r.name}",))
                    st.text_input("📍 Ubicación actual / Nota de Seguimiento:", value=st.session_state.avances.get(f"nota_{r.name}", "Sin novedad"), key=f"nota_{r.name}", on_change=sync_estado, args=(f"nota_{r.name}",))
                    
                    if st.session_state.user['rol'] in ['admin', 'supervisor']:
                        st.selectbox("Mover de Cuatrimestre:", ["1er Cuatrimestre", "2do Cuatrimestre", "3er Cuatrimestre"], index=["1er Cuatrimestre", "2do Cuatrimestre", "3er Cuatrimestre"].index(cuat_p), key=f"cuat_{r.name}", on_change=sync_estado, args=(f"cuat_{r.name}",))
                        st.selectbox("Transferir Departamento:", ["LOGÍSTICA", "OPERACIONES", "OTRAS DEPENDENCIAS"], index=["LOGÍSTICA", "OPERACIONES", "OTRAS DEPENDENCIAS"].index(depto_p), key=f"depto_{r.name}", on_change=sync_estado, args=(f"depto_{r.name}",))
                with t3:
                    link_guardado = st.session_state.avances.get(f"lnk_nube_{r.name}", URL_BASE_FAE)
                    st.text_input("URL Carpeta Específica del Trámite:", value=link_guardado, key=f"lnk_nube_{r.name}", on_change=sync_estado, args=(f"lnk_nube_{r.name}",))
                    st.link_button("📥 ABRIR EXPEDIENTE EN REPOSITORIO INSTITUCIONAL", url=link_guardado, use_container_width=True)

# --- REPORTE PDF SEPARADO ---
st.sidebar.markdown("---")
pdf_bytes = generar_pdf_oficial(st.session_state.user['nom'], df_visualizacion, cuat_filtro_texto, st.session_state.avances, v_e_c, v_t_c, dep_sel, st.session_state.user['rol'], st.session_state.user['nom'])
st.sidebar.download_button(label="📥 DESCARGAR REPORTE PDF", data=pdf_bytes, file_name=f"Reporte_{dep_sel}_{cuat_sel}.pdf", mime="application/pdf", use_container_width=True)

if st.sidebar.button("Cerrar Sesión Activa"):
    st.session_state.user = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("<div style='text-align: center; background-color: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px;'><p style='color: white; font-size: 11px; margin-bottom: 0;'>© 2026 Desarrollado por:</p><p style='color: #FFD700; font-size: 13px; font-weight: bold; margin-top: 5px;'>Econ. Geovanny Conterón</p><p style='color: #E3F2FD; font-size: 10px; font-style: italic;'>GTAE - FAE</p></div>", unsafe_allow_html=True)