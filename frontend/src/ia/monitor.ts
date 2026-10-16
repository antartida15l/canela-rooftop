// Port a TypeScript de backend/app/modules/atencion/reglas.py.
// Los parámetros reales llegan del servidor en sesion.ajustes.atencion (se congelan al iniciar);
// estos valores solo se usan como respaldo y en las pruebas.

export interface ParamsAtencion {
  intervalo_s: number;
  calibracion_lecturas: number;
  alpha: number;
  confirmaciones: number;
  ausente_confirmaciones: number;
  min_entre_intervenciones_s: number;
  escalado_s: number;
  umbral_relativo: number;
  umbral_minimo: number;
}

export const PARAMS_POR_DEFECTO: ParamsAtencion = {
  intervalo_s: 3,
  calibracion_lecturas: 5,
  alpha: 0.4,
  confirmaciones: 2,
  ausente_confirmaciones: 3,
  min_entre_intervenciones_s: 60,
  escalado_s: 180,
  umbral_relativo: 0.6,
  umbral_minimo: 0.2,
};

export type Motivo = "malestar" | "atencion_baja" | "ausente";

export interface Intervencion {
  t: number;
  tipo: "aviso_suave" | "pausa";
  motivo: Motivo;
}

export const EMOCIONES_MALESTAR: ReadonlySet<string> = new Set(["enojo", "miedo", "triste", "asco"]);
const PRIORIDAD: Motivo[] = ["malestar", "atencion_baja", "ausente"];

/** Decide cuándo sugerir un aviso suave o una pausa. Nunca toma decisiones críticas. */
export class Monitor {
  private p: ParamsAtencion;
  private calibracion: number[] = [];
  private ema: number | null = null;
  private umbral: number | null = null;
  private cuentas: Record<Motivo, number> = { malestar: 0, atencion_baja: 0, ausente: 0 };
  private ultima: number | null = null;
  private ultimoAviso: number | null = null;

  constructor(params: Partial<ParamsAtencion> = {}) {
    this.p = { ...PARAMS_POR_DEFECTO, ...params };
  }

  get calibrado(): boolean {
    return this.umbral !== null;
  }

  procesar(t: number, atencion: number | null, emocion: string | null = null, rostro = true): Intervencion | null {
    const presente = rostro && atencion !== null;
    if (!presente) {
      this.cuentas.ausente += 1;
      this.cuentas.malestar = 0;
      this.cuentas.atencion_baja = 0;
    } else {
      this.cuentas.ausente = 0;
      const a = this.p.alpha;
      this.ema = this.ema === null ? atencion : a * atencion + (1 - a) * this.ema;
      if (this.umbral === null) {
        this.calibracion.push(atencion);
        if (this.calibracion.length >= this.p.calibracion_lecturas) {
          const base = this.calibracion.reduce((s, v) => s + v, 0) / this.calibracion.length;
          this.umbral = Math.max(this.p.umbral_minimo, base * this.p.umbral_relativo);
        }
        return null;
      }
      this.cuentas.atencion_baja = this.ema < this.umbral ? this.cuentas.atencion_baja + 1 : 0;
      this.cuentas.malestar = emocion !== null && EMOCIONES_MALESTAR.has(emocion) ? this.cuentas.malestar + 1 : 0;
    }

    if (this.umbral === null) return null;
    const motivo = this.motivoDisparado();
    if (motivo === null) return null;
    if (this.ultima !== null && t - this.ultima < this.p.min_entre_intervenciones_s) return null;

    const escalar = this.ultimoAviso !== null && t - this.ultimoAviso <= this.p.escalado_s;
    const tipo = escalar ? "pausa" : "aviso_suave";
    this.ultima = t;
    this.ultimoAviso = tipo === "pausa" ? null : t;
    this.cuentas = { malestar: 0, atencion_baja: 0, ausente: 0 };
    return { t, tipo, motivo };
  }

  private motivoDisparado(): Motivo | null {
    for (const m of PRIORIDAD) {
      const minimo = m === "ausente" ? this.p.ausente_confirmaciones : this.p.confirmaciones;
      if (this.cuentas[m] >= minimo) return m;
    }
    return null;
  }
}

export interface LecturaMonitor {
  t: number;
  atencion: number | null;
  emocion: string | null;
  rostro: boolean;
}

export function reproducir(lecturas: LecturaMonitor[], params: Partial<ParamsAtencion> = {}): Intervencion[] {
  const monitor = new Monitor(params);
  const salida: Intervencion[] = [];
  for (const l of lecturas) {
    const r = monitor.procesar(l.t, l.atencion, l.emocion, l.rostro);
    if (r) salida.push(r);
  }
  return salida;
}
