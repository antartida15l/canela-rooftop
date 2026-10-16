import { useEffect, useState } from "react";
import { api } from "../api/cliente";
import type { Nino, Observacion, Sesion } from "../api/tipos";

interface Dominio {
  habilidades: Record<string, { nivel: number; dominio: number; racha: number; muestras: number }>;
}

export default function Historial() {
  const [ninos, setNinos] = useState<Nino[]>([]);
  const [ninoId, setNinoId] = useState("");
  const [sesiones, setSesiones] = useState<Sesion[]>([]);
  const [dominio, setDominio] = useState<Dominio | null>(null);
  const [obs, setObs] = useState<{ id: string; lista: Observacion[] } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<Nino[]>("/ninos").then((n) => {
      setNinos(n);
      if (n[0]) setNinoId(n[0].id);
    }, (e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!ninoId) return;
    setObs(null);
    Promise.all([api<Sesion[]>(`/sesiones?nino_id=${ninoId}`), api<Dominio>(`/dominio/${ninoId}`)]).then(
      ([s, d]) => {
        setSesiones(s);
        setDominio(d);
      },
      (e) => setError(e.message),
    );
  }, [ninoId]);

  async function verObservaciones(id: string) {
    setObs({ id, lista: await api<Observacion[]>(`/sesiones/${id}/observaciones`) });
  }

  return (
    <section>
      <h2>Historial</h2>
      {error && <p className="error" role="alert">{error}</p>}
      {ninos.length === 0 ? (
        <p className="suave">Primero crea un perfil.</p>
      ) : (
        <>
          <label htmlFor="h-nino">Perfil</label>
          <select id="h-nino" value={ninoId} onChange={(e) => setNinoId(e.target.value)}>
            {ninos.map((n) => <option key={n.id} value={n.id}>{n.nombre}</option>)}
          </select>

          {dominio && Object.keys(dominio.habilidades).length > 0 && (
            <div className="tarjeta">
              <h3>Nivel por habilidad</h3>
              <ul>
                {Object.entries(dominio.habilidades).map(([h, d]) => (
                  <li key={h}>{h.replace(/_/g, " ")}: nivel {d.nivel} de 3 · dominio {Math.round(d.dominio * 100)} %</li>
                ))}
              </ul>
            </div>
          )}

          {sesiones.length === 0 ? (
            <p className="suave">Todavía no hay sesiones.</p>
          ) : (
            <table>
              <thead>
                <tr><th>Fecha</th><th>Actividad</th><th>Aciertos</th><th>Nota (0–20)</th><th /></tr>
              </thead>
              <tbody>
                {sesiones.map((s) => (
                  <tr key={s.id}>
                    <td>{new Date(s.inicio).toLocaleString()}</td>
                    <td>{s.ajustes.habilidad.replace(/_/g, " ")}</td>
                    <td>{s.fin ? `${s.kpi.correctas ?? 0}/${s.kpi.respondidas ?? 0}` : "sin terminar"}</td>
                    <td>{s.nota ?? "—"}</td>
                    <td>{s.fin && <button className="boton secundario pequeno" onClick={() => verObservaciones(s.id)}>Observaciones</button>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {obs && (
            <div className="tarjeta">
              <h3>Observaciones de la sesión</h3>
              {obs.lista.length === 0 ? (
                <p className="suave">Sin datos de cámara en esta sesión.</p>
              ) : (
                <ul>{obs.lista.map((o, i) => <li key={i} className={o.nivel === "atencion" ? "" : "suave"}>{o.texto}</li>)}</ul>
              )}
            </div>
          )}
        </>
      )}
    </section>
  );
}
