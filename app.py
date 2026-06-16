import sys
import mock
# Parche de compatibilidad visual
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

# El sistema lee de forma invisible los datos desde la cabina de Streamlit sin exponerlos en el código
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

for admin in lista_admins_reales:
    if admin != "SIN ASIGNAR":
        username = admin.split()[0].replace(".", "").lower()
        if username not in USR:
            USR[username] = {"nom": admin, "pin": "2026", "rol": "user"}

# ==============================================================================
# --- 2. INYECCIÓN DE ESTILOS CSS INSTITUCIONALES (ALTA PRESENTACIÓN) ---
# ==============================================================================
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC !important; }
    
    /* Contenedor del Login Centrado */
    .login-wrapper {
        max-width: 420px;
        margin: 80px auto;
        background-color: #0B2545;
        padding: 35px;
        border-radius: 12px;
        box-shadow: 0px 10px 25px rgba(0,0,0,0.25);
        text-align: center;
    }
    .login-wrapper h2 { color: #FFFFFF !important; font-weight: 800; margin-bottom: 25px; font-size: 24px; }
    .login-wrapper label { color: #FFFFFF !important; font-weight: 600 !important; text-align: left !important; display: block; }
    
    /* Forzar textos blancos legibles en la barra lateral */
    [data-testid="stSidebar"] { background-color: #0B2545 !important; min-width: 320px !important; }
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] h3 { 
        color: #FFFFFF !important; 
        font-weight: 700 !important; 
        font-size: 15px !important;
    }
    
    /* Visibilidad para desplegables internos */
    div[data-baseweb="select"] li span, div[data-baseweb="select"] div { color: #1E293B !important; }
    
    /* Botones de la barra lateral y accesos */
    [data-testid="stSidebar"] button, .login-wrapper button {
        background: #134074 !important;
        color: #FFFFFF !important; 
        border: 1px solid #FFFFFF !important;
        border-radius: 6px !important; 
        font-weight: bold !important;
        width: 100% !important; 
        height: 42px; 
        transition: all 0.3s ease;
    }
    [data-testid="stSidebar"] button:hover, .login-wrapper button:hover { background: #1E40AF !important; box-shadow: 0px 4px 12px rgba(255,255,255,0.2); }
    
    /* Tarjetas del Monitor Central */
    div.metric-premium {
        background-color: #FFFFFF; 
        border-left: 6px solid #134074; 
        padding: 20px;
        border-radius: 8px; 
        box-shadow: 0px 4px 14px rgba(0,0,0,0.05); 
        margin-bottom: 15px;
    }
    
    .stExpander {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        box-shadow: 0px 3px 10px rgba(0,0,0,0.03) !important;
        margin-bottom: 12px !important;
    }
    
    h1, h2, h3 { color: #0B2545 !important; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

# --- AUTENTICACIÓN INSTITUCIONAL ---
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    if os.path.exists(LOGO): st.image(LOGO, width=110)
    st.markdown("<h2>Acceso Sistema GTAE</h2>", unsafe_allow_html=True)
    
    u = st.text_input("Usuario Corporativo:", key="input_user_login").strip().lower()
    p = st.text_input("PIN Militar de Seguridad:", type="password", key="input_pin_login").strip()
    
    if st.button("Ingresar al Monitor Operativo", key="button_submit_login"):
        if u in USR and USR[u]["pin"] == p:
            st.session_state.user = USR[u]
            st.rerun()
        else:
            st.error("Credenciales militares incorrectas.")
            
    st.markdown('</div>', unsafe_allow_html=True)
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

# Estado dinámico del Candado según la presencia de los Secrets
if GITHUB_TOKEN and GITHUB_REPO:
    st.sidebar.success("🔒 Almacenamiento Permanente Activado")
else:
    st.sidebar.warning("⚠️ Modo Local (Configura Secrets en Streamlit)")

dep_sel = st.sidebar.selectbox("Visualizar Departamento:", ["LOGÍSTICA", "OPERACIONES", "OTRAS DEPENDENCIAS"], key="selector_dependencias_fijo_gtae")
cuat_sel = st.sidebar.radio("Seleccione Cuatrimestre:", ["C1", "C2", "C3"])
cuat_mapeo = {"C1": "1er Cuatrimestre", "C2": "2do Cuatrimestre", "C3": "3er Cuatrimestre"}
cuat_filtro_texto = cuat_mapeo[cuat_sel]

# ==============================================================================
# --- 4. GENERADOR DE REPORTES PDF OFICIAL ---
# ==============================================================================
def generar_pdf_oficial(inspector, df, cuat, estados, v_e_a, v_t_a, depto):
    pdf = FPDF(orientation='L', unit='mm', format='A4') 
    pdf.add_page()
    if os.path.exists(LOGO): pdf.image(LOGO, 10, 8, 25)
    
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.set_font("Helvetica", '', 8)
    pdf.cell(0, 5, f"Fecha de reporte: {fecha_actual}", ln=True, align='R')
    
    pdf.set_font("Helvetica", 'B', 14); pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 7, 'FUERZA AEREA ECUATORIANA', ln=True, align='C')
    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(0, 7, 'GRUPO DE TRANSPORTE AEREO ESPECIAL (GTAE)', ln=True, align='C')
    pdf.cell(0, 7, f'DEPARTAMENTO DE {depto}', ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_fill_color(0, 51, 102); pdf.set_text_color(255, 255, 255); pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, f"REPORTE TECNICO DE EJECUCION PRESUPUESTARIA - {cuat}", 0, 1, 'C', True)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", 'B', 8)
    pdf.cell(135, 5, "ELABORADO POR:", 0, 0, 'L')
    pdf.cell(142, 5, "REVISADO Y APROBADO POR:", 0, 1, 'L')
    pdf.ln(12)
    pdf.cell(135, 4, "____________________________________", 0, 0, 'L')
    pdf.cell(142, 4, "____________________________________", 0, 1, 'L')
    pdf.cell(135, 4, f"Econ. {inspector}", 0, 0, 'L')
    pdf.cell(142, 4, f"JEFE DEL DEPARTAMENTO DE {depto} GTAE", 0, 1, 'L')
    
    return pdf.output(dest='S').encode('latin1', errors='ignore')

# --- CÁLCULOS PRESUPUESTARIOS ---
df_visualizacion = df_pac.copy()
v_t_a, v_e_a = 0.0, 0.0

for idx, row in df_visualizacion.iterrows():
    depto_p = st.session_state.avances.get(f"depto_{row.name}", "LOGÍSTICA")
    cuat_p = st.session_state.avances.get(f"cuat_{row.name}", "1er Cuatrimestre")
    monto_p = float(st.session_state.avances.get(f"monto_{row.name}", float(row['COSTO TOTAL'])))
    avance_p = st.session_state.avances.get(f"s_{row.name}", "Pendiente")
    
    if depto_p == dep_sel and proceso_esta_activo(row.name, es_nuevo=False) and cuat_p == cuat_filtro_texto:
        v_t_a += monto_p
        if "DEVENGADO" in str(avance_p).upper() or "FINALIZADO" in str(avance_p).upper():
            v_e_a += monto_p

for i, np in enumerate(st.session_state.avances["procesos_nuevos"]):
    depto_p = st.session_state.avances.get(f"nuevo_depto_{i}", np.get('departamento', 'LOGÍSTICA'))
    cuat_p = st.session_state.avances.get(f"nuevo_cuat_{i}", np['cuatrimestre'])
    monto_p = float(st.session_state.avances.get(f"nuevo_monto_{i}", float(np['monto'])))
    avance_p = st.session_state.avances.get(f"nuevo_s_{i}", "1. Certificación Pertenencia/Existencia")
    
    if depto_p == dep_sel and proceso_esta_activo(i, es_nuevo=True) and cuat_p == cuat_filtro_texto:
        v_t_a += monto_p
        if "DEVENGADO" in str(avance_p).upper() or "FINALIZADO" in str(avance_p).upper():
            v_e_a += monto_p

# ==============================================================================
# --- 5. PANEL CENTRAL GRÁFICO ---
# ==============================================================================
st.markdown(f"Módulo de gestión técnica — Departamento: **{dep_sel}** — Periodo: **{cuat_filtro_texto}**")

col_met, col_pie = st.columns([1, 1])
with col_met:
    st.markdown('<div class="metric-premium">', unsafe_allow_html=True)
    st.metric(f"Presupuesto Planificado {dep_sel.capitalize()}", f"${v_t_a:,.2f}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="metric-premium">', unsafe_allow_html=True)
    st.metric("Monto Real Devengado Anual", f"${v_e_a:,.2f}", delta=f"{((v_e_a/v_t_a)*100) if v_t_a > 0 else 0:.2f}% de Ejecución")
    st.markdown('</div>', unsafe_allow_html=True)

with col_pie:
    monto_pendiente = max(0.0, v_t_a - v_e_a)
    if v_t_a > 0:
        fig = go.Figure(data=[go.Pie(labels=['Devengado Real', 'Pendiente'], values=[v_e_a, monto_pendiente], hole=.4, marker=dict(colors=['#1E3A8A', '#EF4444']))])
        fig.update_layout(margin=dict(t=20, b=0, l=0, r=0), height=180, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No existen procesos registrados para {dep_sel.lower()} en este cuatrimestre.")

# Panel de Administración Integrado
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
# --- 6. DISPLAY DE FILTRADO Y EXPANDERS INTERACTIVOS ---
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
                st.text_input("Objeto:", value=st.session_state.avances.get(f"nuevo_name_{i}", np['objeto']), key=f"nuevo_name_{i}", on_change=sync_estado, args=(f"nuevo_name_{i}",))
                cm, cp = st.columns(2)
                with cm: st.number_input("Monto:", value=monto_t, key=f"nuevo_monto_{i}", on_change=sync_estado, args=(f"nuevo_monto_{i}",))
                with cp: st.text_input("Partida:", value=st.session_state.avances.get(f"nuevo_part_{i}", np['partida']), key=f"nuevo_part_{i}", on_change=sync_estado, args=(f"nuevo_part_{i}",))
                
                c1, c2, c3 = st.columns(3)
                v_gen = st.session_state.avances.get(f"nuevo_eq_gen_{i}", "SIN ASIGNAR").upper().strip()
                v_seg = st.session_state.avances.get(f"nuevo_eq_seg_{i}", "SIN ASIGNAR").upper().strip()
                v_adm = st.session_state.avances.get(f"nuevo_eq_adm_{i}", "SIN ASIGNAR").upper().strip()
                with c1: st.selectbox("Generar Necesidad:", opciones_personal, index=opciones_personal.index(v_gen) if v_gen in opciones_personal else 0, key=f"nuevo_eq_gen_{i}", on_change=sync_estado, args=(f"nuevo_eq_gen_{i}",))
                with c2: st.selectbox("Seguimiento FAE:", opciones_personal, index=opciones_personal.index(v_seg) if v_seg in opciones_personal else 0, key=f"nuevo_eq_seg_{i}", on_change=sync_estado, args=(f"nuevo_eq_seg_{i}",))
                with c3: st.selectbox("Administrador:", opciones_personal, index=opciones_personal.index(v_adm) if v_adm in opciones_personal else 0, key=f"nuevo_eq_adm_{i}", on_change=sync_estado, args=(f"nuevo_eq_adm_{i}",))
            with t2:
                st.select_slider("Fase actual:", options=puntos_fases, value=st.session_state.avances.get(f"nuevo_s_{i}", puntos_fases[0]), key=f"nuevo_s_{i}", on_change=sync_estado, args=(f"nuevo_s_{i}",))
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
            
        proc_text = str(r.get('PROCEDIMIENTO SUGERIDO (SON LOS PROCEDIMIENTOS DE CONTRATACIÓN)', '')).upper()
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
                    st.text_input("Objeto de Contratación:", value=st.session_state.avances.get(f"name_{r.name}", str(r.get(col_desc, 'S/N'))), key=f"name_{r.name}", on_change=sync_estado, args=(f"name_{r.name}",))
                    cm, cp = st.columns(2)
                    with cm: st.number_input("Monto Real:", value=monto_tarjeta, key=f"monto_{r.name}", on_change=sync_estado, args=(f"monto_{r.name}",))
                    with cp: st.text_input("Partida:", value=st.session_state.avances.get(f"part_{r.name}", "S/N"), key=f"part_{r.name}", on_change=sync_estado, args=(f"part_{r.name}",))
                    
                    c1, c2, c3 = st.columns(3)
                    v_gen = st.session_state.avances.get(f"eq_gen_{r.name}", "SIN ASIGNAR").upper().strip()
                    v_seg = st.session_state.avances.get(f"eq_seg_{r.name}", "SIN ASIGNAR").upper().strip()
                    v_adm = st.session_state.avances.get(f"eq_adm_{r.name}", "SIN ASIGNAR").upper().strip()
                    with c1: st.selectbox("Generar Necesidad:", opciones_personal, index=opciones_personal.index(v_gen) if v_gen in opciones_personal else 0, key=f"eq_gen_{r.name}", on_change=sync_estado, args=(f"eq_gen_{r.name}",))
                    with c2: st.selectbox("Seguimiento FAE:", opciones_personal, index=opciones_personal.index(v_seg) if v_seg in opciones_personal else 0, key=f"eq_seg_{r.name}", on_change=sync_estado, args=(f"eq_seg_{r.name}",))
                    with c3: st.selectbox("Administrador:", opciones_personal, index=opciones_personal.index(v_adm) if v_adm in opciones_personal else 0, key=f"eq_adm_{r.name}", on_change=sync_estado, args=(f"eq_adm_{r.name}",))
                with t2:
                    st.select_slider("Fase:", options=puntos, value=st.session_state.avances.get(f"s_{r.name}", puntos[0]), key=f"s_{r.name}", on_change=sync_estado, args=(f"s_{r.name}",))
                    st.selectbox("Mover de Cuatrimestre:", ["1er Cuatrimestre", "2do Cuatrimestre", "3er Cuatrimestre"], index=["1er Cuatrimestre", "2do Cuatrimestre", "3er Cuatrimestre"].index(cuat_p), key=f"cuat_{r.name}", on_change=sync_estado, args=(f"cuat_{r.name}",))
                    st.selectbox("Transferir Departamento:", ["LOGÍSTICA", "OPERACIONES", "OTRAS DEPENDENCIAS"], index=["LOGÍSTICA", "OPERACIONES", "OTRAS DEPENDENCIAS"].index(depto_p), key=f"depto_{r.name}", on_change=sync_estado, args=(f"depto_{r.name}",))
                with t3:
                    link_guardado = st.session_state.avances.get(f"lnk_nube_{r.name}", URL_BASE_FAE)
                    st.text_input("URL Carpeta Específica del Trámite:", value=link_guardado, key=f"lnk_nube_{r.name}", on_change=sync_estado, args=(f"lnk_nube_{r.name}",))
                    st.link_button("📥 ABRIR EXPEDIENTE EN REPOSITORIO INSTITUCIONAL", url=link_guardado, use_container_width=True)

# --- REPORTE PDF SEPARADO ---
st.sidebar.markdown("---")
pdf_bytes = generar_pdf_oficial(st.session_state.user['nom'], df_visualizacion, cuat_sel, st.session_state.avances, v_e_a, v_t_a, dep_sel)
st.sidebar.download_button(label="📥 DESCARGAR REPORTE PDF", data=pdf_bytes, file_name=f"Reporte_{dep_sel}_{cuat_sel}.pdf", mime="application/pdf", use_container_width=True)

if st.sidebar.button("Cerrar Sesión Activa"):
    st.session_state.user = None
    st.rerun()

# --- FIRMA DE AUTOR ---
st.sidebar.markdown("---")
st.sidebar.markdown("<div style='text-align: center; background-color: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px;'><p style='color: white; font-size: 11px; margin-bottom: 0;'>© 2026 Desarrollado por:</p><p style='color: #FFD700; font-size: 13px; font-weight: bold; margin-top: 5px;'>Econ. Geovanny Conterón</p><p style='color: #E3F2FD; font-size: 10px; font-style: italic;'>GTAE - FAE</p></div>", unsafe_allow_html=True)