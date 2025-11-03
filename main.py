import os
import uvicorn # El servidor que corre nuestra app
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel # Para definir la estructura de la pregunta
from dotenv import load_dotenv
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent

# Importamos el Middleware de CORS
from fastapi.middleware.cors import CORSMiddleware

# --- 1. CONFIGURACIÓN INICIAL (Se ejecuta 1 vez al iniciar) ---

print("Iniciando el servidor de API...")

# Cargar la API Key de OpenAI desde el archivo .env
print("Cargando clave de API...")
load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("No se encontró OPENAI_API_KEY. Asegúrate de que tu .env existe.")

# Conectar a la base de datos
print("Conectando a la base de datos...")
engine = create_engine(f'sqlite:///mi_base.db')
db = SQLDatabase(engine=engine)

# Inicializar el "Cerebro" (LLM)
print("Inicializando el modelo de OpenAI (LLM)...")
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Crear el Agente SQL
print("Creando el agente SQL...")
agente = create_sql_agent(
    llm=llm,
    db=db,
    agent_type="openai-tools",
    verbose=True # Veremos el "pensamiento" en la terminal del servidor
)
print("¡Servidor listo para recibir peticiones!")

# --- 2. DEFINICIÓN DE LA API ---

# Inicializar la aplicación FastAPI
app = FastAPI(
    title="Agente de Datos SQL",
    description="Una API que responde preguntas sobre una base de datos usando un agente de IA.",
    version="1.0.0"
)

# --- 3. CONFIGURACIÓN DE CORS ---
# Esto es VITAL para que tu Front-End (que vivirá en otro dominio)
# pueda hablar con este Back-End.
# Por ahora, permitimos todos los orígenes ("*") por simplicidad.
origins = ["*"] # En producción, aquí pondrías la URL de tu app (ej. "https://mi-app.vercel.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permitir todos los métodos (GET, POST, etc.)
    allow_headers=["*"], # Permitir todos los encabezados
)

# --- 4. DEFINICIÓN DE LOS DATOS DE ENTRADA/SALIDA ---

# Usamos Pydantic para decirle a FastAPI cómo debe lucir una "Pregunta"
class Pregunta(BaseModel):
    texto: str # Esperamos un JSON como: {"texto": "¿cuál fue la pregunta?"}

# Y cómo debe lucir una "Respuesta"
class Respuesta(BaseModel):
    respuesta: str # Devolveremos un JSON como: {"respuesta": "La respuesta es..."}

# --- 5. CREACIÓN DEL ENDPOINT (/preguntar) ---

@app.post("/preguntar", response_model=Respuesta)
def preguntar(pregunta: Pregunta):
    """
    Recibe una pregunta en lenguaje natural, la procesa con el agente SQL
    y devuelve la respuesta.
    """
    print(f"\nRecibida pregunta: {pregunta.texto}")
    
    try:
        # Aquí es donde llamamos al agente que creamos al inicio
        resultado = agente.invoke(pregunta.texto)
        
        print(f"Respuesta generada: {resultado['output']}")
        
        # Devolvemos la respuesta en el formato que definimos
        return Respuesta(respuesta=resultado['output'])
        
    except Exception as e:
        print(f"Error procesando la pregunta: {e}")
        # Devolver un error HTTP (FastAPI lo maneja)
        raise HTTPException(status_code=500, detail=f"Error del agente: {e}")

# --- 6. PUNTO DE ENTRADA PARA CORRER EL SERVIDOR (Opcional) ---
# Esto nos permite correrlo con "python main.py", aunque
# es más común usar "uvicorn main:app --reload" en la terminal.
if __name__ == "__main__":
    print("Iniciando servidor Uvicorn en http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)