const managersList = document.getElementById('listaManagers');
const managerSeleccionado = document.getElementById('managerSeleccionado');
const headcount = document.getElementById('headcount');
const timestamp = document.getElementById('timestamp');
const tableBody = document.querySelector('#tablaEquipo tbody');
const searchInput = document.getElementById('buscadorManagers');
const btnGeneral = document.getElementById('btnMostrarGeneral');
const btnNuevoRegistro = document.getElementById('btnNuevoRegistro');
const btnGuardar = document.getElementById('btnGuardar');
const historyEmptyState = document.getElementById('historyEmptyState');
const listaHistorico = document.getElementById('listaHistorico');
const archivoActualizarSabana = document.getElementById('archivoActualizarSabana');
const listaHistoricoBudget = document.getElementById('listaHistoricoBudget');
const budgetHistoryEmptyState = document.getElementById('budgetHistoryEmptyState');

let managerOptions = [];
let selectedManager = null;
let currentTeam = [];
let allEmployees = [];
let rowHeight = 44;
let renderScheduled = false;
let selectedHistory = null;
let selectedHistoryApproved = false;
let selectedManagersForMail = [];


function formatDateTime() {
    const now = new Date();
    return now.toLocaleString('es-MX', {
        dateStyle: 'medium',
        timeStyle: 'short'
    });
}

function normalizeText(value) {
    return String(value ?? '').trim().toLowerCase();
}

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function toNumber(value) {
    if (value === null || value === undefined || value === '') {
        return null;
    }

    const numeric = Number(String(value).replace(/[%,$\s]/g, ''));
    return Number.isFinite(numeric) ? numeric : null;
}

function findValue(source, keys) {
    const item = source ?? {};
    for (const key of keys) {
        const value = item[key];
        if (value !== undefined && value !== null && String(value).trim() !== '') {
            return value;
        }
    }
    return '';
}

function parseDate(value) {
    if (!value) {
        return null;
    }

    const normalized = String(value).trim();
    const parsed = new Date(normalized);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function calculateAntiguedad(fechaIngreso) {
    const parsed = parseDate(fechaIngreso);
    if (!parsed) {
        return '';
    }

    const today = new Date();
    const years = today.getFullYear() - parsed.getFullYear();
    const monthDiff = today.getMonth() - parsed.getMonth();
    const completeYears = monthDiff < 0 || (monthDiff === 0 && today.getDate() < parsed.getDate())
        ? years - 1
        : years;

    return completeYears >= 0 ? `${completeYears} años` : '';
}

function calculateEdad(fechaNacimiento) {
    const parsed = parseDate(fechaNacimiento);
    if (!parsed) {
        return '';
    }

    const today = new Date();
    let age = today.getFullYear() - parsed.getFullYear();
    const monthDiff = today.getMonth() - parsed.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < parsed.getDate())) {
        age -= 1;
    }

    return age >= 0 ? `${age}` : '';
}

function createBlankRecord() {
    return {
        sgi: '',
        nombre: '',
        bu: '',
        tipoEmpleado: '',
        cco: '',
        puesto: '',
        area: '',
        fechaIngreso: '',
        antiguedad: '',
        fechaNacimiento: '',
        edad: '',
        genero: '',
        sd: '',
        sm: '',
        incSalarial: '',
        promocion: '',
        nivelacion: '',
        comentarios: '',
        isNewRecord: true
    };
}

