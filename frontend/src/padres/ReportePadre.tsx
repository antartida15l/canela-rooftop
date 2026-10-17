import { useEffect, useState } from "react";
import { api } from "../api/cliente";
import type { Nino, Reporte } from "../api/tipos";
import VistaReporte from "../reportes/VistaReporte";

export default function ReportePadre() {
  const [ninos, setNinos] = useState<Nino[] | null>(null);
  const [ninoId, setNinoId] = useState("");
  const [dias, setDias] = useState(30);
  const [reporte, setReporte] = useState<Reporte | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<Nino[]>("/ninos").then((n) => {
      setNinos(n);
      if (n[0]) setNinoId(n[0].id);
    }, (e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!ninoId) return;
    setError(null);
    api<Reporte>(`/reportes/${ninoId}?dias=${dias}`).then(setReporte, (e) => setError(e.message));
  }, [ninoId, dias]);

  return (
    <section>
      <h2 className="no-imprimir">Reporte</h2>
      {error && <p className="error" role="alert">{error}</p>}
      {ninos?.length === 0 && <p className="suave">Primero crea un perfil.</p>}
      {ninos && ninos.length > 0 && (
        <div className="fila no-imprimir">
          <div>
            <label htmlFor="r-nino">Perfil</label>
            <select id="r-nino" value={ninoId} onChange={(e) => setNinoId(e.target.value)}>
              {ninos.map((n) => <option key={n.id} value={n.id}>{n.nombre}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="r-dias">Período</label>
            <select id="r-dias" value={dias} onChange={(e) => setDias(Number(e.target.value))}>
              <option value={7}>Última semana</option>
              <option value={30}>Últimos 30 días</option>
              <option value={90}>Últimos 90 días</option>
            </select>
          </div>
        </div>
      )}
      {reporte && <VistaReporte r={reporte} />}
    </section>
  );
}
