"""Aplica al backend los cambios que necesita el frontend:
  1) CORS (para que el navegador pueda llamar a la API)
  2) endpoint POST /sesiones/{id}/ejercicios/{id}/verificar (retroalimentación inmediata al niño)

Uso (desde la carpeta raíz del proyecto, la que contiene backend/ y frontend/):
    python parche_backend.py

Es seguro ejecutarlo más de una vez: lo que ya está aplicado se salta.
Si algo no se puede aplicar, NO modifica ningún archivo y te dice qué hacer a mano.
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
APP = RAIZ / "backend" / "app"


class Fallo(Exception):
    pass


MIDDLEWARE = '''app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Zona-Padres"],
)'''

SCHEMAS = '''

class VerificarIn(BaseModel):
    eleccion: int = Field(ge=0, le=5)


class VerificarOut(BaseModel):
    correcta: bool
'''

SERVICE = '''

def verificar(db: Session, padre_id: str, sesion_id: str, ejercicio_id: str, eleccion: int) -> bool:
    """Solo dice si acertó. No guarda nada: la nota se calcula al cerrar la sesión."""
    sesion = obtener(db, padre_id, sesion_id)
    if sesion is None:
        raise NoEncontrada()
    if sesion["fin"] is not None:
        raise SesionCerrada()
    fila = db.execute(
        text("SELECT habilidad, contenido FROM ejercicios WHERE id = CAST(:e AS uuid) AND activo"),
        {"e": ejercicio_id},
    ).mappings().first()
    if fila is None or fila["habilidad"] != sesion["ajustes"]["habilidad"]:
        raise RespuestasInvalidas("Ejercicio inexistente o de otra habilidad")
    if eleccion >= len(fila["contenido"]["opciones"]):
        raise RespuestasInvalidas("Opción fuera de rango para el ejercicio")
    return eleccion == fila["contenido"]["correcta"]
'''

ROUTER = '''

@router.post("/{sesion_id}/ejercicios/{ejercicio_id}/verificar", response_model=VerificarOut)
def verificar(sesion_id: UUID, ejercicio_id: UUID, datos: VerificarIn,
              u: dict = Depends(solo_padres), db: Session = Depends(get_db)):
    try:
        return {"correcta": service.verificar(db, u["id"], str(sesion_id), str(ejercicio_id),
                                              datos.eleccion)}
    except service.NoEncontrada:
        raise _404
    except service.SesionCerrada:
        raise HTTPException(status.HTTP_409_CONFLICT, "La sesión ya fue cerrada")
    except service.RespuestasInvalidas as e:
        raise HTTPException(422, str(e))
'''


def parche_config(t: str) -> str:
    if "cors_origins" in t:
        return t
    m = (re.search(r"^([ \t]*)zona_padres_minutes[ \t]*:[^\n]*$", t, re.M)
         or re.search(r"^([ \t]*)cookie_secure[ \t]*:[^\n]*$", t, re.M))
    if not m:
        raise Fallo("no encontré dónde añadir el campo dentro de la clase Settings")
    return t[: m.end()] + f'\n{m.group(1)}cors_origins: list[str] = ["http://localhost:5173"]' + t[m.end():]


def parche_main(t: str) -> str:
    if "CORSMiddleware" in t:
        return t
    m = re.search(r"^app[ \t]*=[ \t]*FastAPI\(.*\)[ \t]*$", t, re.M)
    if not m:
        raise Fallo("no encontré la línea  app = FastAPI(...)")
    importes = "from fastapi.middleware.cors import CORSMiddleware\n"
    if "get_settings" not in t:
        importes += "from app.config import get_settings\n"
    return importes + t[: m.end()] + "\n" + MIDDLEWARE + t[m.end():]


def parche_schemas(t: str) -> str:
    return t if "class VerificarIn" in t else t.rstrip("\n") + "\n" + SCHEMAS


def parche_service(t: str) -> str:
    return t if "def verificar(" in t else t.rstrip("\n") + "\n" + SERVICE


def parche_router(t: str) -> str:
    if "def verificar(" in t:
        return t
    m = re.search(r"^router[ \t]*=[ \t]*APIRouter\(", t, re.M)
    if not m:
        raise Fallo("no encontré la línea  router = APIRouter(...)")
    t = (t[: m.start()] + "from app.modules.sesiones.schemas import VerificarIn, VerificarOut\n\n"
         + t[m.start():])
    return t.rstrip("\n") + "\n" + ROUTER


PARCHES = [
    (APP / "config.py", parche_config, "CORS: lista de orígenes permitidos"),
    (APP / "main.py", parche_main, "CORS: middleware"),
    (APP / "modules" / "sesiones" / "schemas.py", parche_schemas, "esquemas VerificarIn / VerificarOut"),
    (APP / "modules" / "sesiones" / "service.py", parche_service, "función verificar()"),
    (APP / "modules" / "sesiones" / "router.py", parche_router, "endpoint POST .../verificar"),
]


def main() -> int:
    if not APP.is_dir():
        print(f"✗ No encuentro {APP}\n  Ejecuta este script desde la carpeta raíz del proyecto (la que contiene backend/).")
        return 1

    nuevos: dict[Path, str] = {}
    informe: list[str] = []
    try:
        for ruta, funcion, descripcion in PARCHES:
            if not ruta.is_file():
                raise Fallo(f"no existe {ruta.relative_to(RAIZ)}")
            original = ruta.read_text(encoding="utf-8")
            try:
                nuevo = funcion(original)
            except Fallo as e:
                raise Fallo(f"{ruta.relative_to(RAIZ)}: {e}") from e
            try:
                compile(nuevo, str(ruta), "exec")
            except SyntaxError as e:
                raise Fallo(f"{ruta.relative_to(RAIZ)}: el resultado tendría un error de sintaxis (línea {e.lineno}). "
                            f"Puede que ese archivo tenga un error previo.") from e
            if nuevo != original:
                nuevos[ruta] = nuevo
                informe.append(f"  + {ruta.relative_to(RAIZ)}: {descripcion}")
            else:
                informe.append(f"  = {ruta.relative_to(RAIZ)}: ya estaba aplicado")
    except Fallo as e:
        print(f"\n✗ No se modificó ningún archivo.\n  Motivo: {e}")
        print("  Aplica los cambios a mano o pásame el mensaje de arriba.")
        return 1

    for ruta, nuevo in nuevos.items():
        ruta.write_text(nuevo, encoding="utf-8")
    print("\n".join(informe))
    print(f"\n✓ Listo ({len(nuevos)} archivo(s) modificado(s)). Ahora ejecuta:  cd backend && pytest -q")
    return 0


if __name__ == "__main__":
    sys.exit(main())
