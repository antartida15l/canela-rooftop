import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import CuentaAdmin from "./auth/CuentaAdmin";
import PantallaAuth from "./auth/PantallaAuth";
import Cabecera from "./Cabecera";
import PortalEspecialista from "./especialista/PortalEspecialista";
import Laboratorio from "./laboratorio/Laboratorio";
import ElegirActividad from "./ninos/ElegirActividad";
import SeleccionNino from "./ninos/SeleccionNino";
import ZonaPadres from "./padres/ZonaPadres";
import PantallaSesion from "./sesion/PantallaSesion";

/** Pantallas de padres e hijos. Cada rol tiene su sitio: no se muestra "Sin permiso" a quien entra por la puerta equivocada. */
function RutaPadre() {
  const { estado, usuario } = useAuth();
  if (estado === "cargando") return <p className="contenedor">Cargando…</p>;
  if (estado === "anonimo") return <Navigate to="/entrar" replace />;
  if (usuario?.rol === "especialista") return <Navigate to="/especialista" replace />;
  if (usuario?.rol === "admin") return <CuentaAdmin />;
  return <Outlet />;
}

function RutaEspecialista() {
  const { estado, usuario } = useAuth();
  if (estado === "cargando") return <p className="contenedor">Cargando…</p>;
  if (estado === "anonimo") return <Navigate to="/entrar" replace />;
  if (usuario?.rol !== "especialista") return <Navigate to="/" replace />;
  return <Outlet />;
}

export default function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AuthProvider>
        <Routes>
          <Route path="/entrar" element={<PantallaAuth />} />
          <Route path="/laboratorio" element={<Laboratorio />} />
          <Route element={<RutaEspecialista />}>
            <Route path="/especialista" element={<PortalEspecialista />} />
          </Route>
          <Route element={<RutaPadre />}>
            <Route path="/sesion/:ninoId" element={<PantallaSesion />} />
            <Route element={<Cabecera />}>
              <Route path="/" element={<SeleccionNino />} />
              <Route path="/jugar/:ninoId" element={<ElegirActividad />} />
              <Route path="/padres" element={<ZonaPadres />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
