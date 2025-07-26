from sqlalchemy import create_engine, text

# Crear el engine de conexión
engine = create_engine("postgresql+psycopg2://postgres:admin123@localhost:5432/dvdrental")

# Ejecutar consulta
with engine.connect() as conn:
    result = conn.execute(text("SELECT title FROM film LIMIT 5;"))
    print("🎬 Películas encontradas:")
    for row in result:
        print(f"- {row.title}")
