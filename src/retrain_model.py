import pandas as pd
import os

data_path = "data/processed/..."  # pon aquí la ruta real que usa tu script
print(f"Intentando leer: {data_path}")
print(f"¿Existe el archivo? {os.path.exists(data_path)}")
print(f"Archivos en data/: {os.listdir('data/') if os.path.exists('data') else 'No existe carpeta data'}")

df = pd.read_csv(data_path)
print(f"Columnas encontradas: {df.columns.tolist()}")
print(f"Shape del dataframe: {df.shape}")
