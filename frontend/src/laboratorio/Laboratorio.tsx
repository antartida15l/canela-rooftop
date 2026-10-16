import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { EMOCION_POR_INDICE } from "../ia/emociones";
import { Monitor, type Intervencion } from "../ia/monitor";
import { useVision, type LecturaVision } from "../ia/useVision";

/** Página de pruebas: comprueba cámara, detección de rostro, modelo de emociones y reglas de intervención. */
export default function Laboratorio() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const monitorRef = useRef(new Monitor());
  const t0 = useRef(0);
  const [activo, setActivo] = useState(false);
  const [ultima, setUltima] = useState<LecturaVision | null>(null);
  const [n, setN] = useState(0);
  const [intervenciones, setIntervenciones] = useState<Intervencion[]>([]);

  const { estado, error } = useVision({
    activo,
    videoRef,
    intervaloMs: 3000,
    primeraLecturaMs: 1000,
    onLectura: (l) => {
      if (t0.current === 0) t0.current = performance.now();
      const t = Math.round((performance.now() - t0.current) / 1000);
      setUltima(l);
      setN((x) => x + 1);
      const iv = monitorRef.current.procesar(t, l.atencion, l.emocion, l.rostro);
      if (iv) setIntervenciones((prev) => [...prev, iv]);
    },
  });

  const alternar = () => {
    if (!activo) {
      monitorRef.current = new Monitor();
      t0.current = 0;
      setN(0);
      setUltima(null);
      setIntervenciones([]);
    }
    setActivo(!activo);
  };

  return (
    <main className="contenedor" data-testid="laboratorio">
      <p>
        <Link to="/">← Volver</Link>
      </p>
      <h1>Laboratorio de cámara</h1>
      <p>
        Prueba la cámara y el modelo de emociones. <strong>Nada sale de tu navegador</strong>: no se guardan ni se envían
        imágenes.
      </p>
      <button className="boton" onClick={alternar} data-testid="lab-alternar">
        {activo ? "Detener" : "Iniciar cámara"}
      </button>

      <p data-testid="lab-estado" aria-live="polite">
        Estado: <strong>{estado}</strong>
        {error && <span className="error"> — {error}</span>}
      </p>

      <div className="lab-rejilla">
        <video ref={videoRef} className="lab-video" muted playsInline data-testid="lab-video" />
        <div data-testid="lab-lectura">
          <h2>Última lectura (#{n})</h2>
          {!ultima && <p>Esperando la primera lectura…</p>}
          {ultima && !ultima.rostro && <p data-testid="lab-sin-rostro">No se detecta ningún rostro.</p>}
          {ultima?.rostro && ultima.extra && (
            <>
              <p>
                Emoción: <strong data-testid="lab-emocion">{ultima.emocion}</strong> · Atención:{" "}
                <strong data-testid="lab-atencion">{ultima.atencion?.toFixed(2)}</strong>
              </p>
              <p>
                Giro {ultima.extra.yaw.toFixed(1)}° · Inclinación {ultima.extra.pitch.toFixed(1)}° · Modelo{" "}
                {ultima.extra.msIA} ms · Total {ultima.extra.msTotal} ms
              </p>
              <ul className="barras">
                {EMOCION_POR_INDICE.map((e, i) => (
                  <li key={e}>
                    <span>{e}</span>
                    <meter min={0} max={1} value={ultima.extra!.probs[i]} />
                    <span>{(ultima.extra!.probs[i] * 100).toFixed(0)} %</span>
                  </li>
                ))}
              </ul>
            </>
          )}
          <h2>Intervenciones simuladas</h2>
          <p>Las 5 primeras lecturas calibran. Luego se aplican las reglas del servidor.</p>
          <ul data-testid="lab-intervenciones">
            {intervenciones.map((i) => (
              <li key={i.t}>
                t={i.t}s · {i.tipo} · {i.motivo}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </main>
  );
}
