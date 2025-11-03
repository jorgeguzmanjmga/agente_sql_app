import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase # <-- CORRECCIÓN 1
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent # <-- CORRECCIÓN 2

# --- CONFIGURACIÓN ---
DB_FILE = 'mi_base.db' # La base de datos que creamos en el paso anterior

def probar_agente():
    """
    Carga la API key, se conecta a la BD,
    crea un agente SQL y ejecuta una pregunta.
    """
    
    # 1. Cargar la API Key de OpenAI desde el archivo .env
    print("Cargando clave de API de OpenAI...")
    load_dotenv()
    
    # Verificación rápida de que la clave se cargó
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: No se encontró la variable OPENAI_API_KEY.")
        print("Asegúrate de que tu archivo .env está bien escrito.")
        return
    print("¡Clave de API cargada con éxito!")

    # 2. Conectarse a la base de datos (igual que antes)
    print(f"Conectando a la base de datos {DB_FILE}...")
    engine = create_engine(f'sqlite:///{DB_FILE}')
    
    # Envolver la conexión de la BD para que LangChain la entienda
    db = SQLDatabase(engine=engine)
    
    # (Opcional) Vamos a ver la estructura de la tabla que LangChain detecta
    print("\nEstructura de la base de datos detectada por LangChain:")
    print(db.get_table_info())

    # 3. Inicializar el "Cerebro" (Modelo de OpenAI)
    # Usamos gpt-3.5-turbo por ser rápido y barato para pruebas.
    # 'temperature=0' significa que queremos respuestas precisas, no creativas.
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    # 4. Crear el Agente SQL
    # Aquí es donde ocurre la magia. Le damos al agente:
    # - El cerebro (llm)
    # - La herramienta (db)
    # - Permiso para "pensar" (agent_type="openai-tools")
    # - 'verbose=True' para que nos muestre su razonamiento (¡crucial!)
    print("\nCreando agente SQL...")
    agente = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="openai-tools",
        verbose=True # ¡Esto es genial! Nos deja ver qué piensa el agente.
    )
    print("¡Agente creado!")

    # 5. ¡Hacer la pregunta!
    pregunta = "¿Cuál es el producto más vendido en la región Norte?"
    print(f"\n--- Ejecutando pregunta: '{pregunta}' ---")
    
    try:
        # Usamos .invoke() que es la forma moderna de LangChain de llamar
        respuesta = agente.invoke(pregunta)
        
        print("\n--- Respuesta Final del Agente ---")
        # La respuesta es un diccionario, el resultado está en la clave 'output'
        print(respuesta['output'])
        
    except Exception as e:
        print(f"\nHa ocurrido un error al ejecutar el agente: {e}")
        print("Revisa tu conexión a internet o el saldo de tu API de OpenAI.")

# Esto hace que el script se ejecute solo cuando lo llamas directamente
if __name__ == "__main__":
    probar_agente()