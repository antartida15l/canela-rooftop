# Canela River Rooftop

Demostración académica desarrollada con React, Vite y TypeScript. No es el sitio oficial del establecimiento.

## Versión 2.0 — experiencia ampliada

- Introducción de pantalla completa, letras escalonadas, horizonte de luz y transición de salida. Sigue siendo independiente del anuncio; aparece después de cerrarlo. Se puede omitir o repetir desde el pie de página.
- Animaciones de entrada por desplazamiento, cambios de categoría, tarjetas, favoritos, botones y galería. Se respeta la preferencia de movimiento reducido del dispositivo.
- Texto ampliado: «Una terraza con encanto y personalidad», Vallecito, coctelería y el ritual de compartir.
- Tres ambientes interactivos: luz de tarde, hora dorada y bajo las luces. La escena del río es una interpretación artística, no una foto del local.
- Instagram y TikTok visibles en portada, navegación, sección Redes y pie. En celular la navegación conserva el enlace Redes.
- Galería navegable con botones y flechas del teclado.

## Abrir esta entrega

Esta edición contiene el proyecto completo y una compilación estándar. No incluye el HTML autónomo con código e imágenes incrustados que acompañaba a la primera entrega. Todas las funciones del sitio están en el proyecto React.

Descomprime el archivo, abre la carpeta `canela-rooftop` en VS Code y utiliza los comandos siguientes. Si tienes una versión anterior, usa una carpeta nueva para evitar mezclar archivos.

## Ejecutar y editar

Necesitas Node.js 22.12+ o una versión LTS más reciente compatible con Vite 7.

```bash
cd canela-rooftop
npm ci
npm run dev
```

Abre la dirección que muestre Vite, normalmente http://localhost:5173. Edita el proyecto en VS Code. No necesitas XAMPP, MySQL, claves API ni variables de entorno.

Para compilar y revisar el resultado:

```bash
npm run build
npm run preview
```

## Publicar en Vercel

1. Crea un repositorio en GitHub y sube el contenido de `canela-rooftop`, sin `node_modules`. El `.gitignore` ya excluye dependencias y archivos locales.
2. En Vercel, selecciona **Add New → Project** e importa el repositorio.
3. Si subiste la carpeta contenedora, configura **Root Directory** como `canela-rooftop`; si subiste su contenido, conserva la raíz.
4. Framework: **Vite**. Build: `npm run build`. Output: `dist`. Install: `npm ci`.
5. Pulsa **Deploy**. Vercel asignará el enlace público. No se ha realizado un despliegue desde esta entrega.

El proyecto se plantea como demostración académica personal. Si se transforma en web comercial del negocio, revisa las condiciones de alojamiento aplicables. La disponibilidad del plan gratuito la determina Vercel.

## Cambiar el anuncio

1. Guarda el arte recibido como `public/assets/anuncio.webp` (también admite JPG o PNG).
2. Abre `src/config.ts` y cambia:

```ts
adImage: '/assets/anuncio.webp' as string | null,
adAlt: 'Descripción de la campaña de Canela',
adLink: null as string | null,
```

Si el anuncio lleva a una página, escribe su URL en `adLink`. La imagen se muestra completa, con la X siempre visible. El contenedor se adapta a distintos tamaños y si la imagen falla vuelve al diseño provisional.

El anuncio aparece al cargar la web. Al cerrarlo comienza la introducción del logo, salvo que el dispositivo solicite reducir movimiento. No reaparece al navegar por secciones. El pie de página tiene un botón para mostrarlo otra vez. `?sinAnuncio=1` permite revisar directamente la página; `?anuncio=1` mantiene el comportamiento normal de mostrarlo al entrar.

## Contenido y archivos