function normalizeRecord(empleado) {
    if (!empleado || typeof empleado !== 'object') {
        return createBlankRecord();
    }

    const fechaIngreso = findValue(empleado, ['fecha_ingreso', 'fechaIngreso', 'ingreso', 'f_ingreso']);
    const fechaNacimiento = findValue(empleado, ['fecha_nacimiento', 'fechaNacimiento', 'f_nacimiento']);
    const baseSalary = toNumber(findValue(empleado, ['budget_salario_mensual', 'sm', 'salario_mensual', 'salario_mensual_base', 'salary', 'salario']));

    return {
        sgi: findValue(empleado, ['sgi', 'id']),
        nombre: findValue(empleado, ['nombre_completo', 'nombre', 'full_name']),
        bu: findValue(empleado, ['compania', 'bu', 'company']),
        tipoEmpleado: findValue(empleado, ['tipo_empleado', 'tipo', 'tipoEmpleado']),
        cco: findValue(empleado, ['ceco', 'cco', 'centro_costo']),
        puesto: findValue(empleado, ['puesto', 'job_title']),
        area: findValue(empleado, ['area', 'filiere', 'filiere_desc', 'division']),
        fechaIngreso: fechaIngreso || '',
        antiguedad: calculateAntiguedad(fechaIngreso) || findValue(empleado, ['antiguedad', 'years_service']) || '',
        fechaNacimiento: fechaNacimiento || '',
        edad: calculateEdad(fechaNacimiento) || findValue(empleado, ['edad']) || '',
        genero: findValue(empleado, ['genero', 'sexo', 'gender']),
        sd: findValue(empleado, ['sd', 'salario_diario', 'salario_diario_base']),
        sm: baseSalary !== null ? baseSalary : findValue(empleado, ['budget_salario_mensual', 'sm', 'salario_mensual', 'salario_mensual_base', 'salary']),
        incSalarial: findValue(empleado, ['inc_salarial', 'incSalarial', 'incremento_salarial', 'inc']) || '',
        promocion: findValue(empleado, ['promocion', 'promotion']) || '',
        nivelacion: findValue(empleado, ['nivelacion', 'nivelacion_salarial']) || '',
        comentarios: findValue(empleado, ['comentarios', 'comments']) || '',
        isNewRecord: Boolean(empleado.isNewRecord)
    };
}

function getManagerLabel(item) {
    return findValue(item, [
        'manager_name',
        'manager_nombre',
        'nombre_manager',
        'nombre_gerente',
        'gerente_nombre',
        'managerFullName',
        'nombre_supervisor',
        'supervisor_nombre',
        'nombre_jefe',
        'jefe_nombre',
        'display_name',
        'managerDisplay'
    ]) || findValue(item, ['manager', 'supervisor', 'jefe', 'gerente']) || findValue(item, ['nombre_completo', 'nombre', 'full_name']) || '';
}

function getManagerKey(item) {
    return findValue(item, ['manager', 'manager_sgi', 'sgi_manager', 'manager_id', 'supervisor', 'jefe', 'gerente']) || '';
}

function getManagerSgi(item) {
    return findValue(item, ['manager_sgi', 'sgi_manager', 'manager_id', 'sg_manager']) || '';
}

function buildManagerOptions(data) {
    const employees = Array.isArray(data) ? data : [];
    const uniqueManagers = new Map();

    employees.forEach((item) => {
        const rawManager = getManagerKey(item);
        const managerValue = normalizeText(rawManager);
        const sgiValue = normalizeText(getManagerSgi(item));
        const nombre = getManagerLabel(item);
        const nombreValue = normalizeText(nombre);

        if (!managerValue || !nombreValue || managerValue === sgiValue) {
            return;
        }

        if (!uniqueManagers.has(rawManager)) {
            uniqueManagers.set(rawManager, {
                manager: rawManager,
                sgi: getManagerSgi(item) || rawManager,
                nombre
            });
        }
    });

    return Array.from(uniqueManagers.values()).sort((a, b) => {
        const nameA = normalizeText(a.nombre || a.manager);
        const nameB = normalizeText(b.nombre || b.manager);
        return nameA.localeCompare(nameB, 'es', { sensitivity: 'base' });
    });
}

function filterManagers() {
    if (!managersList) {
        return;
    }

    const query = normalizeText(searchInput?.value);

    if (!query) {
        managersList.innerHTML = '';
        return;
    }

    const visibleManagers = managerOptions.filter((option) => {
        const hayCoincidencia = normalizeText(option.sgi).includes(query) ||
            normalizeText(option.nombre).includes(query) ||
            normalizeText(option.manager).includes(query) ||
            normalizeText(`${option.nombre} ${option.manager} ${option.sgi}`).includes(query);
        return hayCoincidencia;
    });

    if (!visibleManagers.length) {
        managersList.innerHTML = '<p class="state-text">No se encontraron managers con ese criterio.</p>';
        return;
    }

    managersList.innerHTML = '';

    visibleManagers.forEach((option) => {
        const button = createManagerButton(option);
        managersList.appendChild(button);
    });
}

function createManagerButton(option) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'manager-item';
    button.innerHTML = `
        <span class="manager-info">
            <span class="manager-name">${escapeHtml(option.nombre || option.manager)}</span>
            <span class="manager-meta">${escapeHtml(option.sgi || option.manager)}</span>
        </span>
        <span class="manager-badge">Ver equipo</span>
    `;

    button.classList.toggle('active', selectedManager === option.manager);

    button.addEventListener('click', () => {
        document.querySelectorAll('.manager-item').forEach((item) => item.classList.remove('active'));
        button.classList.add('active');
        selectedManager = option.manager;
        managerSeleccionado.textContent = option.nombre || option.manager;
        if (searchInput) {
            searchInput.value = option.nombre || option.manager;
        }
        headcount.textContent = 'Cargando...';
        managersList.innerHTML = '';
        loadTeam(option.manager);
    });

    return button;
}

