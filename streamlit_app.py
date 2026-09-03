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

st.set_page_config(page_title="Budget Planning 2027", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --blue:#1565C0; --blue-dark:#0d2c57; --green:#1F8B4C; --ink:#1F2937; --muted:#6C757D; --line:#E3E8EF; --canvas:#EEF2F6; }
    .stApp { background: radial-gradient(circle at 10% 0%, #f8fbff 0, var(--canvas) 42%, #e8eef5 100%); color:var(--ink); font-family:'DM Sans', sans-serif; }
    [data-testid="stHeader"] { background:transparent; }
    .block-container { max-width:1600px; padding:20px 18px 28px; }
    .hero { background:#fff; border:1px solid rgba(21,101,192,.08); border-radius:24px; padding:24px 28px 20px; box-shadow:0 14px 40px rgba(15,23,42,.08); }
    .logos { display:flex; justify-content:center; align-items:center; gap:40px; min-height:70px; }
    .logos img { height:70px; max-width:245px; object-fit:contain; }
    .divider { width:2px; height:80px; background:#1f5cb8; }
    .hero-line { margin-top:24px; border-top:1px solid #d9e1ef; }
    .hero h1 { margin:24px 0 0; text-align:center; font:700 42px 'Space Grotesk', sans-serif; color:var(--blue-dark); }
    .section-label { margin:18px 0 8px; color:var(--blue-dark); font:700 18px 'Space Grotesk', sans-serif; }
    .dashboard-card { background:#fff; border:1px solid rgba(15,23,42,.04); border-radius:20px; box-shadow:0 14px 40px rgba(15,23,42,.08); overflow:hidden; min-height:286px; }
    .card-header { display:flex; justify-content:space-between; align-items:center; gap:12px; padding:14px 16px; background:linear-gradient(90deg,#f8fbff,#eef6ff); border-bottom:1px solid var(--line); }
    .card-header h2 { margin:0; color:#17324f; font:700 16px 'Space Grotesk', sans-serif; }
    .pill { border-radius:999px; padding:6px 10px; color:var(--blue); background:rgba(21,101,192,.1); font-size:12px; font-weight:700; white-space:nowrap; }
    .pill.green { color:var(--green); background:rgba(31,139,76,.12); }
    .metric { background:#f8fbff; border:1px solid var(--line); border-radius:12px; padding:10px 12px; min-height:58px; }
    .metric small { display:block; margin-bottom:7px; color:var(--muted); font-size:11px; letter-spacing:.12em; text-transform:uppercase; }
    .metric strong { color:#12304a; font-size:16px; }
    .sheet-panel { background:#fff; border:1px solid rgba(15,23,42,.04); border-radius:20px; box-shadow:0 14px 40px rgba(15,23,42,.08); padding:0 14px 14px; }
    [data-testid="stVerticalBlockBorderWrapper"] { background:#fff; border-color:rgba(15,23,42,.06); border-radius:20px; box-shadow:0 14px 40px rgba(15,23,42,.08); }
    .dashboard-marker { height:0; overflow:hidden; margin:0; padding:0; }
    [data-testid="stVerticalBlockBorderWrapper"]:has(.dashboard-marker) { height:300px; min-height:300px; padding:0 16px 14px; overflow:hidden; }
    [data-testid="stVerticalBlockBorderWrapper"]:has(.dashboard-marker) > div { height:100%; }
    .sheet-head { display:flex; justify-content:space-between; align-items:center; padding:16px 8px 8px; gap:16px; }
    .sheet-head h2 { margin:0 0 6px; color:#17324f; font:700 22px 'Space Grotesk', sans-serif; }
    .sheet-head p { margin:0; color:var(--muted); }
    .sheet-badge { background:var(--blue); color:white; border-radius:999px; padding:8px 12px; font-size:12px; font-weight:700; white-space:nowrap; }
    .history-panel { background:#fff; border:1px solid rgba(15,23,42,.04); border-radius:20px; box-shadow:0 14px 40px rgba(15,23,42,.08); overflow:hidden; min-height:220px; }
    .history-body { padding:12px 14px; max-height:260px; overflow-y:auto; }
    .history-row { border:1px solid var(--line); border-radius:10px; padding:9px 11px; background:#f8fbff; margin-bottom:8px; font-size:12px; }
    .history-row strong { display:block; margin-bottom:4px; }
    .version-selected { border-color:var(--blue); background:#eaf3ff; }
    .stButton > button, .stDownloadButton > button { border-radius:10px; font-weight:700; border:1px solid #d8e5f4; min-height:36px; padding:4px 8px; }
    .stButton > button[kind="primary"], .stDownloadButton > button { background:var(--blue); color:#fff; border-color:var(--blue); }
    .action-bar { margin:4px 0 12px; padding:10px; border:1px solid var(--line); border-radius:14px; background:#fbfdff; }
    .action-label { margin:0 0 6px; color:var(--muted); font-size:11px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; }
    .selected-file { margin:6px 0 8px; padding:7px 9px; border:1px solid var(--line); border-radius:8px; background:#f8fbff; color:#17324f; font-size:12px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    div[data-testid="stHorizontalBlock"] { align-items:flex-end; }
    div[data-testid="stDataEditor"] { border:1px solid var(--line); border-radius:14px; overflow:hidden; min-height:600px; }
    div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stDataEditor"]) { width:100%; }
    div[data-testid="stSelectbox"] { margin-bottom:2px; }
    div[data-testid="stFileUploader"] section { padding:4px 8px; min-height:38px; }
    @media (max-width: 700px) { .block-container { padding:16px 12px 24px; } .hero { padding:20px; } .logos { gap:16px; } .logos img { height:48px; max-width:40%; } .divider { height:58px; } .hero h1 { font-size:30px; } .sheet-head { align-items:flex-start; flex-direction:column; } }
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
st.markdown('<div class="section-label">Dashboard central</div>', unsafe_allow_html=True)

options = managers_from_employees(st.session_state.employees)

with st.container():
    manager_col, info_col, update_col, mail_col = st.columns([1.2, 1.2, 1.2, 1.4], gap="medium")
    with manager_col:
        with st.container(border=True):
            st.markdown('<span class="dashboard-marker"></span>', unsafe_allow_html=True)
            card_header("Managers", "Corporate")
            if st.button("General", key="general", use_container_width=True):
                st.session_state.selected_manager = None
                st.session_state.selected_history_lote = None
                st.session_state.selected_budget_version = None
                st.session_state.sheet_records = api_get("budget_actual", []) or []
                st.session_state.history_items = []
                st.rerun()
            manager_pick = st.selectbox("Manager", options, index=None, key="manager_pick", label_visibility="collapsed", placeholder="Buscar por SGI o nombre", format_func=manager_option_label)
            if manager_pick:
                if manager_pick["manager"] != st.session_state.selected_manager:
                    st.session_state.selected_manager = manager_pick["manager"]
                    st.session_state.selected_history_lote = None
                    st.session_state.selected_budget_version = None
                    team = api_get(f'equipo/{quote(manager_pick["manager"], safe="")}', []) or []
                    st.session_state.sheet_records = team
                    st.session_state.history_items = api_get(f'historial/{quote(manager_pick["manager"], safe="")}', []) or []
                    st.rerun()
    with info_col:
        with st.container(border=True):
            st.markdown('<span class="dashboard-marker"></span>', unsafe_allow_html=True)
            card_header("Información General", "Activa", True)
            current = st.session_state.sheet_records
            country = current[0].get("pais") or current[0].get("country") or "-" if current else "-"
            st.markdown('<div style="padding:14px">', unsafe_allow_html=True)
            for label, value in [("País", country), ("Manager seleccionado", next((x["nombre"] for x in options if x["manager"] == st.session_state.selected_manager), "General")), ("Headcount", len(current))]:
                st.markdown(f'<div class="metric"><small>{label}</small><strong>{value}</strong></div><div style="height:8px"></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    with update_col:
        with st.container(border=True):
            st.markdown('<span class="dashboard-marker"></span>', unsafe_allow_html=True)
            card_header("Actualización", "Live")
            st.markdown(f'<div style="padding:14px"><div class="metric"><small>Última actualización</small><strong>{datetime.now().strftime("%d %b %Y, %H:%M")}</strong></div><div style="height:8px"></div><div class="metric"><small>Estado</small><strong>En revisión</strong></div><div style="height:8px"></div><div class="metric"><small>Próxima métrica</small><strong>Compensación</strong></div></div>', unsafe_allow_html=True)
    with mail_col:
        with st.container(border=True):
            st.markdown('<span class="dashboard-marker"></span>', unsafe_allow_html=True)
            card_header("Envío de Correos", "Budget Planning")
            selected_mail_options = st.multiselect("Managers", options, key="selected_mail", label_visibility="collapsed", format_func=manager_option_label, placeholder="Buscar por SGI o nombre")
            if st.button("📧 Enviar Correos", type="primary", use_container_width=True):
                try:
                    result = api_post("enviar_correos", json={"managers": [item["manager"] for item in selected_mail_options]}).json()
                    st.success(result.get("message", "Solicitud enviada."))
                except requests.RequestException as exc:
                    st.error(f"No fue posible enviar los correos: {exc}")

consolidation_slot = st.empty()
top_history_slot = st.empty()
sheet_slot = st.empty()
budget_history_slot = st.empty()

completed_items = api_get("completados", []) or []
budget_versions = api_get("budget_versiones", []) or []


def render_consolidation(target):
    with target.container(border=True):
        card_header("📥 Consolidación de Respuestas", "Budget Planning")
        consolidation_files = st.file_uploader("Selecciona archivos Excel", type=["xlsx"], accept_multiple_files=True, key="consolidation_files")
        consolidation_action, consolidation_status = st.columns([1, 3], gap="medium")
        with consolidation_action:
            consolidate_clicked = st.button("📥 Consolidar Archivos", type="primary", use_container_width=True)
        with consolidation_status:
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
                        st.download_button("Descargar consolidado", consolidated.content, file_name="consolidado.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    except requests.RequestException as exc:
                        st.error(f"No fue posible consolidar: {exc}")


def render_top_history(target):
    with target.container():
        history_col, completed_col = st.columns([1.2, 1], gap="medium")
        with history_col:
            with st.container(border=True):
                card_header("Histórico del Manager", "Auditoría")
                history_rows(st.session_state.history_items)
                selected_lote = st.selectbox("Lote histórico", [item.get("lote_id") for item in st.session_state.history_items if item.get("lote_id")], index=None, label_visibility="collapsed", placeholder="Selecciona una versión")
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
        with completed_col:
            with st.container(border=True):
                card_header("Completados", "Pendientes de sábana")
                history_rows(completed_items)
                if completed_items:
                    st.dataframe(pd.DataFrame(completed_items), use_container_width=True, hide_index=True, height=220)


def render_sheet(target):
    with target.container():
        st.markdown('<div class="sheet-panel"><div class="sheet-head"><div><h2>General</h2><p>Vista consolidada de la organización para Budget Planning 2027</p></div><span class="sheet-badge">Corporate view</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="action-bar">', unsafe_allow_html=True)
        action_one, action_two, action_three, action_four = st.columns([1.05, 1.05, 1.05, 1.35], gap="small")
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
        data = st.data_editor(records_to_frame(st.session_state.sheet_records), use_container_width=True, num_rows="dynamic", height=620, key="budget_editor")
        with st.expander("Datos adicionales del LEFT JOIN"):
            raw_frame = pd.DataFrame(st.session_state.sheet_records)
            if raw_frame.empty:
                st.caption("No hay datos adicionales disponibles.")
            else:
                st.dataframe(raw_frame, use_container_width=True, hide_index=True, height=260)
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
    with target.container():
        with st.container(border=True):
            card_header("Histórico Budget", "Versiones")
            current_label = "Versión actual · Sábana viva"
            if st.button(current_label, key="budget_version_current", use_container_width=True):
                st.session_state.selected_budget_version = None
                st.session_state.sheet_records = api_get("budget_actual", []) or []
                st.rerun()
            for version in budget_versions:
                version_id = version.get("version_id")
                version_label = f'{version.get("fecha_creacion", "Sin fecha")} · {version.get("descripcion") or version_id}'
                if st.button(version_label, key=f"budget_version_{version_id}", use_container_width=True):
                    st.session_state.selected_budget_version = version_id
                    st.session_state.sheet_records = api_get(f"budget_actual/{quote(version_id, safe='')}", []) or []
                    st.rerun()
            if not budget_versions:
                st.caption("No hay versiones registradas todavía.")


render_consolidation(consolidation_slot)
render_top_history(top_history_slot)
render_sheet(sheet_slot)
render_budget_history(budget_history_slot)

with st.expander("Estado de conexión"):
    st.write(f"Backend Flask configurado: {API_URL}")
    st.caption("La interfaz Streamlit consume los endpoints existentes y no modifica el backend.")

st.caption(f"Frontend Streamlit paralelo · Backend Flask: {API_URL}")
