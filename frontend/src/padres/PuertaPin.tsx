import { useState, type FormEvent } from "react";
import { ApiError, api, guardarZona } from "../api/cliente";

interface Props {
  onAbierta: () => void;
}

export default function PuertaPin({ onAbierta }: Props) {
  const [modo, setModo] = useState<"verificar" | "crear">("verificar");
  const [pin, setPin] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);

  async function verificar(): Promise<boolean> {
    try {
      const r = await api<{ zona_token: string; expira_en_min: number }>("/auth/pin/verificar", { cuerpo: { pin } });
      guardarZona(r.zona_token, r.expira_en_min);
      return true;
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        setModo("crear");
        setError("Aún no tienes un PIN. Créalo para proteger esta zona.");
      } else if (e instanceof ApiError && e.status === 403) setError("PIN incorrecto.");
      else if (e instanceof ApiError && e.status === 423) setError("Demasiados intentos. Espera unos minutos y vuelve a probar.");
      else setError(e instanceof Error ? e.message : "No se pudo verificar el PIN");
      return false;
    }
  }

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setOcupado(true);
    try {
      if (modo === "crear") {
        try {
          await api("/auth/pin", { metodo: "PUT", cuerpo: { pin, password } });
        } catch (err) {
          setError(err instanceof ApiError && err.status === 403 ? "La contraseña no es correcta." : err instanceof Error ? err.message : "No se pudo guardar el PIN");
          return;
        }
      }
      if (await verificar()) onAbierta();
    } finally {
      setOcupado(false);
      setPin("");
    }
  }

  return (
    <main className="contenedor estrecho">
      <h1>Zona de padres</h1>
      <p className="suave">
        {modo === "verificar"
          ? "Escribe tu PIN para continuar. Así los niños no pueden entrar aquí."
          : "Elige un PIN de 4 a 6 números y confirma con tu contraseña."}
      </p>
      <form className="tarjeta" onSubmit={enviar}>
        <label htmlFor="pin">PIN</label>
        <input id="pin" type="password" inputMode="numeric" pattern="\d{4,6}" maxLength={6} autoComplete="off" required value={pin} onChange={(e) => setPin(e.target.value.replace(/\D/g, ""))} />
        {modo === "crear" && (
          <>
            <label htmlFor="pw">Contraseña de la cuenta</label>
            <input id="pw" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
          </>
        )}
        {error && <p className="error" role="alert">{error}</p>}
        <p>
          <button className="boton" type="submit" disabled={ocupado || pin.length < 4}>
            {modo === "crear" ? "Crear PIN y entrar" : "Entrar"}
          </button>
        </p>
      </form>
    </main>
  );
}