function renderManagers(managers) {
    if (!managersList) {
        return;
    }

    managerOptions = Array.isArray(managers) ? managers : [];

    if (!managerOptions.length) {
        managersList.innerHTML = '<p class="state-text">No hay managers disponibles.</p>';
        return;
    }

    filterManagers();
}

function computePercentages(record) {
    const inc = toNumber(record?.incSalarial);
    const promocion = toNumber(record?.promocion);
    const nivelacion = toNumber(record?.nivelacion);
    const baseSalary = toNumber(record?.sm);
    const suma = [inc, promocion, nivelacion].reduce((total, value) => total + (value ?? 0), 0);

    if (baseSalary === null || Number.isNaN(baseSalary)) {
        return { suma, nuevoSalario: null };
    }

    const nuevoSalario = baseSalary + (baseSalary * suma / 100);
    return { suma, nuevoSalario };
}

function updateRowSummary(row, record) {
    const summary = row.querySelector('[data-summary="suma"]');
    const salaryCell = row.querySelector('[data-summary="salario"]');
    const antiguedadCell = row.querySelector('[data-display="antiguedad"]');
    const edadCell = row.querySelector('[data-display="edad"]');

    const { suma, nuevoSalario } = computePercentages(record);

    if (summary) {
        summary.textContent = Number.isFinite(suma) ? `${suma.toFixed(2)}%` : '-';
    }

    if (salaryCell) {
        salaryCell.textContent = nuevoSalario === null ? '-' : new Intl.NumberFormat('es-MX', {
            style: 'currency',
            currency: 'MXN',
            maximumFractionDigits: 2
        }).format(nuevoSalario);
    }

    if (antiguedadCell) {
        antiguedadCell.textContent = record.antiguedad || '-';
    }

    if (edadCell) {
        edadCell.textContent = record.edad || '-';
    }
}

function attachRowListeners() {
    if (!tableBody) {
        return;
    }

    tableBody.querySelectorAll('tr').forEach((row) => {
        if (!row.dataset.rowIndex) {
            return;
        }

        const rowIndex = Number(row.dataset.rowIndex);
        row.querySelectorAll('input[data-field]').forEach((input) => {
            input.addEventListener('input', () => {
                const field = input.dataset.field;
                currentTeam[rowIndex][field] = input.value;

                if (field === 'fechaIngreso') {
                    currentTeam[rowIndex].antiguedad = calculateAntiguedad(input.value);
                }

                if (field === 'fechaNacimiento') {
                    currentTeam[rowIndex].edad = calculateEdad(input.value);
                }

                updateRowSummary(row, currentTeam[rowIndex]);
            });
        });
    });
}

