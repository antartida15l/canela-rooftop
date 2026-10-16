// Prepara los archivos de IA que el navegador necesita:
//  1) binarios WASM de onnxruntime-web      -> public/ort/
//  2) binarios WASM de MediaPipe            -> public/mediapipe/wasm/
//  3) modelo de rostro (face_landmarker)    -> public/mediapipe/face_landmarker.task
//  4) comprueba que esté el modelo de emociones en public/models/
// Nunca falla la instalación: si algo no se puede hacer, avisa y sigue.
import { access, copyFile, mkdir, readdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const pub = path.join(raiz, "public");
const existe = (p) => access(p).then(() => true, () => false);

async function copiar(origen, destino, filtro = () => true) {
  if (!(await existe(origen))) {
    console.warn(`[preparar-ia] no se encontró ${origen} (¿falta npm install?)`);
    return 0;
  }
  await mkdir(destino, { recursive: true });
  let n = 0;
  for (const f of await readdir(origen)) {
    if (filtro(f)) {
      await copyFile(path.join(origen, f), path.join(destino, f));
      n++;
    }
  }
  return n;
}

const ort = await copiar(
  path.join(raiz, "node_modules/onnxruntime-web/dist"),
  path.join(pub, "ort"),
  (f) => /^ort-wasm-simd-threaded\.(wasm|mjs)$/.test(f),
);
const mp = await copiar(
  path.join(raiz, "node_modules/@mediapipe/tasks-vision/wasm"),
  path.join(pub, "mediapipe/wasm"),
);
console.log(`[preparar-ia] onnxruntime-web: ${ort} archivos · mediapipe wasm: ${mp} archivos`);

const URL_ROSTRO =
  "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task";
const tarea = path.join(pub, "mediapipe/face_landmarker.task");
if (!(await existe(tarea))) {
  try {
    const r = await fetch(URL_ROSTRO);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    await mkdir(path.dirname(tarea), { recursive: true });
    await writeFile(tarea, Buffer.from(await r.arrayBuffer()));
    console.log("[preparar-ia] descargado face_landmarker.task");
  } catch (e) {
    console.warn(`[preparar-ia] no se pudo descargar el modelo de rostro (${e.message}).`);
    console.warn(`  Descárgalo de ${URL_ROSTRO}\n  y guárdalo en public/mediapipe/face_landmarker.task`);
  }
}

if (!(await existe(path.join(pub, "models/enet_b0_8_best_vgaf.onnx")))) {
  console.warn("[preparar-ia] FALTA public/models/enet_b0_8_best_vgaf.onnx (modelo de emociones).");
}
