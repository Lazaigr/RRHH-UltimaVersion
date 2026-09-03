# Frontend Streamlit paralelo

Esta versión es una capa visual paralela. No reemplaza ni modifica el frontend HTML/CSS/JavaScript ni el backend Flask.

## Arranque automático recomendado

Desde `C:\Users\L8726088\B2027` instala las dependencias del frontend en un entorno separado:

```powershell
python -m pip install -r streamlit_requirements.txt
```

Después inicia únicamente Streamlit:

```powershell
streamlit run streamlit_app.py
```

La configuración local deja Streamlit en `http://localhost:8501`. Al comenzar, el frontend consulta `http://127.0.0.1:5000/`. Si Flask no responde, inicia automáticamente `backend/app.py` con su directorio de trabajo correcto. Si ya responde, no inicia otro proceso.

## Arranque manual en dos terminales

También puedes conservar dos puestos independientes:

Terminal 1:

```powershell
cd C:\Users\L8726088\B2027\backend
python app.py
```

Terminal 2:

```powershell
cd C:\Users\L8726088\B2027
streamlit run streamlit_app.py
```

En ese caso Streamlit detecta Flask en el puerto `5000` y no hace nada adicional.

La aplicación usa `http://127.0.0.1:5000` por defecto. Para otro backend:

```powershell
$env:FLASK_API_URL = "http://127.0.0.1:5000"
streamlit run streamlit_app.py
```

## Cobertura visual y funcional

- Dashboard horizontal con cuatro cards: Managers, Información General, Actualización y Envío de Correos.
- Logos corporativos, encabezados azules, pills, métricas y tabla tipo sábana.
- Sábana editable mediante `st.data_editor`, con Nuevo Registro, Guardar, Excel y Actualizar Sábana.
- Tabs para Histórico del Manager, Completados, Consolidación e Histórico Budget.
- Consumo de los endpoints Flask existentes, sin consultas SQL ni lógica de negocio duplicada.