function buildRowMarkup(empleado, index) {
    const readOnly = selectedHistoryApproved === true;
    const disabledAttr = readOnly ? 'disabled' : '';
    const { suma, nuevoSalario } = computePercentages(empleado);
    const formatSuma = Number.isFinite(suma) ? `${suma.toFixed(2)}%` : '-';
    const formatSalario = nuevoSalario === null ? '-' : new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN',
        maximumFractionDigits: 2
    }).format(nuevoSalario);

    return `
        <tr data-row-index="${index}">
            <td><input type="text" value="${escapeHtml(empleado.sgi)}" data-field="sgi" aria-label="SGI"></td>
            <td><input type="text" value="${escapeHtml(empleado.nombre)}" data-field="nombre" aria-label="Nombre"></td>
            <td><input type="text" value="${escapeHtml(empleado.bu)}" data-field="bu" aria-label="BU"></td>
            <td><input type="text" value="${escapeHtml(empleado.tipoEmpleado)}" data-field="tipoEmpleado" aria-label="Tipo de empleado"></td>
            <td><input type="text" value="${escapeHtml(empleado.cco)}" data-field="cco" aria-label="CCO"></td>
            <td><input type="text" value="${escapeHtml(empleado.puesto)}" data-field="puesto" aria-label="Puesto"></td>
            <td><input type="text" value="${escapeHtml(empleado.area)}" data-field="area" aria-label="Área"></td>
            <td><input type="text" value="${escapeHtml(empleado.fechaIngreso)}" data-field="fechaIngreso" aria-label="Fecha ingreso"></td>
            <td data-display="antiguedad">${escapeHtml(empleado.antiguedad || '-')}</td>
            <td><input type="text" value="${escapeHtml(empleado.fechaNacimiento)}" data-field="fechaNacimiento" aria-label="Fecha nacimiento"></td>
            <td data-display="edad">${escapeHtml(empleado.edad || '-')}</td>
            <td><input type="text" value="${escapeHtml(empleado.genero)}" data-field="genero" aria-label="Género"></td>
            <td><input type="text" value="${escapeHtml(empleado.sd)}" data-field="sd" aria-label="SD"></td>
            <td><input type="text" value="${escapeHtml(empleado.sm)}" data-field="sm" aria-label="SM"></td>
            <td><input type="text" value="${escapeHtml(empleado.incSalarial)}" data-field="incSalarial" aria-label="Incremento salarial" ${disabledAttr}></td>
            <td><input type="text" value="${escapeHtml(empleado.promocion)}" data-field="promocion" aria-label="Promoción" ${disabledAttr}></td>
            <td><input type="text" value="${escapeHtml(empleado.nivelacion)}" data-field="nivelacion" aria-label="Nivelación" ${disabledAttr}></td>
            <td class="suma-porcentual" data-summary="suma">${formatSuma}</td>
            <td class="nuevo-salario" data-summary="salario">${formatSalario}</td>
            <td><input type="text" value="${escapeHtml(empleado.comentarios)}" data-field="comentarios" aria-label="Comentarios" ${disabledAttr}></td>
        </tr>
    `;
}

function getVisibleRowRange() {
    const wrapper = document.querySelector('.table-wrapper');
    if (!wrapper || !currentTeam.length) {
        return { start: 0, end: 0 };
    }

    const scrollTop = wrapper.scrollTop;
    const viewportHeight = wrapper.clientHeight || 600;
    const start = Math.max(0, Math.floor(scrollTop / rowHeight) - 12);
    const end = Math.min(currentTeam.length, Math.ceil((scrollTop + viewportHeight) / rowHeight) + 12);

    return { start, end };
}

function renderVisibleRows() {
    if (!tableBody || !currentTeam.length) {
        return;
    }

    const { start, end } = getVisibleRowRange();
    const topSpacerHeight = start * rowHeight;
    const bottomSpacerHeight = Math.max(0, (currentTeam.length - end) * rowHeight);

    let markup = '';

    if (topSpacerHeight > 0) {
        markup += `<tr><td colspan="20" style="padding:0;border:0;height:${topSpacerHeight}px"></td></tr>`;
    }

    for (let index = start; index < end; index += 1) {
        markup += buildRowMarkup(currentTeam[index], index);
    }

    if (bottomSpacerHeight > 0) {
        markup += `<tr><td colspan="20" style="padding:0;border:0;height:${bottomSpacerHeight}px"></td></tr>`;
    }

    tableBody.innerHTML = markup;
    attachRowListeners();
}

function scheduleVisibleRowsRender() {
    if (renderScheduled) {
        return;
    }

    renderScheduled = true;
    window.requestAnimationFrame(() => {
        renderVisibleRows();
        renderScheduled = false;
    });
}

function renderTeam(team) {

    const readOnly =
    selectedHistoryApproved === true;

    if (!tableBody) {
        return;
    }

    currentTeam = Array.isArray(team) ? team.map((empleado) => normalizeRecord(empleado)) : [];

    if (!currentTeam.length) {
        tableBody.innerHTML = '<tr><td colspan="20" class="empty-state">No hay subordinados para este manager.</td></tr>';
        headcount.textContent = '0';
        return;
    }

    headcount.textContent = currentTeam.length;
    tableBody.innerHTML = '<tr><td colspan="20" class="empty-state">Cargando tabla...</td></tr>';

    const wrapper = document.querySelector('.table-wrapper');
    if (wrapper) {
        wrapper.removeEventListener('scroll', scheduleVisibleRowsRender);
        wrapper.addEventListener('scroll', scheduleVisibleRowsRender, { passive: true });
    }

    window.setTimeout(() => {
        renderVisibleRows();
    }, 0);
}

function renderManagersFromEmployees(data) {
    const managers = buildManagerOptions(data);
    renderManagers(managers);
}

