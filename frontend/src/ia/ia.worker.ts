// Corre el modelo de emociones fuera del hilo principal para que la interfaz no se trabe.
import * as ort from "onnxruntime-web/wasm";

export type MensajeEntrada =
  | { tipo: "cargar"; modelo: string; wasm: string }
  | { tipo: "inferir"; id: number; tensor: Float32Array };

export type MensajeSalida =
  | { tipo: "listo"; entrada: string; salida: string; ms: number }
  | { tipo: "resultado"; id: number; logits: Float32Array; ms: number }
  | { tipo: "error"; id?: number; mensaje: string };

interface Contexto {
  postMessage(m: MensajeSalida, transfer?: Transferable[]): void;
  onmessage: ((e: MessageEvent<MensajeEntrada>) => void) | null;
}
const ctx = self as unknown as Contexto;
let sesion: ort.InferenceSession | null = null;

ctx.onmessage = async (e) => {
  const m = e.data;
  try {
    if (m.tipo === "cargar") {
      const inicio = performance.now();
      ort.env.wasm.wasmPaths = m.wasm;
      ort.env.wasm.numThreads = 1; // evita requerir cabeceras COOP/COEP
      ort.env.wasm.proxy = false;
      sesion = await ort.InferenceSession.create(m.modelo, {
        executionProviders: ["wasm"],
        graphOptimizationLevel: "all",
      });
      ctx.postMessage({
        tipo: "listo",
        entrada: sesion.inputNames[0],
        salida: sesion.outputNames[0],
        ms: Math.round(performance.now() - inicio),
      });
    } else {
      if (!sesion) throw new Error("El modelo aún no está cargado");
      const inicio = performance.now();
      const tensor = new ort.Tensor("float32", m.tensor, [1, 3, 224, 224]);
      const salida = await sesion.run({ [sesion.inputNames[0]]: tensor });
      const logits = Float32Array.from(salida[sesion.outputNames[0]].data as Float32Array);
      ctx.postMessage(
        { tipo: "resultado", id: m.id, logits, ms: Math.round(performance.now() - inicio) },
        [logits.buffer],
      );
    }
  } catch (err) {
    ctx.postMessage({
      tipo: "error",
      id: m.tipo === "inferir" ? m.id : undefined,
      mensaje: err instanceof Error ? err.message : String(err),
    });
  }
};
