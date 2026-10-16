const base = import.meta.env.BASE_URL;

export const API_URL = String(import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

/** Habilidades que el niño puede elegir. El id debe coincidir con el de los ejercicios del servidor. */
export const HABILIDADES = [
  { id: "matematica_suma", nombre: "Sumas", emoji: "➕" },
  { id: "lectura_comprension", nombre: "Lectura", emoji: "📖" },
] as const;

/** Archivos de IA que sirve el propio sitio (nada se descarga de terceros). */
export const RUTAS_IA = {
  modeloEmociones: `${base}models/enet_b0_8_best_vgaf.onnx`,
  wasmOnnx: `${base}ort/`,
  wasmMediapipe: `${base}mediapipe/wasm`,
  modeloRostro: `${base}mediapipe/face_landmarker.task`,
} as const;
