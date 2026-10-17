import { useCallback, useEffect, useState, type FormEvent } from "react";
import { api } from "../api/cliente";
import type { Acceso, EventoAuditoria, Nino } from "../api/tipos";
import { fechaCorta, fechaHora } from "../reportes/etiquetas";

const ACCION = { otorgado: "Acceso otorgado", revocado: "Acceso revocado", consultado: "Consultó el reporte" } as const;

export default function Especialistas() {
  const [ninos, setNinos] = useState<Nino[] | null>(null);
  const [ninoId, setNinoId] = useState("");
  const [accesos, setAccesos] = useState<Acceso[]>([]);
  const [eventos, setEventos] = useState<EventoAuditoria[]>([]);
  const [email, setEmail] = useState("");
  const [alcance, setAlcance] = useState<"resumen" | "completo">("resumen");
  const [dias, setDias] = useState(30);
  const [error, setError] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);

  useEffect(() => {
    api<Nino[]>("/ninos").then((n) => {
      setNinos(n);
      if (n[0]) setNinoId(n[0].id);
    }, (e) => setError(e.message));
  }, []);

  const cargar = useCallback(async () => {
    if (!ninoId) return;
    try {
      const [a, e] = await Promise.all([
        api<Acceso[]>(`/accesos?nino_id=${ninoId}`),
        api<EventoAuditoria[]>(`/accesos/auditoria?nino_id=${ninoId}`),
      ]);
      setAccesos(a);
      setEventos(e);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    }
  }, [ninoId]);
  useEffect(() => {
    void cargar();
  }, [cargar]);

  async function otorgar(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setOcupado(true);
    try {
      await api("/accesos", { zona: true, cuerpo: { nino_id: ninoId, email, alcance, dias } });
      setEmail("");
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo dar el acceso");
    } finally {
      setOcupado(false);
    }
  }

  async function revocar(a: Acceso) {
    if (!window.confirm(`¿Quitar el acceso de ${a.especialista_email}?`)) return;
    try {
      await api(`/accesos/${a.id}`, { metodo: "DELETE", zona: true });
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo quitar el acceso");
    }
  }

  return (
    <section>
      <h2>Especialistas</h2>
      <p className="suave">
        Un especialista (psicopedagogo, terapeuta…) puede ver un reporte de <strong>solo lectura</strong> de tu hijo o hija.
        Nunca ve sus respuestas una por una ni la condición declarada. El acceso dura como máximo 90 días, puedes quitarlo
        cuando quieras y cada consulta queda registrada abajo.
      </p>
      {error && <p className="error" role="alert">{error}</p>}
      {ninos?.length === 0 && <p className="suave">Primero crea un perfil.</p>}

      {ninos && ninos.length > 0 && (
        <>
          <label htmlFor="e-nino">Perfil</label>
          <select id="e-nino" value={ninoId} onChange={(e) => setNinoId(e.target.value)}>
            {ninos.map((n) => <option key={n.id} value={n.id}>{n.nombre}</option>)}
          </select>

          <form className="tarjeta" onSubmit={otorgar}>
            <h3>Dar acceso</h3>
            <label htmlFor="e-email">Correo del especialista (con cuenta de especialista en NeuroBridge)</label>
            <input id="e-email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
            <label htmlFor="e-alcance">Qué puede ver</label>
            <select id="e-alcance" value={alcance} onChange={(e) => setAlcance(e.target.value as "resumen" | "completo")}>
              <option value="resumen">Resumen: sesiones, notas y nivel por habilidad</option>
              <option value="completo">Completo: además atención y recomendaciones</option>
            </select>
            <label htmlFor="e-dias">Duración (días, máximo 90)</label>
            <input id="e-dias" type="number" min={1} max={90} required value={dias} onChange={(e) => setDias(Number(e.target.value))} />
            <p><button className="boton" type="submit" disabled={ocupado}>Dar acceso</button></p>
          </form>

          <h3>Accesos</h3>
          {accesos.length === 0 ? (
            <p className="suave">Nadie tiene acceso.</p>
          ) : (
            <table data-testid="tabla-accesos">
              <thead><tr><th>Especialista</th><th>Alcance</th><th>Estado</th><th>Vence</th><th /></tr></thead>
              <tbody>
                {accesos.map((a) => (
                  <tr key={a.id}>
                    <td>{a.especialista_email}</td>
                    <td>{a.alcance === "completo" ? "Completo" : "Resumen"}</td>
                    <td>{a.estado}</td>
                    <td>{fechaCorta(a.expira_en)}</td>
                    <td>{a.estado === "vigente" && <button className="boton peligro pequeno" onClick={() => revocar(a)}>Quitar acceso</button>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <h3>Registro de actividad</h3>
          {eventos.length === 0 ? (
            <p className="suave">Aún no hay actividad.</p>
          ) : (
            <ul data-testid="auditoria">
              {eventos.map((e) => (
                <li key={e.id}>{fechaHora(e.fecha)} · {ACCION[e.accion]} · {e.especialista_email}</li>
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  );
}
