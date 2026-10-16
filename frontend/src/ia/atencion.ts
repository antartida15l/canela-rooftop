// Atención estimada solo con la orientación de la cabeza (no con la mirada ni con el rostro en sí).
// Es una señal aproximada: puede no reflejar la concentración real.

const GRADOS = 180 / Math.PI;

/** Zona muerta: pequeñas desviaciones (mirar el centro de la pantalla) no restan. */
export const ZONA_MUERTA_GRADOS = 12;
export const TOLERANCIA_YAW = 35;
export const TOLERANCIA_PITCH = 30;

/**
 * Ángulos de la cabeza a partir de la matriz 4x4 de transformación de MediaPipe
 * (facialTransformationMatrixes[0].data, 16 números). Se usa el vector "hacia delante" del rostro,
 * así que el resultado no depende del orden fila/columna ni del signo de los ejes.
 */
export function angulosCabeza(matriz: ArrayLike<number>): { yaw: number; pitch: number } {
  const fx = matriz[8];
  const fy = matriz[9];
  const fz = Math.abs(matriz[10]);
  return { yaw: Math.atan2(fx, fz) * GRADOS, pitch: Math.atan2(fy, fz) * GRADOS };
}

/** 1 = mirando de frente; 0 = girado hacia otro lado. */
export function puntuacionAtencion(yaw: number, pitch: number): number {
  const dy = Math.max(0, Math.abs(yaw) - ZONA_MUERTA_GRADOS) / TOLERANCIA_YAW;
  const dp = Math.max(0, Math.abs(pitch) - ZONA_MUERTA_GRADOS) / TOLERANCIA_PITCH;
  return Math.min(1, Math.max(0, 1 - Math.hypot(dy, dp)));
}
