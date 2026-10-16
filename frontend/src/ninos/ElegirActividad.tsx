import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/cliente";
import type { Nino } from "../api/tipos";
import { HABILIDADES } from "../config";

export default function ElegirActividad() {
  const { ninoId } = useParams();
  const [nino, setNino] = useState<Nino | null>(null);
  const [error, setError] = useState<string | null>(null);
  const navegar = useNavigate();

  useEffect(() => {
    api<Nino>(`/ninos/${ninoId}`).then(setNino, (e) => setError(e instanceof Error ? e.message : "Error"));
  }, [ninoId]);

  return (
    <main className="contenedor">
      <p><Link to="/">← Cambiar de jugador</Link></p>
      {error && <p className="error" role="alert">{error}</p>}
      {nino && <h1>¡Hola, {nino.nombre}! ¿Qué quieres hacer?</h1>}
      <div className="actividades">
        {HABILIDADES.map((h) => (
          <button key={h.id} className="actividad" onClick={() => navegar(`/sesion/${ninoId}?h=${h.id}`)}>
            <span aria-hidden="true">{h.emoji}</span>
            {h.nombre}
          </button>
        ))}
      </div>
    </main>
  );
}
