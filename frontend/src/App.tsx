import { BrowserRouter, Navigate, Outlet, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import PantallaAuth from "./auth/PantallaAuth";
import Cabecera from "./Cabecera";
import Laboratorio from "./laboratorio/Laboratorio";
import ElegirActividad from "./ninos/ElegirActividad";
import SeleccionNino from "./ninos/SeleccionNino";
import ZonaPadres from "./padres/ZonaPadres";
import PantallaSesion from "./sesion/PantallaSesion";

function RutaProtegida() {
  const { estado } = useAuth();
  if (estado === "cargando") return <p className="contenedor">Cargando…</p>;
  if (estado === "anonimo") return <Navigate to="/entrar" replace />;
  return <Outlet />;
}

export default function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AuthProvider>
        <Routes>
          <Route path="/entrar" element={<PantallaAuth />} />
          <Route path="/laboratorio" element={<Laboratorio />} />
          <Route element={<RutaProtegida />}>
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
