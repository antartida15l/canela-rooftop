import type { Intervencion } from "../ia/monitor";
import type { ParamsAtencion } from "../ia/monitor";

export interface Usuario {
  id: string;
  email: string;
  rol: string;
}

/** Lo que ve la aplicación del niño. La condición declarada NUNCA viaja aquí. */
export interface Nino {
  id: string;
  nombre: string;
  edad: number;
  dominio: Record<string, unknown>;
  creado_en: string;
}

export interface AjustesSesion {
  sesion_min?: number;
  pausa_cada_min?: number;
  pausa_seg?: number;
  ejercicios_objetivo?: number;
  habilidad: string;
  camara: boolean;
  atencion?: Partial<ParamsAtencion>;
}

export interface Sesion {
  id: string;
  nino_id: string;
  inicio: string;
  fin: string | null;
  ajustes: AjustesSesion;
  kpi: Record<string, unknown>;
  nota: number | null;
}

export interface Ejercicio {
  id: string;
  nivel: number;
  tipo: string;
  enunciado: string;
  opciones: string[];
}

export interface Consentimiento {
  tipo: "terminos" | "camara" | "investigacion";
  version_vigente: string;
  aceptado: boolean;
  version_aceptada: string | null;
  fecha: string | null;
  requiere_reaceptacion: boolean;
}

export interface Observacion {
  nivel: "info" | "atencion";
  texto: string;
}

export interface RespuestaEnvio {
  ejercicio_id: string;
  elecciones: number[];
  ms: number;
}

export interface LecturaEnvio {
  t: number;
  rostro: boolean;
  atencion: number | null;
  emocion: string | null;
}

export interface PausaEnvio {
  inicio_s: number;
  duracion_s: number;
  motivo: "programada" | "solicitada" | "sugerida";
}

export interface CierreEnvio {
  respuestas: RespuestaEnvio[];
  detalle: { pausas: PausaEnvio[]; lecturas: LecturaEnvio[]; intervenciones: Intervencion[] };
}

export interface CierreResultado {
  nota: number | null;
  kpi: { respondidas?: number; correctas?: number } & Record<string, unknown>;
}

// ---------- Reportes y especialistas ----------
export interface Reporte {
  periodo_dias: number;
  generado_en: string;
  alcance: "resumen" | "completo";
  nino: { nombre: string; edad: number };
  resumen: {
    sesiones: number;
    minutos: number;
    nota_media: number | null;
    aciertos_pct: number | null;
    tendencia: "mejora" | "estable" | "baja" | "insuficiente";
  };
  habilidades: { habilidad: string; sesiones: number; nota_media: number | null; nivel: number; dominio: number }[];
  sesiones: { id: string; inicio: string; habilidad: string; nota: number | null; respondidas: number; correctas: number }[];
  atencion: {
    sesiones_con_camara: number;
    atencion_media: number | null;
    pct_malestar: number;
    avisos: number;
    pausas_sugeridas: number;
  } | null;
  recomendaciones: { nivel: "info" | "sugerencia"; texto: string }[] | null;
}

export interface Acceso {
  id: string;
  nino_id: string;
  especialista_email: string;
  alcance: "resumen" | "completo";
  creado_en: string;
  expira_en: string;
  revocado_en: string | null;
  estado: "vigente" | "expirado" | "revocado";
}

export interface EventoAuditoria {
  id: number;
  accion: "otorgado" | "revocado" | "consultado";
  alcance: "resumen" | "completo" | null;
  especialista_email: string;
  fecha: string;
}

export interface NinoCompartido {
  nino_id: string;
  nombre: string;
  edad: number;
  alcance: "resumen" | "completo";
  expira_en: string;
}
