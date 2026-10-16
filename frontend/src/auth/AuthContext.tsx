import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { alPerderSesion, api, fijarToken, refrescar } from "../api/cliente";
import type { Usuario } from "../api/tipos";

type Estado = "cargando" | "anonimo" | "autenticado";

interface Contexto {
  estado: Estado;
  usuario: Usuario | null;
  entrar(email: string, password: string): Promise<void>;
  registrar(email: string, password: string, aceptaTerminos: boolean): Promise<void>;
  salir(): Promise<void>;
  salirDeTodo(): Promise<void>;
}

const Ctx = createContext<Contexto | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [estado, setEstado] = useState<Estado>("cargando");
  const [usuario, setUsuario] = useState<Usuario | null>(null);

  const cargarUsuario = useCallback(async () => {
    setUsuario(await api<Usuario>("/auth/yo"));
    setEstado("autenticado");
  }, []);

  // Al abrir la aplicación: si hay cookie de refresco válida, se recupera la sesión
  useEffect(() => {
    (async () => {
      try {
        if (await refrescar()) {
          await cargarUsuario();
          return;
        }
      } catch {
        /* sin sesión */
      }
      setEstado("anonimo");
    })();
  }, [cargarUsuario]);

  useEffect(
    () =>
      alPerderSesion(() => {
        setUsuario(null);
        setEstado("anonimo");
      }),
    [],
  );

  const valor = useMemo<Contexto>(
    () => ({
      estado,
      usuario,
      async entrar(email, password) {
        const r = await api<{ access_token: string }>("/auth/login", { cuerpo: { email, password }, sinAuth: true });
        fijarToken(r.access_token);
        await cargarUsuario();
      },
      async registrar(email, password, aceptaTerminos) {
        const r = await api<{ access_token: string }>("/auth/registro", {
          cuerpo: { email, password, acepta_terminos: aceptaTerminos },
          sinAuth: true,
        });
        fijarToken(r.access_token);
        await cargarUsuario();
      },
      async salir() {
        await api("/auth/logout", { metodo: "POST", sinAuth: true }).catch(() => undefined);
        fijarToken(null);
        setUsuario(null);
        setEstado("anonimo");
      },
      async salirDeTodo() {
        await api("/auth/logout-todo", { metodo: "POST" }).catch(() => undefined);
        fijarToken(null);
        setUsuario(null);
        setEstado("anonimo");
      },
    }),
    [estado, usuario, cargarUsuario],
  );

  return <Ctx.Provider value={valor}>{children}</Ctx.Provider>;
}

export function useAuth(): Contexto {
  const c = useContext(Ctx);
  if (!c) throw new Error("useAuth fuera de AuthProvider");
  return c;
}
