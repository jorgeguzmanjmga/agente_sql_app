import os
import uvicorn
import pandas as pd # <-- AÑADIDO
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect # <-- AÑADIDO 'inspect'
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent
from fastapi.middleware.cors import CORSMiddleware

# --- BLOQUE 1: LÓGICA PARA CREAR LA BASE DE DATOS ---
# Definimos las rutas de los archivos
DB_FILE = 'mi_base.db'
CSV_FILE = 'demo.csv'
TABLE_NAME = 'ventas'

def crear_base_si_no_existe():
    """
    Verifica si el archivo de la BD existe.
    Si no existe, la crea a partir del CSV.
    """
    print("Verificando existencia de la base de datos...")
    if not os.path.exists(DB_FILE):
        print(f"Base de datos no encontrada. Creando '{DB_FILE}' desde '{CSV_FILE}'...")
        
        try:
            # Leer el CSV
            df = pd.read_csv(CSV_FILE)
            
            # Crear conexión y guardar en SQL
            engine = create_engine(f'sqlite:///{DB_FILE}')
            df.to_sql(TABLE_NAME, engine, if_exists='replace', index=False)
            
            print(f"¡Base de datos y tabla '{TABLE_NAME}' creadas con éxito!")
            
        except FileNotFoundError:
            print(f"ERROR CRÍTICO: No se encontró '{CSV_FILE}'. El servidor no puede crear la BD.")
            # En un caso real, esto debería detener la app
        except Exception as e:
            print(f"ERROR CRÍTICO al crear la BD: {e}")
    else:
        print("La base de datos ya existe. Omitiendo creación.")

# --- FIN DEL BLOQUE 1 ---


# --- BLOQUE 2: CONFIGURACIÓN INICIAL DEL SERVIDOR ---

print("Iniciando el servidor de API...")

# 2.1. ¡EJECUTAMOS LA FUNCIÓN!
crear_base_si_no_existe() 

# 2.2. Cargar la API Key de OpenAI
print("Cargando clave de API...")
load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("No se encontró OPENAI_API_KEY. Asegúrate de que tu .env existe.")

# 2.3. Conectar a la base de datos (que ahora sabemos que existe)
print("Conectando a la base de datos...")
engine = create_engine(f'sqlite:///{DB_FILE}')
db = SQLDatabase(engine=engine)

# 2.4. Inicializar el "Cerebro" (LLM)
print("Inicializando el modelo de OpenAI (LLM)...")
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# 2.5. Crear el Agente SQL
print("Creando el agente SQL...")
agente = create_sql_agent(
    llm=llm,
    db=db,
    agent_type="openai-tools",
    verbose=True
)
print("¡Servidor listo para recibir peticiones!")

# --- 3. DEFINICIÓN DE LA API ---
app = FastAPI(
    title="Agente de Datos SQL",
    description="Una API que responde preguntas sobre una base de datos usando un agente de IA.",
    version="1.0.0"
)

# --- 4. CONFIGURACIÓN DE CORS ---
origins = ["*"] # Dejamos "*" por ahora para que Vercel pueda conectarse

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# --- 5. DEFINICIÓN DE LOS DATOS DE ENTRADA/SALIDA ---
class Pregunta(BaseModel):
    texto: str 

class Respuesta(BaseModel):
    respuesta: str 

# --- 6. CREACIÓN DEL ENDPOINT (/preguntar) ---
@app.post("/preguntar", response_model=Respuesta)
def preguntar(pregunta: Pregunta):
    print(f"\nRecibida pregunta: {pregunta.texto}")
    try:
        resultado = agente.invoke(pregunta.texto)
        print(f"Respuesta generada: {resultado['output']}")
        return Respuesta(respuesta=resultado['output'])
    except Exception as e:
        print(f"Error procesando la pregunta: {e}")
        raise HTTPException(status_code=500, detail=f"Error del agente: {e}")

# --- 7. PUNTO DE ENTRADA (Opcional, bueno para pruebas) ---
if __name__ == "__main__":
    print("Iniciando servidor Uvicorn en http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
