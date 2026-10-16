import { RUTAS_IA } from "../config";
import { softmax } from "./emociones";
import type { MensajeEntrada, MensajeSalida } from "./ia.worker";

/** Envoltorio del worker que ejecuta el modelo de emociones. */
export class ClasificadorEmociones {
  private worker: Worker;
  private pendientes = new Map<number, { ok: (r: { probs: number[]; ms: number }) => void; fallo: (e: Error) => void }>();
  private siguiente = 1;
  private listoP: Promise<{ ms: number }>;

  constructor() {
    this.worker = new Worker(new URL("./ia.worker.ts", import.meta.url), { type: "module" });
    this.listoP = new Promise((ok, fallo) => {
      this.worker.onmessage = (e: MessageEvent<MensajeSalida>) => {
        const m = e.data;
        if (m.tipo === "listo") ok({ ms: m.ms });
        else if (m.tipo === "resultado") {
          this.pendientes.get(m.id)?.ok({ probs: softmax(m.logits), ms: m.ms });
          this.pendientes.delete(m.id);
        } else if (m.tipo === "error") {
          const err = new Error(m.mensaje);
          if (m.id !== undefined) {
            this.pendientes.get(m.id)?.fallo(err);
            this.pendientes.delete(m.id);
          } else fallo(err);
        }
      };
      this.worker.onerror = (e) => fallo(new Error(e.message || "Error en el worker de IA"));
    });
    const msg: MensajeEntrada = {
      tipo: "cargar",
      modelo: new URL(RUTAS_IA.modeloEmociones, location.href).href,
      wasm: new URL(RUTAS_IA.wasmOnnx, location.href).href,
    };
    this.worker.postMessage(msg);
  }

  listo(): Promise<{ ms: number }> {
    return this.listoP;
  }

  async clasificar(tensor: Float32Array): Promise<{ probs: number[]; ms: number }> {
    await this.listoP;
    const id = this.siguiente++;
    return new Promise((ok, fallo) => {
      this.pendientes.set(id, { ok, fallo });
      const msg: MensajeEntrada = { tipo: "inferir", id, tensor };
      this.worker.postMessage(msg, [tensor.buffer]);
    });
  }

  cerrar(): void {
    this.worker.terminate();
  }
}

let instancia: Promise<ClasificadorEmociones> | null = null;

/** Un único clasificador por pestaña; si falla la carga, la próxima vez se reintenta. */
export function cargarClasificador(): Promise<ClasificadorEmociones> {
  if (!instancia) {
    const c = new ClasificadorEmociones();
    instancia = c.listo().then(
      () => c,
      (e) => {
        instancia = null;
        c.cerrar();
        throw e;
      },
    );
  }
  return instancia;
}
