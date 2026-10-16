import { FaceLandmarker, FilesetResolver } from "@mediapipe/tasks-vision";
import { RUTAS_IA } from "../config";
import { aTensor, TAM_ENTRADA } from "./emociones";

let landmarkerP: Promise<FaceLandmarker> | null = null;

/** Detector de rostro + pose de la cabeza (MediaPipe). Intenta GPU y cae a CPU si no está disponible. */
export function cargarLandmarker(): Promise<FaceLandmarker> {
  if (!landmarkerP) {
    landmarkerP = crear().catch((e) => {
      landmarkerP = null;
      throw e;
    });
  }
  return landmarkerP;
}

async function crear(): Promise<FaceLandmarker> {
  const fileset = await FilesetResolver.forVisionTasks(RUTAS_IA.wasmMediapipe);
  const opciones = (delegate: "GPU" | "CPU") => ({
    baseOptions: { modelAssetPath: RUTAS_IA.modeloRostro, delegate },
    runningMode: "VIDEO" as const,
    numFaces: 1,
    outputFacialTransformationMatrixes: true,
  });
  try {
    return await FaceLandmarker.createFromOptions(fileset, opciones("GPU"));
  } catch {
    return await FaceLandmarker.createFromOptions(fileset, opciones("CPU"));
  }
}

export type Deteccion =
  | { rostro: false }
  | { rostro: true; caja: { x: number; y: number; lado: number }; matriz: number[] };

let ultimaMarca = 0;

export function detectar(lm: FaceLandmarker, video: HTMLVideoElement): Deteccion {
  const ancho = video.videoWidth;
  const alto = video.videoHeight;
  if (!ancho || !alto) return { rostro: false };

  // MediaPipe exige marcas de tiempo estrictamente crecientes
  const ahora = Math.max(performance.now(), ultimaMarca + 1);
  ultimaMarca = ahora;
  const r = lm.detectForVideo(video, ahora);

  const puntos = r.faceLandmarks?.[0];
  const matriz = r.facialTransformationMatrixes?.[0]?.data;
  if (!puntos || puntos.length === 0 || !matriz) return { rostro: false };

  let minX = 1, minY = 1, maxX = 0, maxY = 0;
  for (const p of puntos) {
    if (p.x < minX) minX = p.x;
    if (p.x > maxX) maxX = p.x;
    if (p.y < minY) minY = p.y;
    if (p.y > maxY) maxY = p.y;
  }
  const lado = Math.max((maxX - minX) * ancho, (maxY - minY) * alto) * 1.15; // pequeño margen alrededor
  const cx = ((minX + maxX) / 2) * ancho;
  const cy = ((minY + maxY) / 2) * alto;
  return { rostro: true, caja: { x: cx - lado / 2, y: cy - lado / 2, lado }, matriz: Array.from(matriz) };
}

let lienzo: HTMLCanvasElement | null = null;

/** Recorta el rostro del vídeo a 224x224 y lo convierte al tensor del modelo. La imagen nunca sale de aquí. */
export function recortarATensor(video: HTMLVideoElement, caja: { x: number; y: number; lado: number }): Float32Array {
  lienzo ??= Object.assign(document.createElement("canvas"), { width: TAM_ENTRADA, height: TAM_ENTRADA });
  const ctx = lienzo.getContext("2d", { willReadFrequently: true });
  if (!ctx) throw new Error("No se pudo crear el lienzo de recorte");
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, TAM_ENTRADA, TAM_ENTRADA);

  // Recorta la zona fuera del cuadro de vídeo sin deformar el resto
  const escala = TAM_ENTRADA / caja.lado;
  const sx = Math.max(0, caja.x);
  const sy = Math.max(0, caja.y);
  const sx2 = Math.min(video.videoWidth, caja.x + caja.lado);
  const sy2 = Math.min(video.videoHeight, caja.y + caja.lado);
  if (sx2 > sx && sy2 > sy) {
    ctx.drawImage(video, sx, sy, sx2 - sx, sy2 - sy, (sx - caja.x) * escala, (sy - caja.y) * escala, (sx2 - sx) * escala, (sy2 - sy) * escala);
  }
  const datos = ctx.getImageData(0, 0, TAM_ENTRADA, TAM_ENTRADA).data;
  return aTensor(datos);
}
