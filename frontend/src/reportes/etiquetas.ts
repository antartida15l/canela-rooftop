export const nombreHabilidad = (id: string): string =>
  ({ matematica_suma: "Sumas", lectura_comprension: "Lectura" })[id] ?? id.replace(/_/g, " ");

export const textoTendencia = (t: string): string =>
  ({ mejora: "Mejorando", estable: "Estable", baja: "Bajando", insuficiente: "Pocos datos" })[t] ?? t;

export const fechaCorta = (iso: string): string =>
  new Date(iso).toLocaleDateString("es", { day: "2-digit", month: "short", year: "numeric" });

export const fechaHora = (iso: string): string =>
  new Date(iso).toLocaleString("es", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });

export const porcentaje = (x: number | null): string => (x === null ? "—" : `${Math.round(x * 100)} %`);

export const AVISO_REPORTE =
  "Este reporte es orientativo: lo genera un sistema automático a partir del desempeño en los ejercicios y, " +
  "si hubo permiso de cámara, de señales simples de atención. No es una evaluación ni un diagnóstico.";
