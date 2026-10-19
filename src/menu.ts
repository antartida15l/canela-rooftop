export type Product = {id:string; name:string; category:string; type:'Comida'|'Bebidas'; price:number; ingredients:string; image:number; imageSrc?:string; alcohol:boolean; variants?:{name:string;price:number}[]};
const items: Product[] = [];
function add(type:Product['type'], category:string, rows:[string,number,string,number,boolean?][]) {
 for (const [name,price,ingredients,image,alcohol] of rows) items.push({id:`p${items.length+1}`, name, price, ingredients, image, category, type, alcohol:alcohol??false});
}
add('Comida','Para compartir',[
 ['Alitas Box 6',25,'6 unidades de alitas, papas nativas y cremas.',0],
 ['Alitas Box 8',27,'8 unidades de alitas, papas nativas y cremas.',1],
 ['Alitas Box 10',30,'10 unidades de alitas, papas nativas y cremas.',2],
 ['Salchi-Alitas Box 6',27,'6 alitas, papas nativas, salchicha de la casa y cremas.',3],
 ['Salchi-Alitas Box 8',29,'8 alitas, papas nativas, salchicha de la casa y cremas.',4],
 ['Salchi-Alitas Box 10',34,'10 alitas, papas nativas, salchicha de la casa y cremas.',5],
 ['Salchipapa clásica',21,'Salchicha de la casa, papas nativas y cremas.',6],
 ['Salchipollo',23,'Tenders de pollo, salchicha de la casa, papas nativas y crema.',7],
]);
add('Comida','Para conversar',[
 ['Hamburguesa de la casa',25,'Hamburguesa artesanal, lechuga, tomate, chimichurri, pepinillos y pan brioche.',8],
 ['Sándwich de pollo',20,'Pollo deshilachado, lechuga, tomate y pan brioche.',9],
 ['Choripán',20,'Chorizo, lechuga, tomate, chimichurri y pepinillos.',10],
 ['Quesadilla de pollo',20,'Tortilla de maíz, queso y pollo deshilachado.',11],
 ['Quesadilla con queso',20,'Tortilla de maíz y queso gratinado.',12],
 ['Tequeños',20,'Wantán, queso y palta.',13],
 ['Panini de jamón',20,'Panini, jamón, queso y mayonesa. Acompañado de chips de papas.',14],
 ['Panini de pollo',20,'Panini, pollo deshilachado, mayonesa y palta. Acompañado de chips de papas.',15],
]);
add('Bebidas','De autor',[
 ['Kallpa',30,'Sinsonte, Gran Kafa, pisco Hacienda del Abuelo, mix de piña golden y fresa, syrup de rocoto y ají limo, bitter de limón sidra, aceite de brassica y ají.',0,true],
 ['Kausay',30,'Aperol, pisco Hacienda del Abuelo, gin Anastasia frutos rojos, zumos de maracuyá y naranja, horchata de coco y agua de azahar.',1,true],
 ['Nuna',30,'Ron Botrán 5 años, vermouth rosso, zumo de naranja, reducción de té Huyro, horchata de almendras y café, fassinola y zumo de toronja.',2,true],
 ['Sunqu',30,'Gin Anastasia Dry, Sitera Amaro, Gran Kafa, zumo de naranja, mix de frutos rojos, fassinola y aquafaba.',3,true],
]);
add('Bebidas','Clásicos',[
 ['Mojito clásico',20,'Flor de Caña 5 años blanco, jarabe simple, zumo de limón y hierbabuena.',4,true],
 ['Mojito afrutado',22,'Sabores disponibles: coco, frutos rojos, maracuyá o fassinola.',5,true],
 ['Mojito Smash afrutado',24,'Mojito batido y doble colado, de sabores más intensos. Consulta los sabores disponibles.',5,true],
 ['Mojito Smash clásico',22,'Mojito batido y doble colado, de sabores más intensos.',4,true],
 ['Piña colada',24,'Ron Flor de Caña 5 años, horchata de coco y mix de piña golden.',6,true],
 ['Botrán colado',25,'Ron Botrán 5 años rubio, horchata de coco y mix de piña golden.',6,true],
 ['Pisco Punch',25,'Pisco Italia, mix de piña golden, zumo de limón y jarabe simple.',0,true],
 ['Botrán Punch',25,'Ron Botrán 5 años rubio, mix de piña golden, zumo de limón y jarabe simple.',0,true],
 ['Pisco Sour',26,'Pisco Italia, zumo de limón, jarabe simple y bitter Ricantí. Clásico o maracuyá.',7,true],
]);
add('Bebidas','Tiki',[
 ['Mai Tai',30,'Mix de rones, triple sec, mix de piña, zumo de naranja y horchata de almendra.',8,true],
 ['Zombie',30,'Mix de rones, pisco, zumos de naranja, toronja y maracuyá, y horchata.',8,true],
 ['Jungle Bird',30,'Mix de rones, Campari, mix de piña golden y fassinola.',8,true],
]);
add('Bebidas','Tequila',[
 ['Tequila Sunrise',25,'Tequila rubio Jimador, zumo de naranja y granadina.',9,true],
 ['Paloma',25,'Tequila rubio Jimador, zumo de toronja, jarabe de agave y soda de toronja.',10,true],
]);
add('Bebidas','Highball',[
 ['Chilcano',21,'Pisco Italia, ginger ale y zumo de limón.',11,true],
 ['Cuba Libre 5 años',23,'Ron Botrán 5 años rubio con Coca-Cola o ginger ale.',2,true],
 ['Cuba Libre 12 años',29,'Flor de Caña 12 años, ginger ale y twist de naranja.',2,true],
]);
add('Bebidas','Boutique',[
 ['Negroni',27,'Gin Dry Anastasia, vermouth rosso y Campari.',12,true],
 ['Capitán',27,'Pisco Italia, vermouth rosso, bitter y twist de naranja.',12,true],
 ['Manhattan',27,'Whiskey, vermouth rosso, bitter y twist de naranja.',12,true],
 ['Sinsoni',27,'Sinsonte, vermouth Miró y gin Anastasia Dry.',12,true],
]);
add('Bebidas','Aperitivos',[
 ['Aperol Spritz',25,'Aperol, prosecco Cinzano, soda y media luna de naranja.',13,true],
 ['Kafa Tonic',26,'Licor de café peruano, agua tónica y twist de toronja.',2,true],
 ['Anastasia Tonic',26,'Gin Dry o gin de frutos rojos, agua tónica y twist.',11,true],
 ['Sangría Spritz',26,'Blend de vinos, pisco, zumo de naranja, prosecco, soda y frutas.',14,true],
]);
add('Bebidas','Vinos',[
 ['Tinto de verano',25,'Blend de vinos, pisco, zumo de naranja, soda de naranja y frutas.',14,true],
 ['Vino caliente',22,'Blend de vinos, pisco, zumo de naranja y jarabe simple.',15,true],
 ['Vino caliente especiado',22,'Blend de vinos, pisco, zumo de naranja, jarabe simple y especias.',15,true],
]);
add('Bebidas','Sin alcohol',[
 ['Ice Tea',21,'Reducción de té, zumo de naranja, jarabe simple y hielo.',11],
 ['Ice Coffee',21,'Reducción de café, zumo de naranja, jarabe simple y hielo.',2],
 ['Piña colada virgen',22,'Mix de piña golden, horchata de coco y zumo de limón.',6],
]);
add('Bebidas','Bombers',[
 ['Atomic Bomb',23,'Tequila, Jägermeister y Red Bull clásico.',2,true],
 ['Sinsonte Bomb',23,'Sinsonte, gin Anastasia Dry y nectarina.',0,true],
]);
add('Bebidas','Infusiones',[
 ['Miss Canela',10,'Piña, cedrón, menta, canela, syrup simple y zumo de limón.',15],
 ['Relajante',10,'Muña, hierbabuena, botánicos, naranja y especias.',15],
 ['Calmante',10,'Té Huyro, cedrón, manzanilla, botánicos y twist.',15],
 ['Reducción de té o café',10,'Reducción, canela, anís estrella y naranja.',15],
]);
add('Bebidas','Infusiones con alcohol',[
 ['Té piteado',23,'Pisco o Anís Najar, té Huyro, botánicos y naranja.',15,true],
 ['Kafa Hot',23,'Gran Kafa, café, botánicos, naranja y horchata.',15,true],
 ['Irish Coffee reversionado',23,'Whisky, café, botánicos, naranja y horchata.',15,true],
]);
for (const p of items) {
 if(p.category==='Infusiones') p.variants=[{name:'Taza',price:10},{name:'Cántaro',price:20}];
 if(p.category==='Infusiones con alcohol') p.variants=[{name:'Taza',price:23},{name:'Cántaro',price:35}];
}
export const menu = items;
