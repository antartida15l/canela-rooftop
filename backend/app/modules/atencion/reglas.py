from statistics import mean

PARAMS = {
    "intervalo_s": 3,                  # una lectura cada 3 s
    "calibracion_lecturas": 5,
    "alpha": 0.4,                      # suavizado exponencial
    "confirmaciones": 2,               # lecturas seguidas para intervenir
    "ausente_confirmaciones": 3,
    "min_entre_intervenciones_s": 60,
    "escalado_s": 180,                 # otra intervención dentro de este plazo => pausa
    "umbral_relativo": 0.6,
    "umbral_minimo": 0.2,
}

# Etiquetas que el detector puede producir y que se tratan como señal de malestar.
EMOCIONES_MALESTAR = frozenset({"enojo", "miedo", "triste", "asco"})
_PRIORIDAD = ("malestar", "atencion_baja", "ausente")


class Monitor:
    """Decide cuándo sugerir un aviso suave o una pausa. Nunca toma decisiones críticas."""

    def __init__(self, params: dict | None = None):
        self.p = {**PARAMS, **(params or {})}
        self._calibracion: list[float] = []
        self._ema: float | None = None
        self._umbral: float | None = None
        self._cuentas = {m: 0 for m in _PRIORIDAD}
        self._ultima: int | None = None
        self._ultimo_aviso: int | None = None

    @property
    def calibrado(self) -> bool:
        return self._umbral is not None

    def procesar(self, t: int, atencion: float | None, emocion: str | None = None,
                 rostro: bool = True) -> dict | None:
        presente = rostro and atencion is not None
        if not presente:
            self._cuentas["ausente"] += 1
            self._cuentas["malestar"] = 0
            self._cuentas["atencion_baja"] = 0
        else:
            self._cuentas["ausente"] = 0
            a = self.p["alpha"]
            self._ema = atencion if self._ema is None else a * atencion + (1 - a) * self._ema
            if not self.calibrado:
                self._calibracion.append(atencion)
                if len(self._calibracion) >= self.p["calibracion_lecturas"]:
                    base = mean(self._calibracion)
                    self._umbral = max(self.p["umbral_minimo"], base * self.p["umbral_relativo"])
                return None
            baja = self._ema < self._umbral
            self._cuentas["atencion_baja"] = self._cuentas["atencion_baja"] + 1 if baja else 0
            malestar = emocion in EMOCIONES_MALESTAR
            self._cuentas["malestar"] = self._cuentas["malestar"] + 1 if malestar else 0

        if not self.calibrado:
            return None
        motivo = self._motivo_disparado()
        if motivo is None:
            return None
        if self._ultima is not None and t - self._ultima < self.p["min_entre_intervenciones_s"]:
            return None  # muy pronto: se conserva la cuenta y se reintenta

        escalar = self._ultimo_aviso is not None and t - self._ultimo_aviso <= self.p["escalado_s"]
        tipo = "pausa" if escalar else "aviso_suave"
        self._ultima = t
        self._ultimo_aviso = None if tipo == "pausa" else t
        self._cuentas = {m: 0 for m in _PRIORIDAD}
        return {"t": t, "tipo": tipo, "motivo": motivo}

    def _motivo_disparado(self) -> str | None:
        for motivo in _PRIORIDAD:
            minimo = (self.p["ausente_confirmaciones"] if motivo == "ausente"
                      else self.p["confirmaciones"])
            if self._cuentas[motivo] >= minimo:
                return motivo
        return None


def reproducir(lecturas: list[dict], params: dict | None = None) -> list[dict]:
    """Aplica las reglas a una lista de lecturas. Sirve para pruebas y para el port a TypeScript."""
    monitor = Monitor(params)
    salida = []
    for lectura in lecturas:
        r = monitor.procesar(lectura["t"], lectura.get("atencion"), lectura.get("emocion"),
                             lectura.get("rostro", True))
        if r:
            salida.append(r)
    return salida