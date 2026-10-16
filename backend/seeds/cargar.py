import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import SessionLocal  # noqa: E402
from app.modules.contenido import service  # noqa: E402
from app.modules.contenido.schemas import EjercicioIn  # noqa: E402

with SessionLocal() as db:
    for archivo in sorted(Path(__file__).parent.glob("ejercicios_*.json")):
        for crudo in json.loads(archivo.read_text(encoding="utf-8")):
            e = EjercicioIn(**crudo)  # valida el formato
            if service.existe(db, e.codigo):
                print(f"= {e.codigo} (ya existe)")
                continue
            service.crear_borrador(db, e.codigo, e.habilidad, e.nivel, e.contenido.model_dump())
            print(f"+ {e.codigo} (borrador)")