| Archivo | Qué modificar |
| --- | --- |
| `src/config.ts` | WhatsApp, dirección, horario, redes y anuncio |
| `src/menu.ts` | Las 60 opciones: nombres, ingredientes, precios y presentaciones |
| `src/main.tsx` | Secciones, modales, reservas, galería y favoritos |
| `src/styles.css` | Estilos base y tamaños adaptables |
| `src/impact.css` | Introducción de pantalla completa, capítulos y animaciones |
| `src/experience.tsx` | Ambientes interactivos, textos y redes sociales |
| `src/motion.ts` | Revelado por desplazamiento y progreso de lectura |
| `public/assets/` | Imágenes, logo y favicon |
| `public/cartas/` | Los dos PDF originales |
| `vercel.json` | Configuración del despliegue |
| `dist/` | Compilación lista para servir mediante HTTP |

### Sustituir ilustraciones por fotos reales

Todos los productos tienen una imagen ilustrativa. Para reducir el peso, se utilizan dos hojas de imágenes: `food.webp` y `drinks.webp`. El índice `image` va de 0 a 15, de izquierda a derecha y de arriba abajo. Las bebidas pueden compartir una ilustración de categoría; no es una fotografía exacta de cada receta.

Para asignar una foto individual a un producto, guárdala en `public/assets/` y, al final de `menu.ts`, antes de exportar `menu`, añade por ejemplo:

```ts
const kallpa = items.find(p => p.name === 'Kallpa');
if (kallpa) kallpa.imageSrc = '/assets/kallpa-real.webp';
```

El componente ya admite imágenes individuales. Ajusta los avisos y textos alternativos cuando reemplaces las ilustraciones por fotos verificadas; no retires avisos globales si aún hay imágenes generadas.

## Comportamiento

- 16 comidas y 44 bebidas se presentan en la web. Los PDF son una opción adicional.
- Búsqueda por nombre/ingredientes, sin distinguir tildes, categoría, filtro sin alcohol y orden por precio.
- Detalles con ingredientes y precios; infusiones por taza/cántaro.
- Favoritos guardados en este navegador; cantidades de 1 a 20 y total referencial. No son pedidos confirmados.
- La solicitud de reserva valida fechas pasadas, domingos y horarios publicados. Luego genera un enlace a WhatsApp; solo el visitante decide enviarlo.
- No se envía ni guarda información del formulario en un servidor.
- Galería ampliable y navegable, mapa externo, vínculos a Instagram/TikTok y acceso directo a WhatsApp.
- Anuncio con bloqueo del fondo, navegación por teclado, Escape, X visible y gestión de foco.
- Respeto de `prefers-reduced-motion`. No hay audio automático ni video descargado: la presentación se anima con CSS.

## Fuentes y límites

La carta y su autoría provienen de los PDF facilitados por el usuario, atribuidos a @dante.vargasx. Dirección, horario y contacto provienen de los datos compartidos por el usuario. Los precios y el horario requieren confirmación del establecimiento antes de un uso real.

Se conserva el logo original para la identidad principal. `logo-hd.png` es una reconstrucción generada con IA que se entrega como recurso alternativo, no como vector oficial.

`hero.webp`, `food.webp` y `drinks.webp` se generaron con IA para esta demostración. No representan fotos verificadas de platos o del local. El sitio lo indica expresamente. No se incorporaron fotos ni videos descargados de Instagram, TikTok o Rappi.

La ficha pública de Rappi encontrada durante la investigación fue https://www.rappi.com.pe/restaurantes/81382-canela-river-roof-top. Sus precios/horarios diferían de los materiales proporcionados y no se usaron para sustituirlos.

## Verificación realizada

- Compilación TypeScript y Vite de producción completada.
- Comprobación de 60 productos, IDs únicos, precios y recursos locales.
- Pruebas de interacción en DOM simulado: anuncio e introducción, búsqueda, favoritos persistentes, cantidades, variantes y total, enlaces WhatsApp, galería, formulario y rechazo de fechas pasadas.
- No se dispuso de navegador visual para validar el aspecto final en dispositivos reales. Antes de exponer, ejecuta npm run dev y comprueba el diseño en tu computadora y celular.

No incluye pagos, disponibilidad de mesas en tiempo real, panel administrativo ni base de datos; todas las funciones acordadas se resuelven en el cliente o mediante un enlace voluntario a WhatsApp.
