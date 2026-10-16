import { useEffect, useRef, useState, type RefObject } from "react";
import { angulosCabeza, puntuacionAtencion } from "./atencion";
import { cargarClasificador, type ClasificadorEmociones } from "./clasificador";
import { emocionDominante, SuavizadorEmocion, type Emocion } from "./emociones";
import { cargarLandmarker, detectar, recortarATensor } from "./vision";

export type EstadoVision = "inactivo" | "cargando" | "listo" | "error";

export interface LecturaVision {
  rostro: boolean;
  atencion: number | null;
  emocion: Emocion | null;
  /** Solo para el laboratorio; nunca se envía al servidor. */
  extra?: { yaw: number; pitch: number; probs: number[]; msIA: number; msTotal: number };
}

interface Opciones {
  activo: boolean;
  pausado?: boolean;
  intervaloMs?: number;
  primeraLecturaMs?: number;
  videoRef: RefObject<HTMLVideoElement>;
  onLectura: (l: LecturaVision) => void;
}

async function abrirCamara(): Promise<MediaStream> {
  if (!navigator.mediaDevices?.getUserMedia) throw new Error("Este navegador no permite usar la cámara");
  return navigator.mediaDevices.getUserMedia({
    video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" },
    audio: false,
  });
}

async function leer(
  lm: Awaited<ReturnType<typeof cargarLandmarker>>,
  clasificador: ClasificadorEmociones,
  video: HTMLVideoElement,
  suavizador: SuavizadorEmocion,
): Promise<LecturaVision> {
  const inicio = performance.now();
  const det = detectar(lm, video);
  if (!det.rostro) return { rostro: false, atencion: null, emocion: null };

  const { yaw, pitch } = angulosCabeza(det.matriz);
  const atencion = puntuacionAtencion(yaw, pitch);
  const tensor = recortarATensor(video, det.caja);
  const { probs, ms } = await clasificador.clasificar(tensor);
  const suaves = suavizador.actualizar(probs);
  const { emocion } = emocionDominante(suaves);
  return {
    rostro: true,
    atencion,
    emocion,
    extra: { yaw, pitch, probs: suaves, msIA: ms, msTotal: Math.round(performance.now() - inicio) },
  };
}

/**
 * Abre la cámara, carga los modelos y emite una lectura cada `intervaloMs` (3 s por defecto).
 * Solo se conservan etiquetas y números; los fotogramas se procesan en memoria y se descartan.
 */
export function useVision({ activo, pausado = false, intervaloMs = 3000, primeraLecturaMs, videoRef, onLectura }: Opciones) {
  const [estado, setEstado] = useState<EstadoVision>("inactivo");
  const [error, setError] = useState<string | null>(null);
  const onLecturaRef = useRef(onLectura);
  const pausadoRef = useRef(pausado);
  onLecturaRef.current = onLectura;
  pausadoRef.current = pausado;

  useEffect(() => {
    if (!activo) {
      setEstado("inactivo");
      return;
    }
    let cancelado = false;
    let temporizador: number | undefined;
    let flujo: MediaStream | undefined;
    const suavizador = new SuavizadorEmocion(0.4);

    (async () => {
      setEstado("cargando");
      setError(null);
      try {
        const [lm, clasificador, camara] = await Promise.all([cargarLandmarker(), cargarClasificador(), abrirCamara()]);
        flujo = camara;
        if (cancelado) {
          camara.getTracks().forEach((t) => t.stop());
          return;
        }
        const video = videoRef.current;
        if (!video) throw new Error("No hay elemento de vídeo");
        video.srcObject = camara;
        await video.play();
        if (cancelado) return;
        setEstado("listo");

        const ciclo = async () => {
          if (cancelado) return;
          const inicio = performance.now();
          if (!pausadoRef.current) {
            try {
              const lectura = await leer(lm, clasificador, video, suavizador);
              if (!cancelado) onLecturaRef.current(lectura);
            } catch (e) {
              console.warn("Lectura omitida:", e);
            }
          }
          if (!cancelado) {
            temporizador = window.setTimeout(ciclo, Math.max(0, intervaloMs - (performance.now() - inicio)));
          }
        };
        temporizador = window.setTimeout(ciclo, primeraLecturaMs ?? intervaloMs);
      } catch (e) {
        if (cancelado) return;
        const nombre = e instanceof DOMException ? e.name : "";
        setError(
          nombre === "NotAllowedError"
            ? "No se dio permiso para usar la cámara."
            : nombre === "NotFoundError"
              ? "No se encontró ninguna cámara."
              : e instanceof Error
                ? e.message
                : String(e),
        );
        setEstado("error");
      }
    })();

    return () => {
      cancelado = true;
      window.clearTimeout(temporizador);
      flujo?.getTracks().forEach((t) => t.stop());
      if (videoRef.current) videoRef.current.srcObject = null;
    };
  }, [activo, intervaloMs, primeraLecturaMs, videoRef]);

  return { estado, error };
}
