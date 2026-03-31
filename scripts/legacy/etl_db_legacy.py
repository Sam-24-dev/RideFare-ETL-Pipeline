"""
Script ETL para crear una base de datos SQLite con datos de rides y weather.
Este script simula un proceso de Ingeniería de Datos.
"""

import sqlite3
import pandas as pd


def limpiar_nombres_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia los espacios en los nombres de columnas del DataFrame."""
    df.columns = df.columns.str.strip()
    return df


def cargar_csv_a_tabla(conn: sqlite3.Connection, csv_path: str, tabla: str) -> None:
    """Lee un archivo CSV, limpia los nombres de columnas y lo guarda en una tabla SQL."""
    # Leer el archivo CSV
    df = pd.read_csv(csv_path)
    
    # Limpiar espacios en los nombres de columnas
    df = limpiar_nombres_columnas(df)
    
    # Guardar en la base de datos SQLite
    df.to_sql(tabla, conn, if_exists='replace', index=False)


def main():
    # Conectar (o crear) la base de datos SQLite
    conn = sqlite3.connect('ridefare.db')
    
    try:
        # Cargar rides.csv en la tabla 'rides'
        cargar_csv_a_tabla(conn, 'PFDA_rides.csv', 'rides')
        
        # Cargar weather.csv en la tabla 'weather'
        cargar_csv_a_tabla(conn, 'PFDA_weather.csv', 'weather')
        
        # Confirmar los cambios
        conn.commit()
        
        print('Base de datos creada exitosamente')
        
    finally:
        # Cerrar la conexión
        conn.close()


if __name__ == '__main__':
    main()
