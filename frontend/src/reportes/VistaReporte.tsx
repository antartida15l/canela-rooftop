import type { Reporte } from "../api/tipos";
import { AVISO_REPORTE, fechaCorta, fechaHora, nombreHabilidad, porcentaje, textoTendencia } from "./etiquetas";

/** Reporte de un niño. Lo usan el padre y el especialista (solo lectura). */
export default function VistaReporte({ r }: { r: Reporte }) {
  const { resumen } = r;
  return (
    <article data-testid="reporte">
      <h2>
        {r.nino.nombre} · {r.nino.edad} años
      </h2>
      <p className="suave">
        Últimos {r.periodo_dias} días · generado el {fechaCorta(r.generado_en)}
        {r.alcance === "resumen" && " · vista resumida"}
      </p>

      <div className="tarjetas-resumen">
        <div className="dato"><strong data-testid="rep-sesiones">{resumen.sesiones}</strong><span>sesiones</span></div>
        <div className="dato"><strong>{resumen.minutos}</strong><span>minutos</span></div>
        <div className="dato"><strong data-testid="rep-nota">{resumen.nota_media ?? "—"}</strong><span>nota media (0–20)</span></div>
        <div className="dato"><strong>{porcentaje(resumen.aciertos_pct)}</strong><span>aciertos</span></div>
        <div className="dato"><strong>{textoTendencia(resumen.tendencia)}</strong><span>tendencia</span></div>
      </div>

      {r.habilidades.length > 0 && (
        <section>
          <h3>Por habilidad</h3>
          <table>
            <thead><tr><th>Habilidad</th><th>Sesiones</th><th>Nota media</th><th>Nivel</th><th>Dominio</th></tr></thead>
            <tbody>
              {r.habilidades.map((h) => (
                <tr key={h.habilidad}>
                  <td>{nombreHabilidad(h.habilidad)}</td>
                  <td>{h.sesiones}</td>
                  <td>{h.nota_media ?? "—"}</td>
                  <td>{h.nivel} de 3</td>
                  <td>{porcentaje(h.dominio)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {r.atencion && (
        <section>
          <h3>Atención (con permiso de cámara)</h3>
          <p>
            {r.atencion.sesiones_con_camara} {r.atencion.sesiones_con_camara === 1 ? "sesión" : "sesiones"} con cámara · atención
            media {r.atencion.atencion_media ?? "—"} (de 0 a 1) · expresiones de malestar {porcentaje(r.atencion.pct_malestar)} ·{" "}
            {r.atencion.avisos} avisos y {r.atencion.pausas_sugeridas} pausas sugeridas.
          </p>
          <p className="suave">Señales aproximadas: se basan en la orientación de la cabeza y la expresión facial.</p>
        </section>
      )}

      {r.recomendaciones && (
        <section>
          <h3>Observaciones y sugerencias</h3>
          <ul data-testid="recomendaciones">
            {r.recomendaciones.map((x, i) => (
              <li key={i} className={x.nivel === "sugerencia" ? "sugerencia" : "suave"}>{x.texto}</li>
            ))}
          </ul>
        </section>
      )}

      {r.sesiones.length > 0 && (
        <section>
          <h3>Sesiones</h3>
          <table>
            <thead><tr><th>Fecha</th><th>Actividad</th><th>Aciertos</th><th>Nota</th></tr></thead>
            <tbody>
              {r.sesiones.map((s) => (
                <tr key={s.id}>
                  <td>{fechaHora(s.inicio)}</td>
                  <td>{nombreHabilidad(s.habilidad)}</td>
                  <td>{s.correctas}/{s.respondidas}</td>
                  <td>{s.nota ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {!r.recomendaciones && <p className="suave">{AVISO_REPORTE}</p>}
      <p className="no-imprimir">
        <button className="boton secundario pequeno" onClick={() => window.print()}>Imprimir o guardar como PDF</button>
      </p>
    </article>
  );
}
