# NeuroBridge · frontend

React 18 + Vite + TypeScript. La IA corre **en el navegador**: ninguna imagen sale del equipo.

## Arranque

```bash
cd frontend
npm install                 # copia los WASM y descarga el modelo de rostro (postinstall)
# copia public/models/enet_b0_8_best_vgaf.onnx  (ver public/models/LEEME.txt)
cp .env.example .env        # VITE_API_URL=http://localhost:8000
npm run dev                 # http://localhost:5173
```

Backend aparte (`backend/`): `uvicorn app.main:app --reload`.
Usa `localhost` en las dos direcciones (no mezcles con `127.0.0.1`): la cookie de refresco es `SameSite=Strict`.

## Rutas

| Ruta | Quién | Qué |
|---|---|---|
| `/entrar` | todos | iniciar sesión / crear cuenta |
| `/` | sesión iniciada | elegir quién juega |
| `/jugar/:ninoId` | sesión iniciada | elegir actividad |
| `/sesion/:ninoId?h=habilidad` | sesión iniciada | ejercicios, pausas, cámara |
| `/padres` | sesión + PIN | perfiles, **reporte**, **especialistas**, consentimientos, historial |
| `/especialista` | cuenta de especialista | reportes de solo lectura de los niños que cada familia compartió |
| `/laboratorio` | público | prueba la cámara, el modelo y las reglas, sin backend |

## IA en el navegador (`src/ia/`)

| Archivo | Función |
|---|---|
| `vision.ts` | MediaPipe FaceLandmarker: rostro + pose de la cabeza; recorta el rostro a 224×224 |
| `atencion.ts` | atención a partir de la orientación de la cabeza (zona muerta de 12°) |
| `emociones.ts` | preprocesado (ImageNet), softmax, suavizado exponencial, orden de clases |
| `ia.worker.ts` + `clasificador.ts` | ejecutan el ONNX con onnxruntime-web (WASM) en un Web Worker |
| `monitor.ts` | reglas de intervención (calibración de 5 lecturas, 2 lecturas seguidas, 60 s entre avisos); port de `backend/app/modules/atencion/reglas.py` |
| `useVision.ts` | abre la cámara y emite una lectura cada 3 s |

Solo se envían etiquetas y números (`t, rostro, atencion, emocion`); el servidor rechaza cualquier otro campo.
Sin consentimiento de cámara vigente la sesión funciona igual, sin detección.

## Privacidad

- Los tokens viven solo en memoria (no en `localStorage`); el de refresco es una cookie `httpOnly`.
- La condición declarada se escribe una vez al crear el perfil y nunca se muestra en pantallas del niño.
- La zona de padres exige PIN; su token dura 5 minutos y se pierde al recargar.

## Reportes y especialistas

- **Reporte del padre** (zona de padres → Reporte): sesiones, minutos, nota media, aciertos, tendencia, nivel por
  habilidad, resumen de atención (solo con permiso de cámara) y sugerencias redactadas como observaciones, no como
  diagnósticos. Se puede imprimir o guardar como PDF.
- **Especialistas** (zona de padres → Especialistas): la familia da acceso por correo, eligiendo el alcance
  (*resumen* o *completo*) y la duración (máximo 90 días); puede quitarlo cuando quiera y ve el registro de cada consulta.
- **Portal del especialista** (`/especialista`): solo lectura. Nunca ve la condición declarada, las respuestas una por
  una ni las lecturas de cámara en bruto.
- Las cuentas de especialista y de administrador **no se crean desde la pantalla de registro** (que crea cuentas de
  padre): las habilita un administrador. En desarrollo:
  `UPDATE usuarios SET rol='especialista' WHERE email='correo@ejemplo.com';`

## Pruebas y build

```bash
npm test         # 39 pruebas: monitor, atención, preprocesado (mismos valores que Python)
npm run build    # tsc + vite build + service worker (cachea los modelos de IA)
```

## Pendiente

- Cuantizar el modelo a INT8 (16 MB → ~4 MB) y validar que no pierda precisión.
- Evaluar el modelo por edad y con expresiones atípicas antes de abrirlo al público.
- Textos legales (Ley 29733) validados por un abogado.
