import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/cliente";
import type { Nino } from "../api/tipos";

export default function SeleccionNino() {
  const [ninos, setNinos] = useState<Nino[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const navegar = useNavigate();

  useEffect(() => {
    api<Nino[]>("/ninos").then(setNinos, (e) => setError(e instanceof Error ? e.message : "Error"));
  }, []);

  return (
    <main className="contenedor">
      <h1>¿Quién va a jugar hoy?</h1>
      {error && <p className="error" role="alert">{error}</p>}
      {ninos === null && !error && <p>Cargando…</p>}
      {ninos?.length === 0 && (
        <p className="tarjeta">
          Todavía no hay perfiles. Un adulto puede crear uno en la <Link to="/padres">zona de padres</Link>.
        </p>
      )}
      <div className="rejilla-ninos">
        {ninos?.map((n) => (
          <button key={n.id} className="nino" onClick={() => navegar(`/jugar/${n.id}`)}>
            <span className="avatar" aria-hidden="true">{n.nombre.slice(0, 1).toUpperCase()}</span>
            {n.nombre}
          </button>
        ))}
      </div>
    </main>
  );
}
