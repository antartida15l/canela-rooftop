import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { ApiError, api } from "../api/cliente";
import type { CierreEnvio, CierreResultado, Ejercicio, PausaEnvio, RespuestaEnvio, LecturaEnvio, Sesion } from "../api/tipos";
import { Monitor, type Intervencion } from "../ia/monitor";
import { useVision, type LecturaVision } from "../ia/useVision";

type Fase = "iniciando" | "jugando" | "pausa" | "cerrando" | "fin" | "error";
type Retro = { tipo: "ok" | "reintento" | "siguiente"; texto: string } | null;

const MAX_INTENTOS = 3;
const esperar = (ms: number) => new Promise<void>((r) => window.setTimeout(r, ms));
const mensajeDe = (e: unknown) => (e instanceof ApiError || e instanceof Error ? e.message : "Algo salió mal");

export default function PantallaSesion() {
  const { ninoId } = useParams();
  const [params] = useSearchParams();
  const habilidad = params.get("h") ?? "";
  const navegar = useNavigate();

  const [fase, setFaseEstado] = useState<Fase>("iniciando");
  const [error, setError] = useState<string | null>(null);
  const [errorEnvio, setErrorEnvio] = useState(false);
  const [sesion, setSesion] = useState<Sesion | null>(null);
  const [ejercicios, setEjercicios] = useState<Ejercicio[]>([]);
  const [indice, setIndice] = useState(0);
  const [intentos, setIntentos] = useState<number[]>([]);
  const [retro, setRetro] = useState<Retro>(null);
  const [verificando, setVerificando] = useState(false);
  const [aviso, setAviso] = useState<string | null>(null);
  const [pausa, setPausa] = useState<{ motivo: PausaEnvio["motivo"]; restante: number } | null>(null);
  const [resultado, setResultado] = useState<CierreResultado | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  // Estado mutable que no debe provocar renders ni quedar obsoleto dentro de temporizadores
  const S = useRef({
    fase: "iniciando" as Fase,
    iniciado: false,
    cerrando: false,
    indice: 0,
    inicioMs: 0,
    activoS: 0,
    ultimaPausaProgS: 0,
    reloj: { acum: 0, desde: null as number | null },
    monitor: null as Monitor | null,
    pausaActual: null as { motivo: PausaEnvio["motivo"]; inicioS: number; desde: number } | null,
    respuestas: [] as RespuestaEnvio[],
    lecturas: [] as LecturaEnvio[],
    intervenciones: [] as Intervencion[],
    pausas: [] as PausaEnvio[],
  }).current;

  const cambiarFase = (f: Fase) => {
    S.fase = f;
    setFaseEstado(f);
  };
  const segundos = () => Math.floor((performance.now() - S.inicioMs) / 1000);
  const arrancarReloj = () => {
    S.reloj.desde = performance.now();
  };
  const detenerReloj = () => {
    if (S.reloj.desde !== null) S.reloj.acum += performance.now() - S.reloj.desde;
    S.reloj.desde = null;
  };
  const leerYReiniciarReloj = () => {
    detenerReloj();
    const ms = Math.min(600_000, Math.round(S.reloj.acum));
    S.reloj.acum = 0;
    return ms;
  };

  // ---------- Pausas ----------
  function registrarPausaAbierta() {
    const p = S.pausaActual;
    if (!p) return;
    if (S.pausas.length < 50) {
      S.pausas.push({ inicio_s: p.inicioS, duracion_s: Math.round((performance.now() - p.desde) / 1000), motivo: p.motivo });
    }
    S.pausaActual = null;
  }
  function empezarPausa(motivo: PausaEnvio["motivo"]) {
    if (S.fase !== "jugando") return;
    detenerReloj();
    S.pausaActual = { motivo, inicioS: segundos(), desde: performance.now() };
    setPausa({ motivo, restante: sesion?.ajustes.pausa_seg ?? 30 });
    setAviso(null);
    cambiarFase("pausa");
  }
  function reanudar() {
    registrarPausaAbierta();
    setPausa(null);
    arrancarReloj();
    cambiarFase("jugando");
  }

  // ---------- Cierre ----------
  async function enviar() {
    if (!sesion) return;
    const cuerpo: CierreEnvio = {
      respuestas: S.respuestas,
      detalle: {
        pausas: S.pausas.slice(0, 50),
        lecturas: S.lecturas.slice(0, 1500),
        intervenciones: S.intervenciones.slice(0, 100),
      },
    };
    try {
      setResultado(await api<CierreResultado>(`/sesiones/${sesion.id}/cerrar`, { cuerpo }));
      cambiarFase("fin");
    } catch (e) {
      setError(mensajeDe(e));
      setErrorEnvio(true);
      cambiarFase("error");
    }
  }
  async function terminar() {
    if (S.cerrando || !sesion) return;
    S.cerrando = true;
    detenerReloj();
    registrarPausaAbierta();
    setPausa(null);
    setAviso(null);
    cambiarFase("cerrando");
    await enviar();
  }

  // Los temporizadores llaman siempre a la versión más reciente de estas funciones
  const acciones = useRef({ terminar, empezarPausa, enviar });
  acciones.current = { terminar, empezarPausa, enviar };

  // ---------- Inicio ----------
  useEffect(() => {
    if (S.iniciado || !ninoId || !habilidad) return;
    S.iniciado = true;
    (async () => {
      try {
        const s = await api<Sesion>("/sesiones", { cuerpo: { nino_id: ninoId, habilidad } });
        const cantidad = Math.min(20, Math.max(1, s.ajustes.ejercicios_objetivo ?? 10));
        const lote = await api<Ejercicio[]>(`/sesiones/${s.id}/ejercicios?cantidad=${cantidad}`);
        if (lote.length === 0) throw new Error("Todavía no hay ejercicios para esta actividad.");
        S.monitor = new Monitor(s.ajustes.atencion ?? {});
        S.inicioMs = performance.now();
        setSesion(s);
        setEjercicios(lote);
        arrancarReloj();
        cambiarFase("jugando");
      } catch (e) {
        setError(mensajeDe(e));
        cambiarFase("error");
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ninoId, habilidad]);

  // Reloj de la sesión: solo cuenta el tiempo activo (sin pausas). Aplica los ajustes congelados.
  useEffect(() => {
    if (fase !== "jugando" || !sesion) return;
    const aj = sesion.ajustes;
    const id = window.setInterval(() => {
      S.activoS += 1;
      if (aj.sesion_min && S.activoS >= aj.sesion_min * 60) {
        void acciones.current.terminar();
        return;
      }
      const cada = (aj.pausa_cada_min ?? 0) * 60;
      if (cada > 0 && S.activoS - S.ultimaPausaProgS >= cada) {
        S.ultimaPausaProgS = S.activoS;
        acciones.current.empezarPausa("programada");
      }
    }, 1000);
    return () => window.clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fase, sesion]);

  useEffect(() => {
    if (fase !== "pausa") return;
    const id = window.setInterval(() => setPausa((p) => (p ? { ...p, restante: Math.max(0, p.restante - 1) } : p)), 1000);
    return () => window.clearInterval(id);
  }, [fase]);

  // ---------- Cámara (solo si la sesión nació con consentimiento) ----------
  const onLectura = useCallback((l: LecturaVision) => {
    if (S.fase !== "jugando" || !S.monitor) return;
    const t = segundos();
    const atencion = l.atencion === null ? null : Math.round(l.atencion * 1000) / 1000;
    if (S.lecturas.length < 1500) S.lecturas.push({ t, rostro: l.rostro, atencion, emocion: l.emocion });
    const iv = S.monitor.procesar(t, atencion, l.emocion, l.rostro);
    if (!iv) return;
    if (S.intervenciones.length < 100) S.intervenciones.push(iv);
    if (iv.tipo === "pausa") acciones.current.empezarPausa("sugerida");
    else {
      setAviso("Vas muy bien 🌟 Si quieres, puedes respirar un momento.");
      window.setTimeout(() => setAviso(null), 9000);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const camaraPermitida = !!sesion?.ajustes.camara;
  const vision = useVision({
    activo: camaraPermitida && (fase === "jugando" || fase === "pausa"),
    pausado: fase === "pausa",
    intervaloMs: (sesion?.ajustes.atencion?.intervalo_s ?? 3) * 1000,
    videoRef,
    onLectura,
  });

  // ---------- Respuestas ----------
  function avanzar() {
    setRetro(null);
    setIntentos([]);
    const sig = S.indice + 1;
    if (sig >= ejercicios.length) {
      void acciones.current.terminar();
      return;
    }
    S.indice = sig;
    setIndice(sig);
    if (S.fase === "jugando") arrancarReloj();
  }

  async function elegir(i: number) {
    const ej = ejercicios[indice];
    if (!sesion || !ej || verificando || fase !== "jugando") return;
    const elecciones = [...intentos, i];
    setVerificando(true);
    try {
      const r = await api<{ correcta: boolean }>(`/sesiones/${sesion.id}/ejercicios/${ej.id}/verificar`, {
        cuerpo: { eleccion: i },
      });
      if (r.correcta || elecciones.length >= MAX_INTENTOS) {
        S.respuestas.push({ ejercicio_id: ej.id, elecciones, ms: leerYReiniciarReloj() });
        setRetro(
          r.correcta
            ? { tipo: "ok", texto: "¡Muy bien! 🎉" }
            : { tipo: "siguiente", texto: "Vamos con otro. ¡Tú puedes! 💪" },
        );
        await esperar(r.correcta ? 900 : 1200);
        avanzar();
      } else {
        setIntentos(elecciones);
        setRetro({ tipo: "reintento", texto: "Casi. Inténtalo otra vez 🙂" });
      }
    } catch {
      setRetro({ tipo: "reintento", texto: "Hubo un problema de conexión. Inténtalo otra vez." });
    } finally {
      setVerificando(false);
    }
  }

  // ---------- Pantallas ----------
  if (fase === "iniciando") {
    return (
      <main className="sesion">
        <div className="sesion-cuerpo"><p data-testid="fase">Preparando tu actividad…</p></div>
      </main>
    );
  }

  if (fase === "error") {
    return (
      <main className="sesion">
        <div className="sesion-cuerpo">
          <div className="tarjeta" style={{ maxWidth: 520 }} data-testid="fase-error">
            <h1>Ups</h1>
            <p className="error" role="alert">{error}</p>
            <div className="fila">
              {errorEnvio && (
                <button className="boton" onClick={() => { setError(null); cambiarFase("cerrando"); void acciones.current.enviar(); }}>
                  Reintentar
                </button>
              )}
              <button className="boton secundario" onClick={() => navegar("/")}>Volver al inicio</button>
            </div>
          </div>
        </div>
      </main>
    );
  }

  if (fase === "cerrando") {
    return (
      <main className="sesion">
        <div className="sesion-cuerpo"><p data-testid="fase">Guardando tu trabajo…</p></div>
      </main>
    );
  }

  if (fase === "fin") {
    const resp = Number(resultado?.kpi.respondidas ?? 0);
    const ok = Number(resultado?.kpi.correctas ?? 0);
    const estrellas = resp === 0 ? 0 : ok / resp >= 0.8 ? 3 : ok / resp >= 0.5 ? 2 : 1;
    return (
      <main className="sesion">
        <div className="sesion-cuerpo">
          <div style={{ textAlign: "center" }} data-testid="fase-fin">
            <h1>{resp === 0 ? "¡Gracias por venir!" : "¡Terminaste!"}</h1>
            {estrellas > 0 && <p className="estrellas" aria-label={`${estrellas} estrellas`}>{"⭐".repeat(estrellas)}</p>}
            <p>{resp > 0 ? `Respondiste ${resp} ${resp === 1 ? "ejercicio" : "ejercicios"}.` : "Vuelve cuando quieras."}</p>
            <button className="boton" onClick={() => navegar("/")}>Volver al inicio</button>
          </div>
        </div>
      </main>
    );
  }

  const ej = ejercicios[indice];
  return (
    <main className="sesion" data-testid="sesion">
      <div className="sesion-barra">
        <div className="puntos" role="img" aria-label={`Ejercicio ${indice + 1} de ${ejercicios.length}`}>
          {ejercicios.map((e, i) => (
            <span key={e.id} className={`punto ${i < indice ? "hecho" : i === indice ? "actual" : ""}`} />
          ))}
        </div>
        <div className="fila">
          {camaraPermitida && (
            <div className="camara" data-testid="camara">
              <video ref={videoRef} muted playsInline style={{ display: vision.estado === "listo" ? "block" : "none" }} />
              <span>
                {vision.estado === "cargando" && "Preparando cámara…"}
                {vision.estado === "listo" && "📷 Cámara activa · no se guardan imágenes"}
                {vision.estado === "error" && "Cámara no disponible. Seguimos sin ella."}
              </span>
            </div>
          )}
          <button className="boton secundario pequeno" onClick={() => empezarPausa("solicitada")} data-testid="pedir-pausa">
            Necesito una pausa
          </button>
          <button
            className="boton secundario pequeno"
            onClick={() => window.confirm("¿Terminar por hoy?") && void terminar()}
          >
            Terminar
          </button>
        </div>
      </div>

      <div className="sesion-cuerpo">
        <div>
          <h1 className="enunciado" data-testid="enunciado">{ej.enunciado}</h1>
          <div className="opciones" role="group" aria-label="Respuestas">
            {ej.opciones.map((o, i) => (
              <button key={i} className="opcion" data-testid={`opcion-${i}`} disabled={verificando || fase !== "jugando"} onClick={() => void elegir(i)}>
                {o}
              </button>
            ))}
          </div>
          <p className={`mensaje ${retro?.tipo ?? ""}`} aria-live="polite" data-testid="retro">{retro?.texto ?? ""}</p>
        </div>
      </div>

      {aviso && fase === "jugando" && (
        <div className="aviso-suave" role="status" data-testid="aviso">
          <span>{aviso}</span>
          <button className="boton secundario pequeno" onClick={() => { setAviso(null); empezarPausa("solicitada"); }}>Descansar</button>
          <button className="boton pequeno" onClick={() => setAviso(null)}>Seguir</button>
        </div>
      )}

      {fase === "pausa" && pausa && (
        <div className="superposicion" role="dialog" aria-modal="true" aria-label="Pausa" data-testid="pausa">
          <div>
            <h1>Hagamos una pausa 🌿</h1>
            <p>Respira despacio: inhala cuando crezca, exhala cuando se achique.</p>
            <div className="respira" aria-hidden="true" />
            <p className="cuenta" aria-live="off">{pausa.restante > 0 ? pausa.restante : "¡Listo!"}</p>
            <button className="boton" disabled={pausa.restante > 0} onClick={reanudar} data-testid="continuar">
              Continuar
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
