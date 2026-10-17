import { useNavigate } from "react-router-dom";
import { useAuth } from "./AuthContext";

/** Las cuentas de administrador gestionan contenido por la API; no usan las pantallas de padres. */
export default function CuentaAdmin() {
  const { usuario, salir } = useAuth();
  const navegar = useNavigate();
  return (
    <main className="contenedor estrecho" data-testid="cuenta-admin">
      <h1>Cuenta de administrador</h1>
      <p>
        Estás conectado como <strong>{usuario?.email}</strong>, una cuenta de administrador. Desde aquí se gestiona el
        contenido (activar ejercicios) usando la documentación de la API, no las pantallas de padres.
      </p>
      <p className="suave">Para jugar o ver reportes, entra con una cuenta de padre.</p>
      <button
        className="boton"
        onClick={async () => {
          await salir();
          navegar("/entrar");
        }}
      >
        Salir
      </button>
    </main>
  );
}
