import io
import os
import subprocess
import sys
import time
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests
import streamlit as st

try:
    from st_aggrid import AgGrid, GridOptionsBuilder
except ImportError:
    AgGrid = None
    GridOptionsBuilder = None


API_URL = os.getenv("FLASK_API_URL", "http://127.0.0.1:5000").rstrip("/")
REQUEST_TIMEOUT = 45
PROJECT_DIR = Path(__file__).resolve().parent
FLASK_DIR = PROJECT_DIR / "backend"
FLASK_APP = FLASK_DIR / "app.py"

COLUMNS = [
    "SGI", "Nombre", "BU", "Tipo Empleado", "CCO", "Puesto", "Área",
    "Fecha Ingreso", "Antigüedad", "Fecha Nacimiento", "Edad", "Género",
    "SD", "SM", "Inc Salarial %", "Promoción %", "Nivelación %", "Suma %",
    "Nuevo salario", "Comentarios",
]
FIELD_MAP = {
    "SGI": "sgi", "Nombre": "nombre", "BU": "bu", "Tipo Empleado": "tipoEmpleado",
    "CCO": "cco", "Puesto": "puesto", "Área": "area", "Fecha Ingreso": "fechaIngreso",
    "Antigüedad": "antiguedad", "Fecha Nacimiento": "fechaNacimiento", "Edad": "edad",
    "Género": "genero", "SD": "sd", "SM": "sm", "Inc Salarial %": "incSalarial",
    "Promoción %": "promocion", "Nivelación %": "nivelacion", "Suma %": "sumaPorcentual",
    "Nuevo salario": "nuevoSalario", "Comentarios": "comentarios",
}

