import { describe, expect, it } from "vitest";
import {
  aTensor,
  EMOCION_POR_INDICE,
  emocionDominante,
  softmax,
  SuavizadorEmocion,
  TAM_ENTRADA,
} from "../emociones";

// Imagen sintética idéntica a la de la referencia en Python (ref_preproc.py)
function imagen(): Uint8ClampedArray {
  const px = new Uint8ClampedArray(TAM_ENTRADA * TAM_ENTRADA * 4);
  for (let y = 0; y < TAM_ENTRADA; y++) {
    for (let x = 0; x < TAM_ENTRADA; x++) {
      const p = (y * TAM_ENTRADA + x) * 4;
      px[p] = (x * 3 + y) % 256;
      px[p + 1] = (x + y * 5) % 256;
      px[p + 2] = (x * y) % 256;
      px[p + 3] = 255;
    }
  }
  return px;
}

describe("aTensor (coincide con el preprocesado de referencia en Python)", () => {
  const t = aTensor(imagen());
  const n = TAM_ENTRADA * TAM_ENTRADA;
  const en = (c: number, y: number, x: number) => t[c * n + y * TAM_ENTRADA + x];

  it("tiene forma CHW", () => {
    expect(t).toBeInstanceOf(Float32Array);
    expect(t.length).toBe(3 * n);
  });

  it.each([
    [0, 0, 0, -2.117904],
    [1, 0, 0, -2.035714],
    [2, 0, 0, -1.804444],
    [0, 20, 10, -1.261666],
    [1, 20, 10, -0.109944],
    [2, 20, 10, 1.681394],
    [0, 223, 223, 0.005565],
    [1, 223, 223, -1.020308],
    [2, 223, 223, -0.671547],
    [2, 100, 150, 0.844793],
  ])("canal %i, fila %i, columna %i", (c, y, x, esperado) => {
    expect(en(c, y, x)).toBeCloseTo(esperado, 4);
  });

  it("la suma total coincide", () => {
    let s = 0;
    for (const v of t) s += v;
    expect(s).toBeCloseTo(33454.34375, -1);
  });
});

describe("clases y softmax", () => {
  it("el orden de clases es el de HSEmotion de 8 clases", () => {
    expect(EMOCION_POR_INDICE).toEqual([
      "enojo", "desprecio", "asco", "miedo", "feliz", "neutral", "triste", "sorpresa",
    ]);
  });

  it("softmax suma 1 y conserva el máximo", () => {
    const p = softmax([1, 2, 3, 4, 10, 0, -1, 2]);
    expect(p.reduce((s, v) => s + v, 0)).toBeCloseTo(1, 6);
    expect(emocionDominante(p).emocion).toBe("feliz");
  });

  it("softmax es estable con logits grandes", () => {
    const p = softmax([1000, 999, 0, 0, 0, 0, 0, 0]);
    expect(p.every(Number.isFinite)).toBe(true);
  });
});

describe("SuavizadorEmocion", () => {
  const feliz = [0, 0, 0, 0, 1, 0, 0, 0];
  const enojo = [1, 0, 0, 0, 0, 0, 0, 0];

  it("la primera lectura pasa tal cual", () => {
    expect(new SuavizadorEmocion().actualizar(feliz)).toEqual(feliz);
  });

  it("una lectura suelta distinta no cambia la etiqueta dominante", () => {
    const s = new SuavizadorEmocion(0.4);
    s.actualizar(feliz);
    s.actualizar(feliz);
    expect(emocionDominante(s.actualizar(enojo)).emocion).toBe("feliz");
  });

  it("lecturas sostenidas sí la cambian", () => {
    const s = new SuavizadorEmocion(0.4);
    s.actualizar(feliz);
    let ultima = feliz;
    for (let i = 0; i < 4; i++) ultima = s.actualizar(enojo);
    expect(emocionDominante(ultima).emocion).toBe("enojo");
  });
});
