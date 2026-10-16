import { Link, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";

/** Marco de las pantallas con sesión iniciada (menos la pantalla de juego, que va sin distracciones). */
export default function Cabecera() {
  const { usuario, salir } = useAuth();
  const navegar = useNavigate();
  return (
    <>
      <header className="cabecera">
        <Link to="/" className="marca">
          NeuroBridge
        </Link>
        <nav className="fila">
          <Link className="boton secundario pequeno" to="/padres">
            Zona de padres
          </Link>
          <button
            className="boton secundario pequeno"
            onClick={async () => {
              await salir();
              navegar("/entrar");
            }}
            title={usuario?.email}
          >
            Salir
          </button>
        </nav>
      </header>
      <Outlet />
    </>
  );
}
