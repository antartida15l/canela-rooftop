import { useCallback, useEffect, useState, type FormEvent } from "react";
import { api } from "../api/cliente";
import type { Nino } from "../api/tipos";

const CONDICIONES = [
  { valor: "ninguna", texto: "Ninguna / no aplica" },
  { valor: "tdah", texto: "TDAH" },
  { valor: "tea", texto: "TEA" },
  { valor: "dislexia", texto: "Dislexia" },
  { valor: "discalculia", texto: "Discalculia" },
  { valor: "otra", texto: "Otra" },
  { valor: "prefiero_no_decir", texto: "Prefiero no decirlo" },
];

export default function ListaNinos() {
  const [ninos, setNinos] = useState<Nino[]>([]);
  const [nombre, setNombre] = useState("");
  const [edad, setEdad] = useState("8");
  const [condicion, setCondicion] = useState("ninguna");
  const [error, setError] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);

  const cargar = useCallback(() => api<Nino[]>("/ninos").then(setNinos, (e) => setError(e.message)), []);
  useEffect(() => {
    void cargar();
  }, [cargar]);

  async function crear(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setOcupado(true);
    try {
      await api("/ninos", { zona: true, cuerpo: { nombre, edad: Number(edad), condicion } });
      setNombre("");
      setCondicion("ninguna");
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear el perfil");
    } finally {
      setOcupado(false);
    }
  }

  async function borrar(n: Nino) {
    if (!window.confirm(`¿Eliminar el perfil de ${n.nombre}? Se borrarán también todas sus sesiones y no se puede deshacer.`)) return;
    try {
      await api(`/ninos/${n.id}`, { metodo: "DELETE", zona: true });
      await cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo eliminar");
    }
  }

  return (
    <section>
      <h2>Perfiles</h2>
      {ninos.length === 0 && <p className="suave">Aún no hay perfiles.</p>}
      <ul>
        {ninos.map((n) => (
          <li key={n.id} className="fila" style={{ marginBottom: 8 }}>
            <strong>{n.nombre}</strong> · {n.edad} años
            <button className="boton peligro pequeno" onClick={() => borrar(n)}>Eliminar</button>
          </li>
        ))}
      </ul>

      <form className="tarjeta" onSubmit={crear}>
        <h3>Agregar un perfil</h3>
        <label htmlFor="n-nombre">Nombre</label>
        <input id="n-nombre" type="text" required maxLength={60} value={nombre} onChange={(e) => setNombre(e.target.value)} />
        <label htmlFor="n-edad">Edad</label>
        <input id="n-edad" type="number" min={3} max={18} required value={edad} onChange={(e) => setEdad(e.target.value)} />
        <label htmlFor="n-cond">Condición declarada</label>
        <select id="n-cond" value={condicion} onChange={(e) => setCondicion(e.target.value)}>
          {CONDICIONES.map((c) => (
            <option key={c.valor} value={c.valor}>{c.texto}</option>
          ))}
        </select>
        <p className="suave">
          Se guarda cifrada y solo sirve para elegir los ajustes iniciales (duración, pausas, formato). No es un
          diagnóstico, no se verifica y tu hijo o hija nunca la verá.
        </p>
        {error && <p className="error" role="alert">{error}</p>}
        <button className="boton" type="submit" disabled={ocupado}>Crear perfil</button>
      </form>
    </section>
  );
}
