import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { hayZona, salirDeZona } from "../api/cliente";
import { useAuth } from "../auth/AuthContext";
import Consentimientos from "./Consentimientos";
import Especialistas from "./Especialistas";
import Historial from "./Historial";
import ListaNinos from "./ListaNinos";
import PuertaPin from "./PuertaPin";
import ReportePadre from "./ReportePadre";

type Seccion = "ninos" | "reporte" | "especialistas" | "consentimientos" | "historial";

export default function ZonaPadres() {
  const [abierta, setAbierta] = useState(hayZona());
  const [seccion, setSeccion] = useState<Seccion>("ninos");
  const { salirDeTodo } = useAuth();
  const navegar = useNavigate();

  // La zona se bloquea sola cuando vence el token (5 minutos)
  useEffect(() => {
    if (!abierta) return;
    const id = window.setInterval(() => {
      if (!hayZona()) setAbierta(false);
    }, 1000);
    return () => window.clearInterval(id);
  }, [abierta]);

  if (!abierta) return <PuertaPin onAbierta={() => setAbierta(true)} />;

  const pestana = (s: Seccion, texto: string) => (
    <button className={`boton pestana ${seccion === s ? "" : "secundario"}`} onClick={() => setSeccion(s)}>
      {texto}
    </button>
  );

  return (
    <main className="contenedor">
      <div className="fila" style={{ justifyContent: "space-between" }}>
        <h1>Zona de padres</h1>
        <button
          className="boton secundario"
          onClick={() => {
            salirDeZona();
            navegar("/");
          }}
        >
          Cerrar zona de padres
        </button>
      </div>
      <div className="pestanas no-imprimir" style={{ flexWrap: "wrap" }}>
        {pestana("ninos", "Perfiles")}
        {pestana("reporte", "Reporte")}
        {pestana("especialistas", "Especialistas")}
        {pestana("consentimientos", "Consentimientos")}
        {pestana("historial", "Historial")}
      </div>
      {seccion === "ninos" && <ListaNinos />}
      {seccion === "reporte" && <ReportePadre />}
      {seccion === "especialistas" && <Especialistas />}
      {seccion === "consentimientos" && <Consentimientos />}
      {seccion === "historial" && <Historial />}
      <hr />
      <p>
        <button
          className="boton secundario pequeno"
          onClick={async () => {
            await salirDeTodo();
            navegar("/entrar");
          }}
        >
          Cerrar sesión en todos los dispositivos
        </button>
      </p>
    </main>
  );
}
