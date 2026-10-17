import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/cliente";
import type { NinoCompartido, Reporte } from "../api/tipos";
import { useAuth } from "../auth/AuthContext";
import { fechaCorta } from "../reportes/etiquetas";
import VistaReporte from "../reportes/VistaReporte";

/** Zona de solo lectura para especialistas: ven únicamente lo que cada familia les compartió. */
export default function PortalEspecialista() {
  const { usuario, salir } = useAuth();
  const navegar = useNavigate();
  const [ninos, setNinos] = useState<NinoCompartido[] | null>(null);
  const [ninoId, setNinoId] = useState("");
  const [dias, setDias] = useState(30);
  const [reporte, setReporte] = useState<Reporte | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<NinoCompartido[]>("/especialista/ninos").then(setNinos, (e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!ninoId) return;
    setError(null);
    setReporte(null);
    api<Reporte>(`/especialista/ninos/${ninoId}/reporte?dias=${dias}`).then(setReporte, (e) =>
      setError(e.status === 404 ? "Ya no tienes acceso a este reporte." : e.message),
    );
  }, [ninoId, dias]);

  return (
    <>
      <header className="cabecera no-imprimir">
        <span className="marca">NeuroBridge · Especialistas</span>
        <button
          className="boton secundario pequeno"
          onClick={async () => {
            await salir();
            navegar("/entrar");
          }}
        >
          Salir ({usuario?.email})
        </button>
      </header>
      <main className="contenedor">
        <h1 className="no-imprimir">Niños compartidos contigo</h1>
        <p className="suave no-imprimir">
          Vista de solo lectura. Cada familia decide qué ves y por cuánto tiempo, y puede quitarte el acceso en cualquier
          momento. Cada consulta queda registrada para la familia.
        </p>
        {error && <p className="error" role="alert">{error}</p>}
        {ninos === null && !error && <p>Cargando…</p>}
        {ninos?.length === 0 && <p className="tarjeta" data-testid="sin-ninos">Todavía ninguna familia te ha compartido un reporte.</p>}

        <div className="rejilla-ninos no-imprimir">
          {ninos?.map((n) => (
            <button key={n.nino_id} className="nino" onClick={() => setNinoId(n.nino_id)} aria-pressed={n.nino_id === ninoId}>
              <span className="avatar" aria-hidden="true">{n.nombre.slice(0, 1).toUpperCase()}</span>
              {n.nombre}
              <small className="suave">
                {n.alcance === "completo" ? "Completo" : "Resumen"} · hasta {fechaCorta(n.expira_en)}
              </small>
            </button>
          ))}
        </div>

        {ninoId && (
          <div className="no-imprimir">
            <label htmlFor="p-dias">Período</label>
            <select id="p-dias" value={dias} onChange={(e) => setDias(Number(e.target.value))}>
              <option value={7}>Última semana</option>
              <option value={30}>Últimos 30 días</option>
              <option value={90}>Últimos 90 días</option>
            </select>
          </div>
        )}
        {reporte && <VistaReporte r={reporte} />}
      </main>
    </>
  );
}