async function loadManagers() {
    if (allEmployees.length) {
        renderManagersFromEmployees(allEmployees);
        return;
    }

    try {
        const response = await fetch('http://127.0.0.1:5000/empleados');
        if (!response.ok) {
            throw new Error('No se pudieron cargar los managers');
        }

        const data = await response.json();
        allEmployees = Array.isArray(data) ? data : [];
        renderManagersFromEmployees(allEmployees);
        renderMailManagers();
    } catch (error) {
        managersList.innerHTML = '<p class="state-text">No fue posible cargar la lista de managers.</p>';
        console.error(error);
    }
}

function renderMailManagers(searchTerm = '') {

    const container =
        document.getElementById(
            'mailManagersList'
        );

    if (!container) {
        return;
    }

    const managers =
        [...new Set(
            allEmployees
                .map(
                    employee => employee.manager
                )
                .filter(Boolean)
        )]
        .filter(manager =>
            manager
                .toLowerCase()
                .includes(
                    searchTerm.toLowerCase()
                )
        )
        .sort();

    container.innerHTML =
        managers.map(manager => `

            <label
                class="mail-manager-item">

                <input
                    type="checkbox"
                    class="mail-manager-checkbox"
                    value="${manager}"
                    ${
                        selectedManagersForMail.includes(manager)
                            ? 'checked'
                            : ''
                    }>

                <span>
                    ${manager}
                </span>

            </label>

        `).join('');

    container
        .querySelectorAll(
            '.mail-manager-checkbox'
        )
        .forEach(checkbox => {

            checkbox.addEventListener(
                'change',
                event => {

                    const manager =
                        event.target.value;

                    if (
                        event.target.checked
                    ) {

                        if (
                            !selectedManagersForMail.includes(manager)
                        ) {

                            selectedManagersForMail.push(
                                manager
                            );

                        }

                    } else {

                        selectedManagersForMail =
                            selectedManagersForMail
                            .filter(
                                item =>
                                    item !== manager
                            );

                    }

                }
            );

        });

}

function initializeMailSearch() {

    const searchInput =
        document.getElementById(
            'mailSearch'
        );

    if (!searchInput) {
        return;
    }

    searchInput.addEventListener(
        'input',
        event => {

            renderMailManagers(
                event.target.value
            );

        }
    );

}

async function loadGeneral() {
    await loadBudgetSheet();
}

async function loadBudgetSheet(versionId = null) {
    const endpoint = versionId
        ? `http://127.0.0.1:5000/budget_actual/${encodeURIComponent(versionId)}`
        : 'http://127.0.0.1:5000/budget_actual';

    try {
        const response = await fetch(endpoint);
        if (!response.ok) throw new Error('No se pudo cargar la sábana Budget');
        const data = await response.json();
        selectedManager = null;
        managerSeleccionado.textContent = 'General';
        const paisSeleccionado =
            document.getElementById('paisSeleccionado');

        if (paisSeleccionado) {
            paisSeleccionado.textContent = '-';
        }
        renderTeam(data);
        clearHistory();

        if (searchInput) {
            searchInput.value = '';
        }
        filterManagers();
    } catch (error) {
        console.error(error);
        if (tableBody) tableBody.innerHTML = '<tr><td colspan="20" class="empty-state">No fue posible cargar la sábana.</td></tr>';
    }
}

async function loadTeam(manager) {
    try {
        const response = await fetch(`http://127.0.0.1:5000/equipo/${encodeURIComponent(manager)}`);
        if (!response.ok) {
            throw new Error('No se pudo cargar el equipo');
        }

        const data = await response.json();
        const paisSeleccionado = document.getElementById('paisSeleccionado');
        if (paisSeleccionado) {
            const pais = data.length > 0 ? findValue(data[0], ['pais', 'country']) : '';
            paisSeleccionado.textContent = pais || '-';
        }
        renderTeam(data);
        await loadHistory(manager);
    } catch (error) {
        tableBody.innerHTML = '<tr><td colspan="20" class="empty-state">No fue posible cargar el equipo.</td></tr>';
        console.error(error);
    }
}

function clearHistory() {

    if (listaHistorico) {
        listaHistorico.innerHTML = '';
    }

    if (historyEmptyState) {
        historyEmptyState.textContent =
            'Seleccione un manager para ver el historial.';
    }

    selectedHistory = null;

    selectedHistoryApproved = false;

    const historyActions =
        document.getElementById(
            "historyActions"
        );

    if (historyActions) {

        historyActions.style.display =
            "none";

    }

    const btnAprobar =
        document.getElementById(
            "btnAprobar"
        );

    if (btnAprobar) {

        btnAprobar.disabled = false;

        btnAprobar.textContent =
            "Aprobar";

    }

}

