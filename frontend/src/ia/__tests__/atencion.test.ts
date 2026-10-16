import { describe, expect, it } from "vitest";
import { angulosCabeza, puntuacionAtencion } from "../atencion";

/** Matriz 4x4 (columna-mayor) de una rotación pura de yaw o pitch, en grados. */
function matriz(yawDeg: number, pitchDeg: number): number[] {
  const y = (yawDeg * Math.PI) / 180;
  const p = (pitchDeg * Math.PI) / 180;
  const [sy, cy, sp, cp] = [Math.sin(y), Math.cos(y), Math.sin(p), Math.cos(p)];
  // R = Ry(y) * Rx(p), filas:
  const R = [
    [cy, sy * sp, sy * cp],
    [0, cp, -sp],
    [-sy, cy * sp, cy * cp],
  ];
  const d = new Array(16).fill(0);
  for (let c = 0; c < 3; c++) for (let r = 0; r < 3; r++) d[c * 4 + r] = R[r][c];
  d[15] = 1;
  return d;
}

describe("angulosCabeza", () => {
  it("de frente", () => {
    const { yaw, pitch } = angulosCabeza(matriz(0, 0));
    expect(yaw).toBeCloseTo(0, 6);
    expect(pitch).toBeCloseTo(0, 6);
  });
  it("giro lateral", () => {
    expect(Math.abs(angulosCabeza(matriz(30, 0)).yaw)).toBeCloseTo(30, 4);
    expect(Math.abs(angulosCabeza(matriz(-30, 0)).yaw)).toBeCloseTo(30, 4);
  });
  it("inclinación vertical", () => {
    expect(Math.abs(angulosCabeza(matriz(0, 20)).pitch)).toBeCloseTo(20, 4);
  });
});

describe("puntuacionAtencion", () => {
  it("de frente vale 1", () => expect(puntuacionAtencion(0, 0)).toBe(1));
  it("mirar un poco hacia abajo (pantalla) casi no resta", () => {
    expect(puntuacionAtencion(0, -15)).toBeGreaterThan(0.85);
    expect(puntuacionAtencion(5, -10)).toBe(1);
  });
  it("es simétrica", () => {
    expect(puntuacionAtencion(30, 0)).toBeCloseTo(puntuacionAtencion(-30, 0), 10);
  });
  it("girar mucho la cabeza la baja a casi cero", () => {
    expect(puntuacionAtencion(30, 0)).toBeCloseTo(1 - 18 / 35, 4);
    expect(puntuacionAtencion(60, 0)).toBe(0);
  });
  it("siempre está entre 0 y 1", () => {
    for (const yaw of [-90, -45, 0, 45, 90]) for (const pitch of [-90, 0, 90]) {
      const s = puntuacionAtencion(yaw, pitch);
      expect(s).toBeGreaterThanOrEqual(0);
      expect(s).toBeLessThanOrEqual(1);
    }
  });
});
