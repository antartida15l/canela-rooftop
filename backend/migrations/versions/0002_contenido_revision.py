"""contenido: código, versión única y revisión pedagógica obligatoria"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    ALTER TABLE ejercicios
        ADD COLUMN codigo TEXT NOT NULL,
        ADD COLUMN revisado_por TEXT,
        ADD COLUMN revisado_en TIMESTAMPTZ,
        ADD CONSTRAINT uq_ejercicio_codigo_version UNIQUE (codigo, version),
        ADD CONSTRAINT ck_activo_requiere_revision
            CHECK (NOT activo OR (revisado_por IS NOT NULL AND revisado_en IS NOT NULL));
    """)


def downgrade() -> None:
    op.execute("""
    ALTER TABLE ejercicios
        DROP CONSTRAINT ck_activo_requiere_revision,
        DROP CONSTRAINT uq_ejercicio_codigo_version,
        DROP COLUMN revisado_en,
        DROP COLUMN revisado_por,
        DROP COLUMN codigo;
    """)