async function loadHistory(manager) {

    if (!manager || !listaHistorico || !historyEmptyState) {
        clearHistory();
        return;
    }

    try {

        const response = await fetch(
            `http://127.0.0.1:5000/historial/${encodeURIComponent(manager)}`
        );

        if (!response.ok) {
            throw new Error('No se pudo cargar el historial');
        }

        const data = await response.json();

        const historyItems =
            Array.isArray(data) ? data : [];

        if (!historyItems.length) {

            historyEmptyState.textContent =
                'No hay historial para este manager todavía.';

            listaHistorico.innerHTML = '';

            return;

        }

        historyEmptyState.textContent =
            'Últimos cambios guardados';

        listaHistorico.innerHTML = historyItems.map((item) => {

            const timestampValue =
                item.timestamp
                    ? new Date(item.timestamp)
                        .toLocaleString('es-MX', {
                            dateStyle: 'medium',
                            timeStyle: 'short'
                        })
                    : 'Sin fecha';

            return `
                    <div
                        class="history-item ${item.aprobado ? 'approved' : ''}"
                        data-lote="${item.lote_id}">

                    <strong>
                        ${escapeHtml(item.manager || manager)}
                    </strong>

                    <span>
                        ${escapeHtml(timestampValue)}
                    </span>

                    <span>
                        ${(item.registros?.length || 0)}
                        registros
                    </span>

                </div>
            `;

        }).join('');

        listaHistorico
            .querySelectorAll('.history-item')
            .forEach(item => {

                item.addEventListener('click', async () => {

                    document
                    .getElementById("historyActions")
                    .style.display = "flex";

                    document
                        .querySelectorAll('.history-item')
                        .forEach(x =>
                            x.classList.remove('active')
                        );

                    item.classList.add('active');

                    const loteId =
                        item.dataset.lote;

                    selectedHistory = loteId;

                    if (loteId) {

                        await loadHistoryDetail(loteId);

                    }

                });

            });

    } catch (error) {

        console.error(error);

        historyEmptyState.textContent =
            'No fue posible cargar el historial.';

        listaHistorico.innerHTML = '';

    }

}

async function loadCompleted() {

    try {

        const response =
            await fetch(
                "http://127.0.0.1:5000/completados"
            );

        const data =
            await response.json();

        renderCompleted(data);

    }
    catch (error) {

        console.error(
            "Error cargando completados",
            error
        );

    }

}

function renderCompleted(items) {

    const container =
        document.getElementById(
            "listaCompletados"
        );

    const emptyState =
        document.getElementById(
            "completedEmptyState"
        );

    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (!items.length) {

        if (emptyState) {

            emptyState.style.display =
                "block";

        }

        return;

    }

    if (emptyState) {

        emptyState.style.display =
            "none";

    }

    items.forEach(item => {

        const card =
            document.createElement("div");

        card.className =
            "history-item approved";

        card.dataset.lote =
            item.lote_id;

        card.innerHTML = `
            <strong>
                ${item.manager}
            </strong>
            <br>
            <small>
                ${new Date(
                    item.fecha_registro
                ).toLocaleString()}
            </small>
        `;

        container.appendChild(card);

    });

}

async function loadHistoryDetail(loteId) {

    try {

        const response = await fetch(
            `http://127.0.0.1:5000/historial_detalle/${loteId}`
        );

        const data = await response.json();

        selectedHistoryApproved =
            data.length > 0 &&
            data[0].aprobado === true;

        if (selectedHistoryApproved) {

            lockHistoricalVersion();

        }

        currentTeam = data;

        renderTeam(data);

    }
    catch(error){

        console.error(error);

    }

}

