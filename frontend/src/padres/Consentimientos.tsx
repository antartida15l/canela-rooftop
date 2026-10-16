import { useEffect, useState } from "react";
import { api } from "../api/cliente";
import type { Consentimiento } from "../api/tipos";

const TEXTOS = {
  terminos: { titulo: "Términos de uso", detalle: "Necesarios para usar la plataforma. Para retirarlos, elimina la cuenta." },
  camara: {
    titulo: "Cámara (atención y emociones)",
    detalle:
      "Permite detectar señales simples de atención y emoción para sugerir pausas. Las imágenes se analizan en el navegador y nunca se guardan ni se envían; solo se conservan etiquetas. Sin este permiso la sesión funciona igual.",
  },
  investigacion: { titulo: "Investigación", detalle: "Permite usar datos anonimizados para mejorar la plataforma." },
} as const;

export default function Consentimientos() {
  const [lista, setLista] = useState<Consentimiento[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<Consentimiento[]>("/consentimientos").then(setLista, (e) => setError(e.message));
  }, []);

  async function cambiar(tipo: Consentimiento["tipo"], aceptado: boolean) {
    setError(null);
    try {
      setLista(await api<Consentimiento[]>(`/consentimientos/${tipo}`, { metodo: "PUT", cuerpo: { aceptado } }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo guardar");
    }
  }

  return (
    <section>
      <h2>Consentimientos</h2>
      {error && <p className="error" role="alert">{error}</p>}
      {lista.map((c) => (
        <div key={c.tipo} className="tarjeta">
          <h3>{TEXTOS[c.tipo].titulo}</h3>
          <p className="suave">{TEXTOS[c.tipo].detalle}</p>
          {c.requiere_reaceptacion && <p className="error">El texto cambió: hace falta aceptar de nuevo.</p>}
          {c.tipo === "terminos" ? (
            <p className="exito">Aceptados (versión {c.version_aceptada})</p>
          ) : (
            <label className="fila">
              <input type="checkbox" checked={c.aceptado} onChange={(e) => cambiar(c.tipo, e.target.checked)} />
              <span>{c.aceptado ? "Activado" : "Desactivado"}</span>
            </label>
          )}
        </div>
      ))}
    </section>
  );
}
