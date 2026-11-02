export const site = {
 name: 'Canela River Rooftop', phone: '51941576020', address: 'Calle García Calderón 408-A, esquina con Av. La Marina, Vallecito, Arequipa',
 hours: 'Lunes a sábado · 3:00–9:00 p. m.', instagram: 'https://www.instagram.com/canelarooftop_aqp/', tiktok: 'https://www.tiktok.com/@canelarooftop_aqp',
 map: 'https://www.google.com/maps/search/?api=1&query=Canela+River+Rooftop+Garcia+Calderon+408+Arequipa',
 // Sustituye null por '/assets/anuncio.webp' al recibir el arte final.
 adImage: '/assets/anuncio.webp' as string | null, adAlt: 'Los Jueves con Ilegal, gin de olivas: parrillas, cócteles de autor y amburgesas 2x1', adLink: null as string | null,
};
export const waLink = (message: string) => `https://wa.me/${site.phone}?text=${encodeURIComponent(message)}`;
export const money = (n: number) => new Intl.NumberFormat('es-PE', {style:'currency', currency:'PEN', maximumFractionDigits:2}).format(n);