async function saveChanges() {
    if (!btnGuardar) {
        return;
    }

    const managerName = selectedManager || 'General';   
    console.log("CURRENT TEAM");
    console.log(currentTeam);   

    const payload = {
        manager: managerName,
        registros: currentTeam
    };

    const setStatus = (message) => {
        if (historyEmptyState) {
            historyEmptyState.textContent = message;
        }
    };

    try {
        const response = await fetch('http://127.0.0.1:5000/guardar_registro', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error('No se pudo guardar la información');
        }

        const result = await response.json();
        setStatus(result.message || 'Cambios guardados correctamente');

        if (selectedManager) {
            await loadHistory(selectedManager);
        }
    } catch (error) {
        console.error(error);
        localStorage.setItem('budget-planning-draft', JSON.stringify(payload));

        setStatus('Reintentando guardar...');
        try {
            const retryResponse = await fetch('http://127.0.0.1:5000/guardar_registro', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (retryResponse.ok) {
                const retryResult = await retryResponse.json();
                setStatus(retryResult.message || 'Cambios guardados correctamente');
                return;
            }
        } catch (retryError) {
            console.error(retryError);
        }

        setStatus('El guardado quedó pendiente localmente. Revisa la conexión del backend.');
    }
}

function initialize() {
    if (timestamp) {
        timestamp.textContent = formatDateTime();
    }

    if (searchInput) {
        searchInput.addEventListener('input', filterManagers);
    }

    if (btnGeneral) {
        btnGeneral.addEventListener('click', () => {
            selectedManager = null;
            if (searchInput) {
                searchInput.value = '';
            }
            managerSeleccionado.textContent = 'General';
            headcount.textContent = 'Cargando...';
            loadGeneral();
        });
    }

    if (btnNuevoRegistro) {
        btnNuevoRegistro.addEventListener('click', () => {
            currentTeam.unshift(createBlankRecord());
            renderTeam(currentTeam);
            if (historyEmptyState) {
                historyEmptyState.textContent = 'Nuevo registro listo para guardar.';
            }
        });
    }

    if (btnGuardar) {
        btnGuardar.addEventListener('click', saveChanges);
    }

    loadManagers();
    loadGeneral();
    loadCompleted();
    initializeMailSearch();
}

async function approveHistory() {

    console.log("BOTON APROBAR");
    console.log(selectedHistory);

    if (!selectedHistory) {
        return;
    }

    const response =
        await fetch(
            `http://127.0.0.1:5000/aprobar/${selectedHistory}`,
            {
                method: "POST"
            }
        );

    const result =
        await response.json();

    if (result.ok) {

        lockHistoricalVersion();

    }

}

document
    .getElementById("btnAprobar")
    ?.addEventListener(
        "click",
        approveHistory
    );

document
    .getElementById("btnExcel")
    ?.addEventListener(
        "click",
        () => {

            if (!selectedHistory) {

                alert(
                    "Selecciona un histórico primero."
                );

                return;

            }

            window.open(
                `http://127.0.0.1:5000/excel/${selectedHistory}`,
                "_blank"
            );

        }
    );

document
    .getElementById("btnExcelActual")
    ?.addEventListener(
        "click",
        downloadCurrentSheet
    );

document
    .getElementById("btnEnviarCorreos")
    ?.addEventListener(
        "click",
        sendManagersForMail
    );
    
function lockHistoricalVersion() {

    selectedHistoryApproved = true;

    document
        .querySelectorAll(
            "#tablaEquipo input"
        )
        .forEach(input => {

            input.disabled = true;

            input.style.background =
                "#f5f5f5";

            input.style.cursor =
                "not-allowed";

        });

    const btnGuardar =
        document.getElementById(
            "btnGuardar"
        );

    const btnNuevoRegistro =
        document.getElementById(
            "btnNuevoRegistro"
        );

    if(btnGuardar){

        btnGuardar.disabled = true;

        btnGuardar.style.opacity = "0.5";

    }

    if(btnNuevoRegistro){

        btnNuevoRegistro.disabled = true;

        btnNuevoRegistro.style.opacity = "0.5";

    }

    const btnAprobar =
        document.getElementById(
            "btnAprobar"
        );

    if(btnAprobar){

        btnAprobar.disabled = true;

        btnAprobar.textContent =
            "✔ Aprobado";

    }

}

async function downloadCurrentSheet() {

    try {

        const response =
            await fetch(
                "http://127.0.0.1:5000/excel_actual",
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify({
                        manager:
                            selectedManager ||
                            "General",

                        registros:
                            currentTeam
                    })
                }
            );

        if (!response.ok) {

            throw new Error(
                "No se pudo generar el Excel"
            );

        }

        const blob =
            await response.blob();

        const url =
            window.URL.createObjectURL(
                blob
            );

        const a =
            document.createElement("a");

        a.href = url;

        a.download =
            selectedManager
                ? `Budget_${selectedManager}.xlsx`
                : "Budget_General.xlsx";

        document.body.appendChild(a);

        a.click();

        a.remove();

        window.URL
            .revokeObjectURL(url);

    }
    catch(error){

        console.error(error);

        alert(
            "Error al generar el Excel"
        );

    }

}

