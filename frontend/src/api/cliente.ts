import { API_URL } from "../config";

export class ApiError extends Error {
  constructor(
    public status: number,
    public detalle: unknown,
  ) {
    super(mensajeDe(detalle, status));
  }
  get codigo(): string | undefined {
    const d = this.detalle as { codigo?: string } | null;
    return d && typeof d === "object" ? d.codigo : undefined;
  }
}

function mensajeDe(detalle: unknown, status: number): string {
  if (typeof detalle === "string") return detalle;
  if (Array.isArray(detalle)) {
    return detalle.map((d) => (d && typeof d === "object" && "msg" in d ? String((d as { msg: unknown }).msg) : "dato no válido")).join(". ");
  }
  if (detalle && typeof detalle === "object" && "codigo" in detalle) return String((detalle as { codigo: unknown }).codigo);
  return `Error ${status}`;
}

// El token de acceso y el de la zona de padres viven SOLO en memoria (no en localStorage).
let accessToken: string | null = null;
let zona: { token: string; expira: number } | null = null;
const oyentes = new Set<() => void>();

export const haySesion = () => accessToken !== null;
export function alPerderSesion(fn: () => void): () => void {
  oyentes.add(fn);
  return () => oyentes.delete(fn);
}
export function fijarToken(t: string | null): void {
  accessToken = t;
  if (t === null) zona = null;
}

export const hayZona = () => zona !== null && Date.now() < zona.expira;
export const zonaExpiraEn = () => (zona ? Math.max(0, zona.expira - Date.now()) : 0);
export function guardarZona(token: string, minutos: number): void {
  zona = { token, expira: Date.now() + minutos * 60_000 };
}
export function salirDeZona(): void {
  zona = null;
}

interface Opciones {
  metodo?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  cuerpo?: unknown;
  /** Exige el token de la zona de padres (se obtiene al verificar el PIN). */
  zona?: boolean;
  /** No envía el token ni intenta renovarlo (login, registro, refresh). */
  sinAuth?: boolean;
}

async function pedir(path: string, o: Opciones): Promise<Response> {
  const headers: Record<string, string> = {};
  if (o.cuerpo !== undefined) headers["Content-Type"] = "application/json";
  if (!o.sinAuth && accessToken) headers.Authorization = `Bearer ${accessToken}`;
  if (o.zona) {
    if (!hayZona()) throw new ApiError(403, { codigo: "zona_padres_requerida" });
    headers["X-Zona-Padres"] = zona!.token;
  }
  return fetch(`${API_URL}${path}`, {
    method: o.metodo ?? (o.cuerpo !== undefined ? "POST" : "GET"),
    headers,
    body: o.cuerpo !== undefined ? JSON.stringify(o.cuerpo) : undefined,
    credentials: "include", // la cookie httpOnly de refresco
  });
}

let renovando: Promise<boolean> | null = null;

/** Renueva el token de acceso con la cookie de refresco. Varias llamadas a la vez comparten una sola petición. */
export function refrescar(): Promise<boolean> {
  renovando ??= (async () => {
    try {
      const r = await pedir("/auth/refresh", { metodo: "POST", cuerpo: {}, sinAuth: true });
      if (!r.ok) return false;
      accessToken = ((await r.json()) as { access_token: string }).access_token;
      return true;
    } catch {
      return false;
    } finally {
      renovando = null;
    }
  })();
  return renovando;
}

async function leer(r: Response): Promise<never | unknown> {
  if (r.status === 204) return undefined;
  const texto = await r.text();
  const datos = texto ? JSON.parse(texto) : undefined;
  if (!r.ok) {
    const detalle = datos && typeof datos === "object" && "detail" in datos ? (datos as { detail: unknown }).detail : datos;
    const err = new ApiError(r.status, detalle);
    if (err.codigo === "zona_padres_requerida") salirDeZona();
    throw err;
  }
  return datos;
}

export async function api<T = void>(path: string, o: Opciones = {}): Promise<T> {
  let r = await pedir(path, o);
  if (r.status === 401 && !o.sinAuth) {
    if (await refrescar()) {
      r = await pedir(path, o);
    } else {
      accessToken = null;
      zona = null;
      oyentes.forEach((fn) => fn());
    }
  }
  return (await leer(r)) as T;
}
