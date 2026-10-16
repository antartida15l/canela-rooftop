import { useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthContext";

export default function PantallaAuth() {
  const { estado, entrar, registrar } = useAuth();
  const [modo, setModo] = useState<"entrar" | "registro">("entrar");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [acepta, setAcepta] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);

  if (estado === "autenticado") return <Navigate to="/" replace />;

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setOcupado(true);
    try {
      if (modo === "entrar") await entrar(email, password);
      else await registrar(email, password, acepta);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo completar la operación");
    } finally {
      setOcupado(false);
    }
  }

  return (
    <main className="contenedor estrecho">
      <h1>NeuroBridge</h1>
      <p className="suave">Aprender a tu ritmo, con apoyo.</p>
      <div className="pestanas" role="tablist">
        <button role="tab" aria-selected={modo === "entrar"} className={`boton pestana ${modo === "entrar" ? "" : "secundario"}`} onClick={() => setModo("entrar")}>
          Entrar
        </button>
        <button role="tab" aria-selected={modo === "registro"} className={`boton pestana ${modo === "registro" ? "" : "secundario"}`} onClick={() => setModo("registro")}>
          Crear cuenta
        </button>
      </div>
      <form className="tarjeta" onSubmit={enviar}>
        <label htmlFor="email">Correo</label>
        <input id="email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        <label htmlFor="password">Contraseña</label>
        <input
          id="password"
          type="password"
          autoComplete={modo === "entrar" ? "current-password" : "new-password"}
          required
          minLength={modo === "registro" ? 10 : undefined}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {modo === "registro" && (
          <>
            <p className="suave">Mínimo 10 caracteres.</p>
            <label className="fila">
              <input type="checkbox" checked={acepta} onChange={(e) => setAcepta(e.target.checked)} />
              <span>Acepto los términos de uso y el tratamiento de datos personales de mi hijo o hija.</span>
            </label>
            <p className="suave">(Textos legales pendientes de validación por un abogado.)</p>
          </>
        )}
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <p>
          <button className="boton" type="submit" disabled={ocupado || (modo === "registro" && !acepta)}>
            {ocupado ? "Un momento…" : modo === "entrar" ? "Entrar" : "Crear cuenta"}
          </button>
        </p>
      </form>
    </main>
  );
}
