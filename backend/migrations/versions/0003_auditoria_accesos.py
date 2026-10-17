"""auditoría de accesos de especialistas"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE auditoria_accesos (
        id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        nino_id            UUID NOT NULL REFERENCES ninos(id) ON DELETE CASCADE,
        acceso_id          UUID,          -- referencia lógica: la fila de acceso puede desaparecer
        especialista_id    UUID REFERENCES usuarios(id) ON DELETE SET NULL,
        especialista_email CITEXT NOT NULL,  -- copia, para conservar el registro si se borra la cuenta
        actor_id           UUID REFERENCES usuarios(id) ON DELETE SET NULL,
        accion             TEXT NOT NULL CHECK (accion IN ('otorgado','revocado','consultado')),
        alcance            TEXT CHECK (alcance IN ('resumen','completo')),
        detalle            JSONB NOT NULL DEFAULT '{}'::jsonb,
        fecha              TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX ix_auditoria_nino_fecha ON auditoria_accesos(nino_id, fecha DESC);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS auditoria_accesos;")
