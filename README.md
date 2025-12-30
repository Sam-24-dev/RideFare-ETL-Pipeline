#  RideFare: Pipeline ETL & Predicción de Precios con ML

Proyecto *End-to-End* de Ingeniería de Datos y Analytics 
simulando un entorno real de aplicaciones de transporte (tipo Uber/Lyft).

##  Arquitectura del Proyecto
Este proyecto transforma datos crudos en insights de negocio mediante una arquitectura de 3 etapas:

1.  **Pipeline ETL :** Script de Python (`etl_db.py`) que extrae datos crudos (CSV con ~1.2 Millones de filas), limpia formatos inconsistentes y carga la data optimizada en una **Base de Datos SQLite**.
2.  **Integración SQL:** Extracción de datos para análisis mediante consultas SQL complejas (JOINs) entre tablas de `Viajes` y `Clima`.
3.  **Machine Learning:** Implementación de un modelo *Random Forest Regressor* para predecir la dinámica de precios.

##  Resultados y Desafíos de Ingeniería

### 1. Volumen y Limpieza de Datos
* **Procesamiento:** Se ingirieron 1.2M+ registros.
* **Calidad:** Tras el proceso de limpieza y cruce SQL, se consolidó un dataset final de ~600k viajes verificados.

### 2. Rendimiento del Modelo (Baseline)
* **RMSE:** $9.00 (Margen de error promedio).
* **R² Score:** 0.15 (Baseline).
* **Análisis Técnico:** La correlación baja indica que la `Distancia` y el `Surge Multiplier` son los factores dominantes. La data del `Clima` (unida por hora) añade complejidad/ruido, lo que sugiere la necesidad de datos climáticos más granulares (por minuto) para futuras iteraciones.

### 3. Visualización de Insights

![Gráfico de Feature Importance](imagenes/feature_importance.png)

##  Stack Tecnológico
* **Lenguajes:** Python, SQL.
* **Librerías:** Pandas, Scikit-Learn, SQLite3, Matplotlib/Seaborn, Plotly.
* **Herramientas:** Jupyter Notebook, VS Code.

##  Cómo Ejecutar

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/RideFare-ETL-Pipeline.git

# 2. Instalar dependencias
pip install pandas scikit-learn matplotlib seaborn plotly jupyter

# 3. Ejecutar el ETL (crea la base de datos)
python etl_db.py

# 4. Abrir el notebook de análisis
jupyter notebook RideFare_Analysis_Engineering.ipynb
```

---
Desarrollado por Samir Caizapasto - Estudiante de Ingeniería en Computación ESPOL
