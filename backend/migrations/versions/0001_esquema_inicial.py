"""esquema inicial: 8 tablas"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE usuarios (
        id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email              CITEXT NOT NULL UNIQUE,
        pass_hash          TEXT NOT NULL,
        pin_hash           TEXT,
        pin_intentos       SMALLINT NOT NULL DEFAULT 0,
        pin_bloqueado_hasta TIMESTAMPTZ,
        rol                TEXT NOT NULL CHECK (rol IN ('padre','especialista','admin')),
        token_version      INTEGER NOT NULL DEFAULT 0,
        creado_en          TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE TABLE consentimientos (
        id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        usuario_id  UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        tipo        TEXT NOT NULL CHECK (tipo IN ('terminos','camara','investigacion')),
        version     TEXT NOT NULL,
        aceptado    BOOLEAN NOT NULL,
        fecha       TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    -- Cada cambio es una fila nueva. El vigente es la última por (usuario, tipo).
    CREATE INDEX ix_consent_usuario_tipo ON consentimientos(usuario_id, tipo, fecha DESC);

    CREATE TABLE perfiles_apoyo (
        codigo  TEXT PRIMARY KEY,
        nombre  TEXT NOT NULL,
        ajustes JSONB NOT NULL
    );

    CREATE TABLE ninos (
        id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        padre_id          UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        nombre            TEXT NOT NULL,
        edad              SMALLINT NOT NULL CHECK (edad BETWEEN 3 AND 18),
        condicion_cifrada BYTEA,
        perfil            TEXT NOT NULL REFERENCES perfiles_apoyo(codigo),
        dominio           JSONB NOT NULL DEFAULT '{}'::jsonb,
        creado_en         TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX ix_ninos_padre ON ninos(padre_id);

    CREATE TABLE ejercicios (
        id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        habilidad TEXT NOT NULL,
        nivel     SMALLINT NOT NULL CHECK (nivel BETWEEN 1 AND 3),
        contenido JSONB NOT NULL,
        version   INTEGER NOT NULL DEFAULT 1,
        activo    BOOLEAN NOT NULL DEFAULT FALSE  -- solo true tras revisión pedagógica
    );
    CREATE INDEX ix_ejercicios_busqueda ON ejercicios(habilidad, nivel) WHERE activo;

    CREATE TABLE sesiones (
        id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        nino_id   UUID NOT NULL REFERENCES ninos(id) ON DELETE CASCADE,
        inicio    TIMESTAMPTZ NOT NULL DEFAULT now(),
        fin       TIMESTAMPTZ,
        ajustes   JSONB NOT NULL,                      -- congelados al iniciar
        kpi       JSONB NOT NULL DEFAULT '{}'::jsonb,  -- se conserva siempre
        detalle   JSONB NOT NULL DEFAULT '{}'::jsonb,  -- se purga a los 12 meses
        nota      NUMERIC(4,2) CHECK (nota BETWEEN 0 AND 20)
    );
    CREATE INDEX ix_sesiones_nino_inicio ON sesiones(nino_id, inicio DESC);

    CREATE TABLE respuestas (
        id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        sesion_id   UUID NOT NULL REFERENCES sesiones(id) ON DELETE CASCADE,
        ejercicio_id UUID NOT NULL REFERENCES ejercicios(id),
        correcta    BOOLEAN NOT NULL,
        intentos    SMALLINT NOT NULL DEFAULT 1,
        ms          INTEGER NOT NULL,
        creado      TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX ix_respuestas_sesion ON respuestas(sesion_id);

    CREATE TABLE accesos_especialista (
        id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        nino_id         UUID NOT NULL REFERENCES ninos(id) ON DELETE CASCADE,
        especialista_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        alcance         TEXT NOT NULL CHECK (alcance IN ('resumen','completo')),
        creado_en       TIMESTAMPTZ NOT NULL DEFAULT now(),
        expira_en       TIMESTAMPTZ NOT NULL,
        revocado_en     TIMESTAMPTZ,
        CONSTRAINT ck_acceso_max_90_dias CHECK (expira_en <= creado_en + INTERVAL '90 days')
    );
    CREATE INDEX ix_acceso_nino ON accesos_especialista(nino_id);
    CREATE INDEX ix_acceso_especialista ON accesos_especialista(especialista_id);

    -- Catálogo inicial. Los ajustes son PLACEHOLDERS: los valores reales
    -- los define y revisa un psicopedagogo.
    INSERT INTO perfiles_apoyo (codigo, nombre, ajustes) VALUES
      ('general',     'Base general',      jsonb_build_object('sesion_min',15,'pausa_cada_min',10,'pausa_seg',30)),
      ('tdah',        'Apoyo TDAH',        jsonb_build_object('sesion_min',10,'pausa_cada_min',5, 'pausa_seg',30)),
      ('tea',         'Apoyo TEA',         jsonb_build_object('sesion_min',15,'pausa_cada_min',10,'pausa_seg',30)),
      ('dislexia',    'Apoyo dislexia',    jsonb_build_object('sesion_min',15,'pausa_cada_min',8, 'pausa_seg',30)),
      ('discalculia', 'Apoyo discalculia', jsonb_build_object('sesion_min',15,'pausa_cada_min',8, 'pausa_seg',30));
    """)


def downgrade() -> None:
    op.execute("""
    DROP TABLE IF EXISTS accesos_especialista, respuestas, sesiones, ejercicios,
                         ninos, perfiles_apoyo, consentimientos, usuarios CASCADE;
    """)