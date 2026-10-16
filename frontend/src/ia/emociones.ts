// Preprocesado y postprocesado del modelo enet_b0_8_best_vgaf (HSEmotion, EfficientNet-B0).
// Entrada: [1,3,224,224] float32, RGB normalizado con media/desviación de ImageNet.
// Salida: [1,8] logits en este orden (el de la librería HSEmotion para los modelos de 8 clases).

export const TAM_ENTRADA = 224;

export type Emocion = "enojo" | "desprecio" | "asco" | "miedo" | "feliz" | "neutral" | "triste" | "sorpresa";

/** Anger, Contempt, Disgust, Fear, Happiness, Neutral, Sadness, Surprise */
export const EMOCION_POR_INDICE: readonly Emocion[] = [
  "enojo",
  "desprecio",
  "asco",
  "miedo",
  "feliz",
  "neutral",
  "triste",
  "sorpresa",
];

const MEDIA = [0.485, 0.456, 0.406] as const;
const DESV = [0.229, 0.224, 0.225] as const;

/** RGBA (alto*ancho*4) -> tensor CHW normalizado. */
export function aTensor(rgba: ArrayLike<number>, ancho = TAM_ENTRADA, alto = TAM_ENTRADA): Float32Array {
  const n = ancho * alto;
  const out = new Float32Array(3 * n);
  for (let i = 0; i < n; i++) {
    const p = i * 4;
    out[i] = (rgba[p] / 255 - MEDIA[0]) / DESV[0];
    out[n + i] = (rgba[p + 1] / 255 - MEDIA[1]) / DESV[1];
    out[2 * n + i] = (rgba[p + 2] / 255 - MEDIA[2]) / DESV[2];
  }
  return out;
}

export function softmax(z: ArrayLike<number>): number[] {
  let max = -Infinity;
  for (let i = 0; i < z.length; i++) max = Math.max(max, z[i]);
  const e = Array.from({ length: z.length }, (_, i) => Math.exp(z[i] - max));
  const suma = e.reduce((s, v) => s + v, 0);
  return e.map((v) => v / suma);
}

export function emocionDominante(probs: readonly number[]): { emocion: Emocion; confianza: number } {
  let mejor = 0;
  for (let i = 1; i < probs.length; i++) if (probs[i] > probs[mejor]) mejor = i;
  return { emocion: EMOCION_POR_INDICE[mejor], confianza: probs[mejor] };
}

/** Suavizado exponencial de las probabilidades, para que la etiqueta no parpadee entre lecturas. */
export class SuavizadorEmocion {
  private actual: number[] | null = null;
  constructor(private alpha = 0.4) {}

  actualizar(probs: readonly number[]): number[] {
    if (this.actual === null) {
      this.actual = [...probs];
    } else {
      const previo = this.actual;
      this.actual = probs.map((p, i) => this.alpha * p + (1 - this.alpha) * previo[i]);
    }
    return [...this.actual];
  }

  reiniciar(): void {
    this.actual = null;
  }
}