async function sendManagersForMail() {

    try {

        const response =
            await fetch(
                "http://127.0.0.1:5000/enviar_correos",
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify({
                        managers:
                            selectedManagersForMail
                    })
                }
            );

        const result =
            await response.json();

        console.log(result);

        alert(
            "Solicitud enviada."
        );

    }
    catch(error){

        console.error(error);

    }

}

async function consolidarExcels() {

    const files =
        document.getElementById(
            "excelFiles"
        ).files;

    if (!files.length) {

        alert(
            "Selecciona al menos un archivo."
        );

        return;

    }

    const formData =
        new FormData();

    for (const file of files) {

        formData.append(
            "files",
            file
        );

    }

    try {

        const response =
            await fetch(
                "http://127.0.0.1:5000/consolidar_excels",
                {
                    method: "POST",
                    body: formData
                }
            );

        if (!response.ok) {

            throw new Error(
                "Error al consolidar"
            );

        }

        alert(
            "✅ Consolidación completada correctamente"
        );

        window.open(
            "http://127.0.0.1:5000/descargar_consolidado",
            "_blank"
        );

    }
    catch(error){

        console.error(error);

        alert(
            "❌ Error al consolidar archivos"
        );

    }

}

document
    .getElementById(
        "btnConsolidar"
    )
    ?.addEventListener(
        "click",
        consolidarExcels
    );


async function actualizarSabana() {
    archivoActualizarSabana?.click();
}

async function enviarActualizacionSabana(file) {
    const formData = new FormData();
    formData.append('file', file);
    const boton = document.getElementById('btnActualizarSabana');
    const textoOriginal = boton.textContent;
    boton.disabled = true;
    boton.textContent = 'Procesando...';
    try {
        const response =
            await fetch(
                "http://127.0.0.1:5000/actualizar_sabana",
                {
                    method: "POST",
                    body: formData
                }
            );

        const result =
            await response.json();

        if (!response.ok || !result.success) {
            throw new Error(result.error || 'Error actualizando sábana');
        }
        alert(`✅ Sábana actualizada correctamente\n\nVersión generada: ${result.version_id}\nRegistros actualizados: ${result.registros_actualizados}`);
        cargarHistoricoBudget();

    }
    catch(error){

        console.error(error);

        alert(`❌ ${error.message}`);
    } finally {
        boton.disabled = false;
        boton.textContent = textoOriginal;

    }

}

document
    .getElementById(
        "btnActualizarSabana"
    )
    ?.addEventListener(
        "click",
        actualizarSabana
    );

archivoActualizarSabana?.addEventListener('change', () => {
    const file = archivoActualizarSabana.files[0];
    if (file) enviarActualizacionSabana(file);
    archivoActualizarSabana.value = '';
});

async function cargarHistoricoBudget() {
    if (!listaHistoricoBudget || !budgetHistoryEmptyState) return;
    try {
        const response = await fetch('http://127.0.0.1:5000/budget_versiones');
        if (!response.ok) throw new Error('No se pudieron cargar las versiones');
        const versiones = await response.json();
        budgetHistoryEmptyState.textContent = versiones.length
            ? 'Versiones registradas'
            : 'No hay versiones registradas todavía.';
        listaHistoricoBudget.innerHTML = `
            <div class="history-item active" data-budget-version="">
                <strong>Versión actual</strong>
                <span>Sábana viva</span>
                <span>Última actualización</span>
            </div>
        ` + versiones.map((version) => `
            <div class="history-item" data-budget-version="${escapeHtml(version.version_id)}">
                <strong>${escapeHtml(new Date(version.fecha_creacion).toLocaleString('es-MX'))}</strong>
                <span>${escapeHtml(version.version_id)}</span>
                <span>${escapeHtml(version.descripcion || '')}</span>
            </div>
        `).join('');
        listaHistoricoBudget.querySelectorAll('[data-budget-version]').forEach((item) => {
            item.addEventListener('click', async () => {
                listaHistoricoBudget.querySelectorAll('.history-item').forEach((entry) => entry.classList.remove('active'));
                item.classList.add('active');
                await loadBudgetSheet(item.dataset.budgetVersion || null);
            });
        });
    } catch (error) {
        budgetHistoryEmptyState.textContent = 'No fue posible cargar las versiones.';
        console.error(error);
    }
}

initialize();
cargarHistoricoBudget();
