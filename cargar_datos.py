import pandas as pd
from sqlalchemy import create_engine, inspect # Importamos 'inspect' para verificar

# --- CONFIGURACIÓN ---
CSV_FILE = 'demo.csv'        # El archivo que acabamos de crear
DB_FILE = 'mi_base.db'     # El nombre de la base de datos que se creará
TABLE_NAME = 'ventas'        # El nombre que tendrá la tabla dentro de la BD

def cargar_datos():
    """
    Lee un CSV y lo carga en una base de datos SQLite.
    Si la tabla ya existe, la reemplaza.
    """
    print(f"Iniciando carga de datos desde {CSV_FILE}...")
    
    # 1. Leer el CSV con Pandas
    try:
        df = pd.read_csv(CSV_FILE)
        print("CSV leído correctamente:")
        print(df.head()) # Muestra las primeras 5 filas
        
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {CSV_FILE}.")
        print("Asegúrate de haberlo creado en la misma carpeta.")
        return
    except Exception as e:
        print(f"Error inesperado al leer el CSV: {e}")
        return

    # 2. Crear conexión a la base de datos SQLite
    # Esto crea el archivo 'mi_base.db' si no existe
    engine = create_engine(f'sqlite:///{DB_FILE}')
    print(f"\nConectando a la base de datos {DB_FILE}...")

    # 3. Guardar el DataFrame en la tabla SQL
    # 'if_exists='replace'' significa que si la tabla 'ventas' ya existe,
    # la borrará y la creará de nuevo. Perfecto para pruebas.
    try:
        df.to_sql(TABLE_NAME, engine, if_exists='replace', index=False)
        print(f"¡Éxito! Datos guardados en la tabla '{TABLE_NAME}'.")

        # 4. Verificación (Opcional pero recomendado)
        inspector = inspect(engine)
        if inspector.has_table(TABLE_NAME):
            print(f"Verificación: La tabla '{TABLE_NAME}' existe en la base de datos.")
        else:
            print(f"Verificación fallida: La tabla '{TABLE_NAME}' no se encontró.")
            
    except Exception as e:
        print(f"Error al guardar datos en la base de datos: {e}")

# Esto hace que el script se ejecute solo cuando lo llamas directamente
if __name__ == "__main__":
    cargar_datos()