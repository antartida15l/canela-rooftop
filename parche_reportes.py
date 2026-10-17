"""Conecta el módulo de reportes y especialistas con tu backend.

Hace dos cosas en archivos que ya tienes:
  1) backend/app/main.py        -> registra los routers de reportes, accesos y especialista
  2) backend/tests/conftest.py  -> añade la fixture `especialista_de` que usan los tests nuevos

Uso (desde la carpeta raíz del proyecto, la que contiene backend/ y frontend/):
    python parche_reportes.py

Es seguro ejecutarlo más de una vez. Si algo no se puede aplicar, NO modifica ningún archivo.
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
MAIN = RAIZ / "backend" / "app" / "main.py"
CONFTEST = RAIZ / "backend" / "tests" / "conftest.py"


class Fallo(Exception):
    pass


IMPORTS = (
    "from app.modules.especialistas.router import router as accesos_router\n"
    "from app.modules.especialistas.router import router_especialista\n"
    "from app.modules.reportes.router import router as reportes_router\n"
)
INCLUDES = (
    "app.include_router(reportes_router)\n"
    "app.include_router(accesos_router)\n"
    "app.include_router(router_especialista)\n"
)

FIXTURE = '''

@pytest.fixture
def especialista_de(registrar, db):
    """Crea una cuenta y la convierte en especialista (en producción lo hace un administrador)."""
    def _crear(email="doc@test.pe"):
        h = registrar(email)
        db.execute(text("UPDATE usuarios SET rol = 'especialista' WHERE email = :e"), {"e": email})
        db.commit()
        return h
    return _crear
'''


def parche_main(t: str) -> str:
    if "accesos_router" in t:
        return t
    incluidos = list(re.finditer(r"^app\.include_router\(.*\)[ \t]*$", t, re.M))
    if not incluidos:
        raise Fallo("no encontré ninguna línea  app.include_router(...)")
    fin = incluidos[-1].end()
    return IMPORTS + t[:fin] + "\n" + INCLUDES.rstrip("\n") + t[fin:]


def parche_conftest(t: str) -> str:
    if "def especialista_de" in t:
        return t
    if "import pytest" not in t or "from sqlalchemy import text" not in t:
        raise Fallo("conftest.py no importa pytest o sqlalchemy.text como se esperaba")
    return t.rstrip("\n") + "\n" + FIXTURE


def main() -> int:
    for ruta in (MAIN, CONFTEST):
        if not ruta.is_file():
            print(f"✗ No encuentro {ruta}\n  Ejecuta este script desde la carpeta raíz del proyecto (la que contiene backend/).")
            return 1
    nuevos, informe = {}, []
    try:
        for ruta, funcion, desc in ((MAIN, parche_main, "routers de reportes y especialistas"),
                                    (CONFTEST, parche_conftest, "fixture especialista_de")):
            original = ruta.read_text(encoding="utf-8")
            try:
                nuevo = funcion(original)
            except Fallo as e:
                raise Fallo(f"{ruta.relative_to(RAIZ)}: {e}") from e
            try:
                compile(nuevo, str(ruta), "exec")
            except SyntaxError as e:
                raise Fallo(f"{ruta.relative_to(RAIZ)}: el resultado tendría un error de sintaxis (línea {e.lineno})") from e
            if nuevo != original:
                nuevos[ruta] = nuevo
                informe.append(f"  + {ruta.relative_to(RAIZ)}: {desc}")
            else:
                informe.append(f"  = {ruta.relative_to(RAIZ)}: ya estaba aplicado")
    except Fallo as e:
        print(f"\n✗ No se modificó ningún archivo.\n  Motivo: {e}")
        return 1
    for ruta, nuevo in nuevos.items():
        ruta.write_text(nuevo, encoding="utf-8")
    print("\n".join(informe))
    print("\n✓ Listo. Ahora:  cd backend && alembic upgrade head   (y la misma migración en la base de pruebas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