st.set_page_config(page_title="Budget Planning 2027", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --blue:#1557a6; --blue-dark:#102e52; --green:#24784b; --ink:#1d2a3a; --muted:#68788a; --line:#dbe4ee; --canvas:#edf2f7; --surface:#ffffff; --soft:#f5f8fb; --shadow:0 10px 26px rgba(27,55,87,.07); }
    .stApp { background:linear-gradient(180deg,#f7faff 0%,var(--canvas) 58%,#e8eef5 100%); color:var(--ink); font-family:'DM Sans', sans-serif; }
    [data-testid="stSidebar"] { background:#f7faff; border-right:1px solid #d9e4ef; }
    [data-testid="stSidebar"] .block-container { padding:20px 16px; }
    [data-testid="stMetric"] { background:var(--surface); border:1px solid #d4e0ec; border-radius:14px; padding:12px 14px; min-height:88px; box-shadow:0 5px 16px rgba(27,55,87,.05); }
    [data-testid="stMetricLabel"] { color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:.1em; }
    [data-testid="stMetricValue"] { color:var(--blue-dark); font-family:'Space Grotesk',sans-serif; font-size:24px; }
    [data-testid="stHeader"] { background:transparent; }
    .block-container { max-width:1680px; padding:16px 24px 24px; }
    .hero { background:var(--surface); border:1px solid rgba(21,101,192,.08); border-radius:18px; padding:18px 26px 16px; box-shadow:var(--shadow); }
    .logos { display:flex; justify-content:center; align-items:center; gap:40px; min-height:70px; }
    .logos img { height:70px; max-width:245px; object-fit:contain; }
    .divider { width:2px; height:80px; background:#1f5cb8; }
    .hero-line { margin-top:24px; border-top:1px solid #d9e1ef; }
    .hero h1 { margin:18px 0 0; text-align:center; font:700 38px 'Space Grotesk', sans-serif; color:var(--blue-dark); }
    .section-label { margin:14px 0 7px; color:var(--blue-dark); font:700 17px 'Space Grotesk', sans-serif; }
    .executive-label { margin:12px 0 6px; color:var(--muted); font-size:11px; font-weight:700; letter-spacing:.14em; text-transform:uppercase; }
    .dashboard-card { background:var(--surface); border:1px solid rgba(15,23,42,.04); border-radius:16px; box-shadow:var(--shadow); overflow:hidden; min-height:286px; }
    .card-header { display:flex; justify-content:space-between; align-items:center; gap:12px; padding:12px 15px; background:linear-gradient(90deg,#f8fbff,#eef5fc); border-bottom:1px solid var(--line); }
    .card-header h2 { margin:0; color:#17324f; font:700 15px 'Space Grotesk', sans-serif; }
    .pill { border-radius:999px; padding:5px 9px; color:var(--blue); background:rgba(21,101,192,.09); font-size:11px; font-weight:700; white-space:nowrap; }
    .pill.green { color:var(--green); background:rgba(31,139,76,.12); }
    .metric { background:var(--soft); border:1px solid var(--line); border-radius:10px; padding:9px 11px; min-height:52px; }
    .metric small { display:block; margin-bottom:7px; color:var(--muted); font-size:11px; letter-spacing:.12em; text-transform:uppercase; }
    .metric strong { color:#12304a; font-size:16px; }
    .sheet-panel { background:var(--surface); border:1px solid rgba(15,23,42,.04); border-radius:16px; box-shadow:0 12px 30px rgba(15,23,42,.08); padding:0 12px 12px; }
    .sheet-panel.primary { box-shadow:0 14px 34px rgba(21,87,166,.11); border-color:#cbdbea; }
    .action-center { background:var(--surface); border:1px solid #cbdbea; border-radius:16px; box-shadow:var(--shadow); padding:0 14px 14px; }
    .action-center .card-header { margin:0 -14px 12px; }
    .action-toolbar { margin-bottom:12px; }
    .action-toolbar div[data-testid="stHorizontalBlock"] { align-items:stretch; }
    .action-toolbar div[data-testid="stFileUploader"] section { min-height:38px; }
    .action-note { color:var(--muted); font-size:12px; line-height:1.45; margin:0 0 12px; }
    .history-grid [data-testid="stVerticalBlockBorderWrapper"] { min-height:170px; }
    [data-testid="stVerticalBlockBorderWrapper"] { background:var(--surface); border-color:rgba(15,23,42,.06); border-radius:16px; box-shadow:var(--shadow); }
    .dashboard-marker { height:0; overflow:hidden; margin:0; padding:0; }
    [data-testid="stVerticalBlockBorderWrapper"]:has(.dashboard-marker) { min-height:274px; padding:0 13px 12px; overflow:hidden; }
    [data-testid="stVerticalBlockBorderWrapper"]:has(.dashboard-marker) > div { height:100%; }
    [data-testid="stVerticalBlockBorderWrapper"]:has(.dashboard-marker) .card-header { margin:0 -13px; padding:12px 13px; }
    [data-testid="stVerticalBlockBorderWrapper"]:has(.dashboard-marker) .stSelectbox,
    [data-testid="stVerticalBlockBorderWrapper"]:has(.dashboard-marker) .stMultiSelect { margin-top:4px; }
    [data-testid="stVerticalBlockBorderWrapper"]:has(.dashboard-marker) .stButton { margin-top:4px; }
    [data-testid="stVerticalBlockBorderWrapper"]:has(.kpi-marker) { min-height:132px; padding:0 12px 10px; }
    [data-testid="stVerticalBlockBorderWrapper"]:has(.kpi-marker) .card-header { margin:0 -12px; padding:10px 12px; }
    [data-testid="stVerticalBlockBorderWrapper"]:has(.kpi-marker) .metric { min-height:44px; padding:7px 9px; }
    [data-testid="stVerticalBlockBorderWrapper"]:has(.kpi-marker) .metric small { margin-bottom:3px; font-size:10px; }
    [data-testid="stVerticalBlockBorderWrapper"]:has(.kpi-marker) .metric strong { font-size:14px; }
    .sheet-head { display:flex; justify-content:space-between; align-items:center; padding:14px 7px 7px; gap:16px; }
    .sheet-head h2 { margin:0 0 4px; color:#17324f; font:700 21px 'Space Grotesk', sans-serif; }
    .sheet-head p { margin:0; color:var(--muted); }
    .sheet-badge { background:var(--blue); color:white; border-radius:999px; padding:7px 11px; font-size:11px; font-weight:700; white-space:nowrap; }
    .history-panel { background:var(--surface); border:1px solid rgba(15,23,42,.04); border-radius:16px; box-shadow:var(--shadow); overflow:hidden; min-height:190px; }
    .history-body { padding:12px 14px; max-height:260px; overflow-y:auto; }
    .history-row { border:1px solid var(--line); border-radius:10px; padding:9px 11px; background:#f8fbff; margin-bottom:8px; font-size:12px; }
    .history-row strong { display:block; margin-bottom:4px; }
    .version-selected { border-color:var(--blue); background:#eaf3ff; }
    .stButton > button, .stDownloadButton > button { border-radius:8px; font-weight:700; border:1px solid #d3dfec; min-height:38px; padding:5px 10px; transition:background .15s ease,border-color .15s ease; }
    .stButton > button:hover, .stDownloadButton > button:hover { border-color:#9db8d5; }
    .stButton > button[kind="primary"], .stDownloadButton > button { background:var(--blue); color:#fff; border-color:var(--blue); }
    .action-bar { margin:3px 0 10px; padding:8px; border:1px solid var(--line); border-radius:10px; background:#f8fafc; }
    .action-bar .action-label { color:var(--blue-dark); }
    .action-label { margin:0 0 6px; color:var(--muted); font-size:11px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; }
    .selected-file { margin:6px 0 8px; padding:7px 9px; border:1px solid var(--line); border-radius:8px; background:#f8fbff; color:#17324f; font-size:12px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    div[data-testid="stHorizontalBlock"] { align-items:flex-end; }
    div[data-testid="stDataEditor"] { border:1px solid #cfdbe8; border-radius:10px; overflow:hidden; min-height:600px; box-shadow:0 2px 8px rgba(27,55,87,.04); }
    div[data-testid="stDataFrame"] { border:1px solid #cfdbe8; border-radius:10px; overflow:hidden; }
    div[data-testid="stExpander"] { border:1px solid var(--line); border-radius:12px; background:var(--surface); }
    div[data-testid="stExpander"] details summary { font-weight:700; color:var(--blue-dark); }
    div[data-testid="stFileUploader"] section { border:1px dashed #b9c9da; border-radius:8px; background:#fbfdff; }
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] input { border-radius:8px; }
    .stCaption { color:var(--muted); }
    .compact-card { padding:0 14px 14px; }
    .compact-card .card-header { margin:0 -14px 12px; }
    .version-help { color:var(--muted); font-size:12px; margin:0 0 8px; }
    div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stDataEditor"]) { width:100%; }
    div[data-testid="stSelectbox"] { margin-bottom:2px; }
    @media (max-width: 700px) { .block-container { padding:12px 10px 18px; } .hero { padding:16px; } .logos { gap:16px; } .logos img { height:48px; max-width:40%; } .divider { height:58px; } .hero h1 { font-size:30px; } .sheet-head { align-items:flex-start; flex-direction:column; } }
    </style>
    """,
    unsafe_allow_html=True,
)


def endpoint(path):
    return f"{API_URL}/{path.lstrip('/')}"


def flask_is_running():
    try:
        response = requests.get(endpoint(""), timeout=2)
        return response.ok
    except requests.RequestException:
        return False


def ensure_flask_running():
    """Start Flask only when its existing health endpoint is unavailable."""
    if flask_is_running():
        return True, "Flask ya estaba ejecutándose en el puerto 5000."

    if not FLASK_APP.exists():
        return False, f"No se encontró el backend Flask en {FLASK_APP}."

    creation_flags = 0
    if os.name == "nt":
        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW

    try:
        subprocess.Popen(
            [sys.executable, str(FLASK_APP)],
            cwd=str(FLASK_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
            close_fds=os.name != "nt",
        )
    except OSError as exc:
        return False, f"No fue posible iniciar Flask: {exc}"

    for _ in range(20):
        if flask_is_running():
            return True, "Flask se inició automáticamente en el puerto 5000."
        time.sleep(0.5)

    return False, "Flask no respondió en el puerto 5000 después del inicio."


def api_get(path, default=None):
    try:
        response = requests.get(endpoint(path), timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(f"No fue posible conectar con Flask: {exc}")
        return default


def api_get_silent(path, default=None):
    """Read optional future endpoints without interrupting the main dashboard."""
    try:
        response = requests.get(endpoint(path), timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return default


def api_post(path, *, json=None, files=None):
    response = requests.post(endpoint(path), json=json, files=files, timeout=REQUEST_TIMEOUT)
    if not response.ok:
        try:
            detail = response.json().get("error") or response.json().get("message")
        except ValueError:
            detail = response.text.strip()
        raise requests.HTTPError(
            f"{response.status_code} {response.reason}: {detail or 'Error del servidor'}",
            response=response,
        )
    return response


def upload_sheet(filename, content):
    filename = os.path.basename(filename or "")
    if not filename.lower().endswith(".xlsx") or not content:
        raise ValueError("Selecciona un archivo .xlsx válido.")

    try:
        workbook = pd.read_excel(io.BytesIO(content), engine="openpyxl")
    except Exception as exc:
        raise ValueError(f"No se pudo leer el archivo Excel: {exc}") from exc

    def normalize_column(column):
        return "".join(
            character for character in str(column).strip().lower()
            if character.isalnum()
        )

    aliases = {
        "sgi": "SGI",
        "incrementosalarial": "Incremento Salarial",
        "incsalarial": "Incremento Salarial",
        "inc": "Incremento Salarial",
        "promocion": "Promoción",
        "promocionsalarial": "Promoción",
        "nivelacion": "Nivelación",
        "nivelacionsalarial": "Nivelación",
    }
    renamed_columns = {
        column: aliases.get(normalize_column(column), column)
        for column in workbook.columns
    }
    workbook = workbook.rename(columns=renamed_columns)
    required_columns = {"SGI", "Incremento Salarial", "Promoción", "Nivelación"}
    missing_columns = sorted(required_columns - set(workbook.columns))
    if missing_columns:
        raise ValueError(
            "El archivo no contiene las columnas requeridas: "
            + ", ".join(missing_columns)
        )

    normalized_content = io.BytesIO()
    workbook.to_excel(normalized_content, index=False, engine="openpyxl")
    normalized_content.seek(0)
    return api_post(
        "actualizar_sabana",
        files={
            "file": (
                filename,
                normalized_content.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )


def normalize_record(record):
    def value(*keys):
        for key in keys:
            item = record.get(key)
            if item is not None and str(item).strip() != "":
                return item
        return ""

    aliases = {
        "Nombre": ["nombre_completo", "full_name"], "BU": ["compania", "company"],
        "Tipo Empleado": ["tipo_empleado", "tipo", "tipoEmpleado"],
        "CCO": ["ceco", "centro_costo"], "Área": ["filiere", "filiere_desc", "division"],
        "SM": ["salario_mensual", "salario_mensual_base", "salary"],
        "SD": ["salario_diario", "salario_diario_base"],
        "Inc Salarial %": ["inc_salarial", "inc"], "Promoción %": ["promotion"],
        "Nivelación %": ["nivelacion_salarial"], "Comentarios": ["comments"],
        "Fecha Ingreso": ["fecha_ingreso", "ingreso", "f_ingreso"],
        "Fecha Nacimiento": ["fecha_nacimiento", "f_nacimiento"],
        "Género": ["sexo", "gender"], "Antigüedad": ["antiguedad", "years_service"], "Edad": ["edad"],
        "Suma %": ["suma_porcentual"], "Nuevo salario": ["nuevo_salario"],
    }
    row = {column: value(*([FIELD_MAP[column]] + aliases.get(column, []))) for column in COLUMNS}

    def parse_backend_date(raw_value):
        if not raw_value:
            return None
        raw_text = str(raw_value).strip()
        try:
            return datetime.fromisoformat(raw_text.replace("Z", "+00:00")).date()
        except ValueError:
            try:
                return parsedate_to_datetime(raw_text).date()
            except (TypeError, ValueError, IndexError):
                return None

    today = datetime.now().date()
    entry_date = parse_backend_date(row["Fecha Ingreso"])
    birth_date = parse_backend_date(row["Fecha Nacimiento"])
    if not row["Antigüedad"] and entry_date:
        years = today.year - entry_date.year - ((today.month, today.day) < (entry_date.month, entry_date.day))
        row["Antigüedad"] = f"{years} años" if years >= 0 else ""
    if not row["Edad"] and birth_date:
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        row["Edad"] = str(age) if age >= 0 else ""
    return row


def records_to_frame(records):
    frame = pd.DataFrame([normalize_record(item) for item in (records or [])], columns=COLUMNS)
    for column in ["SD", "SM", "Inc Salarial %", "Promoción %", "Nivelación %"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def frame_to_records(frame):
    records = []
    for row in frame.fillna("").to_dict(orient="records"):
        record = {FIELD_MAP[column]: row.get(column, "") for column in COLUMNS if column in FIELD_MAP}
        record["isNewRecord"] = False
        records.append(record)
    return records


def managers_from_employees(employees):
    options = {}
    for employee in employees or []:
        manager = str(employee.get("manager") or "").strip()
        manager_sgi = str(employee.get("sg_manager") or employee.get("manager_sgi") or employee.get("sgi_manager") or employee.get("manager_id") or manager).strip()
        name = str(
            employee.get("manager_name")
            or employee.get("manager_nombre")
            or employee.get("nombre_manager")
            or employee.get("nombre_gerente")
            or employee.get("managerFullName")
            or employee.get("nombre_supervisor")
            or employee.get("supervisor_nombre")
            or employee.get("nombre_jefe")
            or employee.get("jefe_nombre")
            or employee.get("display_name")
            or manager
        ).strip()
        if manager and name and manager.lower() != str(employee.get("sgi") or "").strip().lower():
            options.setdefault(manager, {"manager": manager, "nombre": name, "sgi": manager_sgi})
    return sorted(options.values(), key=lambda item: item["nombre"].lower())


def manager_option_label(item):
    return f'{item["sgi"]} - {item["nombre"]}'


def version_label(item):
    raw_date = item.get("fecha_creacion") or item.get("fecha") or item.get("created_at") or "Sin fecha"
    try:
        date_text = datetime.fromisoformat(str(raw_date).replace("Z", "+00:00")).strftime("%d/%m/%Y")
    except ValueError:
        date_text = str(raw_date)
    return f'{date_text} - {item.get("descripcion") or item.get("description") or item.get("version_id") or "Versión"}'


def card_header(title, pill, green=False):
    css = "pill green" if green else "pill"
    st.markdown(f'<div class="card-header"><h2>{title}</h2><span class="{css}">{pill}</span></div>', unsafe_allow_html=True)


def history_rows(items):
    if not items:
        st.caption("No hay registros para mostrar.")
    for item in items:
        label = item.get("manager") or item.get("lote_id") or item.get("periodo") or "Versión"
        detail = item.get("timestamp") or item.get("fecha_registro") or item.get("periodo") or ""
        st.markdown(f'<div class="history-row"><strong>{label}</strong><span>{detail}</span></div>', unsafe_allow_html=True)


if "employees" not in st.session_state:
    flask_ready, flask_message = ensure_flask_running()
    st.session_state.flask_ready = flask_ready
    st.session_state.flask_message = flask_message
    st.session_state.employees = api_get("empleados", []) or []
if "selected_manager" not in st.session_state:
    st.session_state.selected_manager = None
if "selected_budget_version" not in st.session_state:
    st.session_state.selected_budget_version = None
if "selected_history_lote" not in st.session_state:
    st.session_state.selected_history_lote = None
if "update_sheet_name" not in st.session_state:
    st.session_state.update_sheet_name = ""
if "update_sheet_bytes" not in st.session_state:
    st.session_state.update_sheet_bytes = None
if "sheet_records" not in st.session_state:
    budget_path = "budget_actual" if not st.session_state.selected_budget_version else f"budget_actual/{quote(st.session_state.selected_budget_version, safe='')}"
    st.session_state.sheet_records = api_get(budget_path, []) or []
if "history_items" not in st.session_state:
    st.session_state.history_items = []
if "selected_prestaciones_version" not in st.session_state:
    st.session_state.selected_prestaciones_version = None

if not st.session_state.get("flask_ready", False):
    st.warning(st.session_state.get("flask_message", "Flask no está disponible."))

image_dir = os.path.join(os.path.dirname(__file__), "imagenes")
logo_one = os.path.join(image_dir, "saint_gobain.png")
logo_two = os.path.join(image_dir, "total_rewards.jpg")
logo_html = ""
for logo in [logo_one, logo_two]:
    if os.path.exists(logo):
        import base64
        mime = "image/png" if logo.endswith(".png") else "image/jpeg"
        with open(logo, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("ascii")
        logo_html += f'<img src="data:{mime};base64,{encoded}" alt="Budget Planning">'

st.markdown(f'<header class="hero"><div class="logos">{logo_html}<span class="divider"></span></div><div class="hero-line"></div><h1>Budget Planning 2027</h1></header>', unsafe_allow_html=True)

options = managers_from_employees(st.session_state.employees)

with st.sidebar:
    st.markdown("### Centro de control")
    st.caption("Compensation & Budget Planning")
    if st.button("General", key="general", use_container_width=True):
        st.session_state.selected_manager = None
        st.session_state.selected_history_lote = None
        st.session_state.selected_budget_version = None
        st.session_state.sheet_records = api_get("budget_actual", []) or []
        st.session_state.history_items = []
        st.rerun()
    manager_pick = st.selectbox("Manager", options, index=None, key="manager_pick", placeholder="Buscar por SGI o nombre", format_func=manager_option_label)
    if manager_pick and manager_pick["manager"] != st.session_state.selected_manager:
        st.session_state.selected_manager = manager_pick["manager"]
        st.session_state.selected_history_lote = None
        st.session_state.selected_budget_version = None
        team = api_get(f'equipo/{quote(manager_pick["manager"], safe="")}', []) or []
        st.session_state.sheet_records = team
        st.session_state.history_items = api_get(f'historial/{quote(manager_pick["manager"], safe="")}', []) or []
        st.rerun()
    st.divider()
    st.markdown("#### Envío de correos")
    selected_mail_options = st.multiselect("Managers", options, key="selected_mail", format_func=manager_option_label, placeholder="Seleccionar managers")
    if st.button("📧 Enviar Correos", type="primary", use_container_width=True):
        try:
            result = api_post("enviar_correos", json={"managers": [item["manager"] for item in selected_mail_options]}).json()
            st.success(result.get("message", "Solicitud enviada."))
        except requests.RequestException as exc:
            st.error(f"No fue posible enviar los correos: {exc}")

current = st.session_state.sheet_records
country = current[0].get("pais") or current[0].get("country") or "-" if current else "-"
manager_name = next((x["nombre"] for x in options if x["manager"] == st.session_state.selected_manager), "General")
st.markdown('<div class="section-label">Executive overview</div>', unsafe_allow_html=True)
kpi_one, kpi_two, kpi_three, kpi_four = st.columns(4, gap="medium")
with kpi_one:
    st.metric("Headcount", len(current), border=True)
with kpi_two:
    st.metric("País", country, border=True)
with kpi_three:
    st.metric("Manager", manager_name, border=True)
with kpi_four:
    st.metric("Estado", "En revisión", border=True)

consolidation_slot = st.empty()
top_history_slot = st.empty()
sheet_slot = st.empty()
budget_history_slot = st.empty()

if "action_panel_open" not in st.session_state:
    st.session_state.action_panel_open = False
completed_items = api_get("completados", []) or []
budget_versions = api_get("budget_versiones", []) or []


def render_consolidation(target):
    with target.container(border=True):
        card_header("📥 Consolidación de Respuestas", "Budget Planning")
        consolidation_files = st.file_uploader("Selecciona archivos Excel", type=["xlsx"], accept_multiple_files=True, key="consolidation_files")
        consolidate_clicked = st.button("📥 Consolidar Archivos", type="primary", use_container_width=True)
        if consolidate_clicked:
            if not consolidation_files:
                st.warning("Selecciona al menos un archivo.")
            else:
                try:
                    payload = [("files", (file.name, file.getvalue(), file.type)) for file in consolidation_files]
                    result = api_post("consolidar_excels", files=payload)
                    st.success(result.json().get("message", "Consolidación completada correctamente"))
                    consolidated = requests.get(endpoint("descargar_consolidado"), timeout=REQUEST_TIMEOUT)
                    consolidated.raise_for_status()
                    st.download_button("Descargar consolidado", consolidated.content, file_name="consolidado.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                except requests.RequestException as exc:
                    st.error(f"No fue posible consolidar: {exc}")


def render_top_history(target):
    with target.container():
        with st.container(border=True):
            card_header("Histórico del Manager", "Auditoría")
            history_options = [item.get("lote_id") for item in st.session_state.history_items if item.get("lote_id")]
            selected_lote = st.selectbox("Lote histórico", history_options, index=None, label_visibility="collapsed", placeholder="Selecciona una versión")
            if selected_lote:
                detail = api_get(f"historial_detalle/{quote(selected_lote, safe='')}", []) or []
                if selected_lote != st.session_state.selected_history_lote:
                    st.session_state.selected_history_lote = selected_lote
                    st.session_state.selected_budget_version = None
                    st.session_state.sheet_records = detail
                    st.rerun()
                if detail:
                    st.dataframe(pd.DataFrame(detail), use_container_width=True, hide_index=True, height=220)
                history_action_one, history_action_two = st.columns(2)
                with history_action_one:
                    if st.button("Aprobar", type="primary", use_container_width=True):
                        try:
                            api_post(f"aprobar/{quote(selected_lote, safe='')}")
                            st.success("Histórico aprobado.")
                        except requests.RequestException as exc:
                            st.error(f"No fue posible aprobar: {exc}")
                with history_action_two:
                    try:
                        history_excel = requests.get(endpoint(f"excel/{quote(selected_lote, safe='')}"), timeout=REQUEST_TIMEOUT)
                        history_excel.raise_for_status()
                        st.download_button("Descargar Excel", history_excel.content, file_name=f"Historico_{selected_lote}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                    except requests.RequestException:
                        st.button("Descargar Excel", disabled=True, use_container_width=True)
        with st.expander("Completados", expanded=False):
            if completed_items:
                st.dataframe(pd.DataFrame(completed_items), use_container_width=True, hide_index=True, height=180)
            else:
                st.caption("No hay históricos aprobados pendientes.")


def render_prestaciones(target):
    with target.container():
        with st.expander("Prestaciones", expanded=False):
            card_header("Prestaciones", "Compensación")
            prestaciones_records = api_get("prestaciones_generales", None)
            if prestaciones_records is None:
                st.error("No fue posible obtener prestaciones_generales desde Flask.")
                return

            st.write(f"Prestaciones encontradas: {len(prestaciones_records)}")
            if not prestaciones_records:
                st.warning("El endpoint prestaciones_generales respondió 0 registros.")
                return

            prestaciones_columns = [
                "pais", "budget", "empresa", "unidad_negocio", "categoria",
                "sindicato", "prestacion", "tipo_valor", "valor", "observaciones",
            ]
            prestaciones_frame = pd.DataFrame(prestaciones_records)
            visible_columns = [column for column in prestaciones_columns if column in prestaciones_frame.columns]
            prestaciones_frame = prestaciones_frame[visible_columns]
            edited_prestaciones = st.data_editor(
                prestaciones_frame,
                use_container_width=True,
                num_rows="dynamic",
                height=420,
                key="prestaciones_editor",
                hide_index=True,
            )
            action_col, description_col = st.columns([1, 2], gap="medium")
            with action_col:
                save_prestaciones = st.button("Guardar Prestaciones", type="primary", use_container_width=True)
            with description_col:
                prestaciones_description = st.text_input("Descripción de versión", placeholder="Ej. Ajuste CEMIX", label_visibility="collapsed")
            if save_prestaciones:
                payload = {
                    "registros": edited_prestaciones.fillna("").to_dict(orient="records"),
                    "descripcion": prestaciones_description.strip() or "Actualización de prestaciones",
                    "usuario": os.getenv("USERNAME") or os.getenv("USER") or "Streamlit",
                }
                try:
                    result = api_post("guardar_prestaciones", json=payload).json()
                    st.success(f'Prestaciones guardadas. Versión: {result.get("version_id", "registrada")}')
                except requests.RequestException as exc:
                    st.error(f"No fue posible guardar prestaciones: {exc}")


def render_prestaciones_history(target):
    with target.container(border=True):
        card_header("Histórico Prestaciones", "Versiones")
        versions = api_get_silent("prestaciones_versiones", []) or []
        version_ids = [item.get("version_id") for item in versions if item.get("version_id")]
        version_map = {item.get("version_id"): item for item in versions}
        selected_version = st.selectbox(
            "Versión de prestaciones",
            [None] + version_ids,
            format_func=lambda value: "Versión actual" if value is None else version_label(version_map[value]),
            index=0,
            key="prestaciones_version_pick",
            label_visibility="collapsed",
            placeholder="Selecciona una versión",
        )
        if selected_version and selected_version != st.session_state.selected_prestaciones_version:
            detail = api_get_silent(f"prestaciones_historico/{quote(str(selected_version), safe='')}", []) or []
            st.session_state.selected_prestaciones_version = selected_version
            if detail:
                st.dataframe(pd.DataFrame(detail), use_container_width=True, hide_index=True, height=260)
        elif selected_version:
            detail = api_get_silent(f"prestaciones_historico/{quote(str(selected_version), safe='')}", []) or []
            if detail:
                st.dataframe(pd.DataFrame(detail), use_container_width=True, hide_index=True, height=260)
        else:
            st.caption("Selecciona una versión para consultar sus datos asociados.")


def render_sheet(target):
    with target.container():
        save_clicked = False
        update_clicked = False
        with st.expander("▶ Centro de Acciones", expanded=False):
            st.markdown('<div class="action-center action-toolbar">', unsafe_allow_html=True)
            card_header("Centro de Acciones", "Operación")
            st.markdown('<p class="action-note">Administra la sábana, carga archivos y confirma los cambios desde este panel.</p>', unsafe_allow_html=True)
            action_one, action_two, action_three, action_four = st.columns(4, gap="small")
            with action_one:
                if st.button("+ Nuevo Registro", use_container_width=True):
                    st.session_state.sheet_records = [{}] + st.session_state.sheet_records
                    st.rerun()
            with action_two:
                excel_payload = {"manager": st.session_state.selected_manager or "General", "registros": frame_to_records(records_to_frame(st.session_state.sheet_records))}
                try:
                    excel_response = api_post("excel_actual", json=excel_payload)
                    st.download_button("Descargar Excel", excel_response.content, file_name="Budget_General.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                except requests.RequestException:
                    st.button("Descargar Excel", disabled=True, use_container_width=True)
            with action_three:
                save_clicked = st.button("Guardar", type="primary", use_container_width=True)
            with action_four:
                with st.form("update_sheet_form", clear_on_submit=False):
                    st.markdown('<p class="action-label">Actualizar Sábana</p>', unsafe_allow_html=True)
                    update_file = st.file_uploader("Archivo .xlsx", type=["xlsx"], key="update_sheet", label_visibility="collapsed")
                    if update_file:
                        st.session_state.update_sheet_name = os.path.basename(update_file.name)
                        st.session_state.update_sheet_bytes = update_file.getvalue()
                    if st.session_state.update_sheet_name:
                        st.markdown(f'<div class="selected-file">Archivo: {st.session_state.update_sheet_name}</div>', unsafe_allow_html=True)
                    update_clicked = st.form_submit_button("Actualizar Sábana", type="primary", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="sheet-panel primary"><div class="sheet-head"><div><h2>General</h2><p>Vista consolidada de la organización para Budget Planning 2027</p></div><span class="sheet-badge">Corporate view</span></div>', unsafe_allow_html=True)
        budget_frame = records_to_frame(st.session_state.sheet_records)
        if AgGrid and GridOptionsBuilder:
            grid_builder = GridOptionsBuilder.from_dataframe(budget_frame)
            grid_builder.configure_default_column(
                editable=True,
                filter=True,
                sortable=True,
                resizable=True,
                wrapText=False,
            )
            grid_builder.configure_grid_options(
                pagination=False,
                sideBar="filters",
                enableRangeSelection=True,
                stopEditingWhenCellsLoseFocus=True,
            )
            grid_response = AgGrid(
                budget_frame,
                gridOptions=grid_builder.build(),
                height=640,
                width="100%",
                theme="streamlit",
                enable_enterprise_modules=False,
                allow_unsafe_jscode=False,
                fit_columns_on_grid_load=False,
                key="budget_aggrid",
            )
            data = pd.DataFrame(grid_response.get("data", budget_frame))
        else:
            st.info("Instala streamlit-aggrid para habilitar la vista avanzada de la sábana.")
            data = st.data_editor(budget_frame, use_container_width=True, num_rows="dynamic", height=620, key="budget_editor")
        st.markdown('</div>', unsafe_allow_html=True)
        if update_clicked:
            if not st.session_state.update_sheet_name or not st.session_state.update_sheet_bytes:
                st.warning("Selecciona un archivo .xlsx.")
            else:
                st.info("⏳ Actualizando sábana...")
                with st.spinner("Procesando archivo en Flask..."):
                    try:
                        result = upload_sheet(
                            st.session_state.update_sheet_name,
                            st.session_state.update_sheet_bytes,
                        ).json()
                        st.success(f'✅ Sábana actualizada correctamente. Versión: {result.get("version_id", "ok")}')
                    except (ValueError, requests.RequestException) as exc:
                        st.error(f"❌ Error al actualizar: {exc}")
        if save_clicked:
            try:
                result = api_post("guardar_registro", json={"manager": st.session_state.selected_manager or "General", "registros": frame_to_records(data)}).json()
                st.session_state.sheet_records = frame_to_records(data)
                st.success(result.get("message", "Cambios guardados correctamente"))
                if st.session_state.selected_manager:
                    st.session_state.history_items = api_get(f'historial/{quote(st.session_state.selected_manager, safe="")}', []) or []
            except requests.RequestException as exc:
                st.error(f"No fue posible guardar: {exc}")
        st.markdown('</div>', unsafe_allow_html=True)


def render_budget_history(target):
    with target.container(border=True):
        card_header("Histórico Budget", "Versiones")
        version_map = {version.get("version_id"): version for version in budget_versions}
        selected_version = st.selectbox(
            "Versión Budget",
            [None] + list(version_map),
            format_func=lambda value: "Versión actual - Sábana viva" if value is None else version_label(version_map[value]),
            index=0,
            key="budget_version_pick",
            label_visibility="collapsed",
            placeholder="Selecciona una versión",
        )
        if selected_version != st.session_state.selected_budget_version:
            st.session_state.selected_budget_version = selected_version
            budget_path = "budget_actual" if selected_version is None else f"budget_actual/{quote(str(selected_version), safe='')}"
            st.session_state.sheet_records = api_get(budget_path, []) or []
            st.rerun()
        if not budget_versions:
            st.caption("No hay versiones registradas todavía.")


render_sheet(sheet_slot)

prestaciones_slot = st.empty()
render_prestaciones(prestaciones_slot)

with st.sidebar:
    st.divider()
    st.markdown("#### Consolidación")
    render_consolidation(st.sidebar)

st.markdown('<div class="executive-label">Históricos y seguimiento</div>', unsafe_allow_html=True)
render_top_history(top_history_slot)
prestaciones_history_slot = st.empty()
render_budget_history(budget_history_slot)
render_prestaciones_history(prestaciones_history_slot)
