import { describe, expect, it } from "vitest";
import { Monitor, PARAMS_POR_DEFECTO, reproducir, type LecturaMonitor } from "../monitor";

function L(t: number, atencion = 0.8, emocion = "neutral", rostro = true): LecturaMonitor {
  return rostro ? { t, rostro: true, atencion, emocion } : { t, rostro: false, atencion: null, emocion: null };
}
function serie(inicio: number, n: number, atencion = 0.8, emocion = "neutral"): LecturaMonitor[] {
  return Array.from({ length: n }, (_, i) => L(inicio + 3 * i, atencion, emocion));
}
const CALIB = serie(0, 5); // 5 lecturas buenas: t = 0..12
const resumen = (r: ReturnType<typeof reproducir>) => r.map((i) => [i.t, i.tipo, i.motivo]);

describe("Monitor (mismas reglas que backend/atencion/reglas.py)", () => {
  it("parámetros acordados", () => {
    expect(PARAMS_POR_DEFECTO.intervalo_s).toBe(3);
    expect(PARAMS_POR_DEFECTO.calibracion_lecturas).toBe(5);
    expect(PARAMS_POR_DEFECTO.confirmaciones).toBe(2);
    expect(PARAMS_POR_DEFECTO.min_entre_intervenciones_s).toBe(60);
  });

  it("no interviene durante la calibración", () => {
    expect(reproducir(serie(0, 5, 0.1, "enojo"))).toEqual([]);
  });

  it("atención baja: dispara tras dos lecturas seguidas suavizadas", () => {
    // EMA tras calibrar = 0.8; umbral = 0.48. Con 0.1: 0.52, 0.352, 0.2512
    expect(resumen(reproducir([...CALIB, ...serie(15, 4, 0.1)]))).toEqual([[21, "aviso_suave", "atencion_baja"]]);
  });

  it("una lectura aislada no dispara nada", () => {
    expect(reproducir([...CALIB, L(15, 0.1), ...serie(18, 10)])).toEqual([]);
    expect(reproducir([...CALIB, L(15, 0.8, "enojo"), ...serie(18, 10)])).toEqual([]);
  });

  it("malestar: dispara tras dos lecturas seguidas", () => {
    expect(resumen(reproducir([...CALIB, ...serie(15, 2, 0.8, "enojo")]))).toEqual([[18, "aviso_suave", "malestar"]]);
  });

  it("malestar tiene prioridad sobre atención baja", () => {
    const r = reproducir([...CALIB, ...serie(15, 6, 0.05, "miedo")]);
    expect(r[0].motivo).toBe("malestar");
  });

  it("escalado: aviso, luego pausa, con 60 s de separación", () => {
    const r = reproducir([...CALIB, ...serie(15, 36, 0.8, "enojo")]); // hasta t = 120
    expect(resumen(r)).toEqual([
      [18, "aviso_suave", "malestar"],
      [78, "pausa", "malestar"],
    ]);
  });

  it("el patrón se repite y nunca hay menos de 60 s entre intervenciones", () => {
    const r = reproducir([...CALIB, ...serie(15, 200, 0.8, "enojo")]);
    expect(r.slice(0, 4).map((i) => i.tipo)).toEqual(["aviso_suave", "pausa", "aviso_suave", "pausa"]);
    const gaps = r.slice(1).map((b, i) => b.t - r[i].t);
    expect(gaps.length).toBeGreaterThan(0);
    expect(gaps.every((g) => g >= 60)).toBe(true);
  });

  it("si pasa mucho tiempo, el escalado se reinicia", () => {
    const r = reproducir([
      ...CALIB,
      ...serie(15, 2, 0.8, "enojo"), // aviso en t = 18
      ...serie(21, 93), // calma hasta t = 297
      L(300, 0.8, "enojo"),
      L(303, 0.8, "enojo"),
    ]);
    expect(resumen(r)).toEqual([
      [18, "aviso_suave", "malestar"],
      [303, "aviso_suave", "malestar"],
    ]);
  });

  it("ausencia de rostro: necesita tres lecturas y no cuenta como desatención", () => {
    expect(reproducir([...CALIB, L(15, 0, "", false), L(18, 0, "", false), ...serie(21, 5)])).toEqual([]);
    const tres = [...CALIB, L(15, 0, "", false), L(18, 0, "", false), L(21, 0, "", false)];
    expect(resumen(reproducir(tres))).toEqual([[21, "aviso_suave", "ausente"]]);
  });

  it("parámetros configurables", () => {
    expect(reproducir([...CALIB, ...serie(15, 2, 0.8, "enojo")], { confirmaciones: 3 })).toEqual([]);
    expect(reproducir([...CALIB, ...serie(15, 3, 0.8, "enojo")], { confirmaciones: 3 })).toHaveLength(1);
  });

  it("el umbral se adapta a la atención base del niño", () => {
    expect(reproducir([...serie(0, 5, 0.3), ...serie(15, 10, 0.25)])).toEqual([]);
  });

  it("expone el estado de calibración", () => {
    const m = new Monitor();
    expect(m.calibrado).toBe(false);
    for (const l of CALIB) m.procesar(l.t, l.atencion, l.emocion);
    expect(m.calibrado).toBe(true);
  });
});
