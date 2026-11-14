Necessito que muntis a Notion el sistema d'organització del nostre equip per a un hackathon de 24 hores. Tens tot el contingut en aquest missatge: no has de buscar res fora ni inventar res.

## Context

Som un equip de quatre estudiants (Subils, Alex, Dídac i David) a la Datathon FME 2026, a Barcelona. Fem el repte de Qualcomm: construir un mentor de matemàtiques que funcioni sencer dins d'una placa Arduino UNO Q, sense internet, fent servir M3Kang, un conjunt de 1.747 problemes de les proves Cangur. Avui és dissabte 14 de novembre de 2026 i l'entrega tanca diumenge 15 a les 12:00. Les demos davant del jurat són diumenge a les 14:00.

El projecte ja està pensat i planificat. El que falta és que l'equip el tingui a Notion de manera que cadascú sàpiga què ha de fer, per a quan, i què vol dir cada tasca.

## Qui ho llegirà i com ha de sonar

Ho llegiran els quatre membres de l'equip, amb pressa i entre tasca i tasca. No tots dominen la part tècnica dels altres: qui fa la web no coneix la placa, i a l'inrevés. Per això:

- Escriu-ho tot en català, amb frases curtes i paraules normals.
- Quan surti un terme tècnic, ha d'estar explicat al glossari o a la mateixa frase.
- Cada tasca diu què s'ha de fer, què vol dir i com sabem que està acabada. Res de frases de motivació ni de farciment.
- Fes servir els textos que et dono tal com estan. Pots arreglar el format perquè es llegeixi bé a Notion, però no reescriguis el contingut, no hi afegeixis tasques ni dades, i no en treguis.

## On crear-ho

Busca al workspace una pàgina del Datathon (per exemple «DataThon FME»). Si existeix, crea-ho tot a dins. Si no, crea una pàgina nova de primer nivell que es digui «Datathon FME 2026 · Mentor Cangur» i fes-la visible per a tot l'equip. Abans de crear res, mira si ja hi ha alguna part feta per no duplicar-la.

## Què has de construir

Una pàgina central amb aquesta estructura, en aquest ordre:

1. Un avís destacat a dalt de tot amb aquest text: «Entrega: diumenge 15/11 a les 12:00 · Codi congelat: diumenge a les 10:00 · Demos: diumenge a les 14:00».
2. Un paràgraf curt: «Construïm un mentor de matemàtiques que viu dins d'una placa Arduino, sense internet. Quan un alumne s'encalla en un problema del Cangur, el mentor no li dona la resposta: li ofereix un problema germà més fàcil perquè hi arribi sol.»
3. El tauler de tasques (la base de dades «Tasques», descrita a sota), incrustat a la pàgina i mostrant la vista «Tauler».
4. Enllaços a les subpàgines, en aquest ordre: Què construïm · Com funciona per dins · Calendari de les 24 hores · Com treballem · Preguntes als mentors · Registre de resultats · Riscos i pla B · Decisions preses · Glossari.

### La base de dades «Tasques»

Propietats:

| Propietat | Tipus | Valors |
|---|---|---|
| Tasca | Títol | — |
| Estat | Estat | Not Started · In progress · Done |
| Responsable | Selecció múltiple | Subils · Alex · Dídac · David · Tots |
| Fase | Selecció | 0 · Arrencada / 1 · Primer tall / 2 · Motor del mentor / 3 · Integració i nit / 4 · Tancament / 5 · Entrega / 6 · Pitch |
| Límit | Data amb hora | Zona horària Europe/Madrid |
| Prioritat | Selecció | P0 · Imprescindible / P1 · Per guanyar / P2 · Si sobra temps |
| Àrea | Selecció | Equip · Placa · Model · Web · Lògica i dades · Contingut · Mesures · Documentació i pitch |
| Fet quan | Text | — |

Dona un color diferent a cada persona i a cada prioritat (P0 vermell, P1 groc, P2 gris).

Dins de cada tasca, al cos de la pàgina, escriu el text de «Què vol dir» sota un títol amb aquest mateix nom. El text de «Fet quan» va a la propietat, perquè es vegi a les targetes.

Vistes:

1. **Tauler** (la principal): tauler agrupat per Estat, amb les tres columnes Not Started, In progress i Done. Cada targeta mostra el títol, el Límit, el Responsable i la Prioritat. Ordenat per Límit, de més proper a més llunyà. Ha de quedar com un tauler de tres columnes clàssic.
2. **Subils**: el mateix tauler, filtrat a les tasques on Responsable conté Subils o Tots.
3. **Alex i Dídac**: el mateix, on Responsable conté Alex, Dídac o Tots.
4. **David**: el mateix, on Responsable conté David o Tots.
5. **Què toca ara**: llista de les tasques que no estan a Done, ordenada per Límit.
6. **Per fases**: taula agrupada per Fase i ordenada per Límit, amb totes les propietats.

Tots els límits de dissabte són del 14/11/2026 i els de diumenge del 15/11/2026. On posa «ds» vol dir dissabte i «dg», diumenge. Si una tasca no indica estat, és Not Started.

### Les tasques

Cada bloc té aquesta forma: número i títol; a sota, fase, responsables, límit, prioritat i àrea; després els dos textos.

**00 · Analitzar el repte i escriure el pla**
Fase 0 · Subils · ds 12:15 · P0 · Equip · Estat: Done
Què vol dir: Hem llegit tot el material del repte, hem mirat les dades i hem decidit què construïm i en quin ordre. El resultat són aquestes pàgines.
Fet quan: El pla és a Notion i tothom el pot llegir.

**01 · Llegir «Què construïm» i confirmar qui fa què**
Fase 0 · Tots · ds 12:45 · P0 · Equip
Què vol dir: Abans de tocar res, tots quatre hem d'entendre el mateix producte i saber què li toca a cadascú. Deu minuts ara estalvien hores de feina duplicada.
Fet quan: Cadascú ha dit en veu alta què farà les properes quatre hores, i ningú no s'ha quedat sense feina ni amb feina repetida.

**02 · Fer les cinc preguntes als mentors de Qualcomm**
Fase 0 · David · ds 13:00 · P0 · Equip
Què vol dir: No hi ha criteris de puntuació publicats. Hi ha cinc coses que no sabem i que canvien el que hem de construir; són a la pàgina «Preguntes als mentors». Com abans les sapiguem, menys feina llençarem.
Fet quan: Les cinc respostes estan escrites a «Preguntes als mentors» i les hem comentat entre tots.

**03 · Crear el repositori de l'equip a GitHub**
Fase 0 · David · ds 13:00 · P0 · Equip
Què vol dir: El repositori és el lloc on viu tot el codi. Entregar-lo públic és obligatori, però el tenim privat fins diumenge. Des del primer moment ha de tenir la regla que impedeix pujar-hi els problemes del Cangur, perquè la seva llicència no ho permet.
Fet quan: Tots quatre hi podem pujar canvis i la regla que bloqueja les dades ja hi és.

**04 · Deixar la placa a punt (passos 0 a 8 de la guia)**
Fase 0 · Alex, Dídac · ds 13:30 · P0 · Placa
Què vol dir: La placa ve buida. Cal actualitzar-la, instal·lar-hi el programa que fa córrer la IA (triga uns 30 minuts a compilar) i baixar els dos models. Sense això no podem provar res de veritat.
Fet quan: La placa contesta els cinc problemes de mostra amb una lletra cadascun, encara que s'equivoqui.

**05 · Crear el projecte web i connectar-lo a un servidor de prova**
Fase 0 · Subils · ds 13:30 · P0 · Web · Estat: In progress
Què vol dir: Muntem l'esquelet de la web i un servidor petit que, de moment, contesta amb dades inventades. Així la web i la placa avancen per separat i s'ajunten més tard.
Fet quan: La web s'obre al portàtil i ensenya un missatge que ve del servidor, no escrit a mà.

**06 · Baixar i preparar els problemes del Cangur**
Fase 0 · Subils · ds 13:30 · P0 · Lògica i dades · Estat: In progress
Què vol dir: M3Kang són 1.747 problemes, cadascun amb la seva imatge i la lletra correcta. Els baixem en català i en anglès. Les cinc opcions només són a la imatge, així que un programa les llegeix (això es diu OCR).
Fet quan: Tenim al portàtil els fitxers de problemes i una imatge per a cada problema.

**07 · Prova crítica: una mini-app a la placa que parli amb la IA i encengui la matriu**
Fase 1 · Alex, Dídac · ds 15:00 · P0 · Placa
Què vol dir: És el risc més gran del projecte. Les apps de la placa viuen dins d'una mena de capsa aïllada, i no està clar que des de dins es pugui parlar amb la IA, que corre a fora. Ho hem de saber aviat: si no funciona, passem al pla B (pàgina «Riscos i pla B»).
Fet quan: Des d'una pàgina de prova premem un botó, la IA contesta i la matriu de LEDs mostra una lletra. O bé hem comprovat que no es pot i hem activat el pla B.

**08 · Mesurar la memòria de la placa amb tot engegat**
Fase 1 · Alex, Dídac · ds 15:30 · P0 · Placa
Què vol dir: La placa té 3,6 GB de memòria per a tot. Si la IA, la web i la matriu no hi caben alhora, es penjarà a mitja demo. Ho mirem ara, no demà.
Fet quan: La memòria lliure amb tot engegat és al «Registre de resultats» i la placa aguanta deu minuts sense penjar-se.

**09 · Mesurar el punt de partida: quants problemes encerta la IA tal com ve**
Fase 1 · Alex, Dídac · ds 16:30 · P0 · Model
Què vol dir: Per poder dir «hem millorat» hem de saber d'on partim. Passem 50 problemes a la IA de la placa i apuntem quants n'encerta i quant triga. Els organitzadors van mesurar un 22,5%.
Fet quan: El percentatge d'encert i els segons per problema són al «Registre de resultats».

**10 · Instal·lar la mateixa IA al portàtil per provar ràpid**
Fase 1 · Alex, Dídac · ds 16:00 · P1 · Model
Què vol dir: A la placa, provar una idea amb 50 problemes són 8 minuts. Al portàtil, amb el mateix model, són segons. Provem les idees al portàtil i anem a la placa només per mesurar temps reals.
Fet quan: La mateixa prova de 50 problemes dona un resultat semblant al portàtil i a la placa.

**11 · Muntar la base de dades dels problemes**
Fase 1 · Subils · ds 15:30 · P0 · Lògica i dades
Què vol dir: Posem tots els problemes en un sol fitxer que viurà a la placa: enunciat, imatge, nivell, resposta correcta i, per a cada problema, quins altres se li assemblen. Aquesta llista de problemes semblants és el cor del producte.
Fet quan: Demanem un problema qualsevol i rebem la seva imatge i cinc problemes que realment s'hi assemblen.

**12 · Pantalla de pràctica**
Fase 1 · Subils · ds 16:30 · P0 · Web
Què vol dir: La pantalla principal. L'alumne veu el problema (la imatge original del Cangur), tria A, B, C, D o E i sap a l'instant si l'ha encertat.
Fet quan: Es poden fer cinc problemes seguits al portàtil sense cap error.

**13 · Matriu de LEDs simulada a la web**
Fase 1 · Subils · ds 16:30 · P1 · Web
Què vol dir: Dibuixem a la web una graella de 8 per 13 punts que imita la matriu de la placa. Serveix per treballar sense tenir la placa, i perquè el jurat vegi a la pantalla el que passa als LEDs.
Fet quan: Quan s'encerta surt un ✓ a la graella, i quan es falla, una ✗.

**14 · Escriure les targetes d'estratègia**
Fase 1 · David · ds 16:30 · P0 · Contingut
Què vol dir: La primera pista que rep un alumne encallat no la fa la IA: és una targeta nostra amb una estratègia («fes un dibuix», «prova amb números petits», «descarta les opcions impossibles»). En calen tres o quatre per a cada un dels cinc temes: geometria, àlgebra, aritmètica, combinatòria i probabilitat, i lògica.
Fet quan: Hi ha entre 15 i 20 targetes curtes, en català, que un alumne de 12 anys entén.

**15 · Obrir el «Registre de resultats»**
Fase 1 · David · ds 14:00 · P0 · Mesures
Què vol dir: Cada número que ensenyem al jurat ha de sortir d'una prova real. Hi ha una taula on tothom apunta què ha mesurat, quan i com. David la vigila i reclama els números que falten.
Fet quan: La taula està en ús i ja hi ha el primer número nostre apuntat.

**16 · Posar la web dins de la placa per primer cop**
Fase 1 · Subils, Alex, Dídac · ds 16:15 · P0 · Placa
Què vol dir: Fins ara la web corria al portàtil. Ara la copiem a la placa i comprovem que la placa la serveix sola, amb el portàtil fent només de pantalla per USB.
Fet quan: Obrim la web des del portàtil connectat per USB i la pàgina ve de la placa.

**17 · Porta 1: comprovació conjunta**
Fase 1 · Tots · ds 16:30 · P0 · Equip
Què vol dir: Primer punt de control. Mirem junts si la peça mínima funciona de punta a punta. Si no funciona, parem tota la resta fins que funcioni.
Fet quan: La web servida per la placa mostra un problema real, diu si la resposta és correcta i encén la matriu de LEDs.

**18 · Triar el següent problema segons com va l'alumne**
Fase 2 · Subils · ds 18:00 · P0 · Lògica i dades
Què vol dir: Si l'alumne encerta, el següent problema és una mica més difícil. Si falla, n'hi posem un de més fàcil del mateix tema. No hi intervé la IA: és una regla sobre els nivells del Cangur, i per això és instantani.
Fet quan: Un alumne de prova que sempre encerta puja de nivell, i un que sempre falla baixa.

**19 · Posar tema a cada problema**
Fase 2 · Subils, David · ds 18:00 · P0 · Lògica i dades
Què vol dir: M3Kang no diu de quin tema és cada problema. L'hi hem de posar nosaltres (cinc temes), perquè el necessitem per triar problemes germans i per a l'anàlisi d'errors que demana el repte. Subils ho automatitza i David en revisa una mostra a mà.
Fet quan: Cada problema té tema, David n'ha revisat 50 i ha apuntat quants estaven bé.

**20 · L'escala de pistes (les quatre que no fan servir la IA)**
Fase 2 · Subils · ds 19:00 · P0 · Lògica i dades
Què vol dir: Quan l'alumne demana ajuda, puja un graó cada vegada: primer una targeta d'estratègia, després un problema germà més fàcil, després li descartem una opció incorrecta i, només si la demana expressament, la solució. Mai saltem directament a la resposta.
Fet quan: En un problema qualsevol es poden demanar les quatre ajudes en ordre i totes tenen sentit.

**21 · Filtre automàtic: aquesta pista revela la resposta?**
Fase 2 · Subils · ds 19:00 · P1 · Lògica i dades
Què vol dir: Tot el que escriu la IA passa per un filtre abans d'arribar a l'alumne. Si la frase conté la resposta correcta, no es mostra. Així podem dir al jurat «zero pistes que revelen la resposta» amb un número al darrere.
Fet quan: El filtre atura una pista de prova que conté la resposta i en deixa passar una que no.

**22 · Provar maneres de demanar pistes a la IA**
Fase 2 · Alex, Dídac · ds 19:30 · P1 · Model
Què vol dir: La IA de la placa és petita i s'equivoca molt en matemàtiques. Per això li donem la resposta correcta i li demanem només una frase d'ajuda que no la reveli. Provem dues o tres maneres de demanar-ho, al portàtil, i ens quedem amb la millor.
Fet quan: Hi ha 30 pistes generades amb la millor manera, a punt perquè David les jutgi.

**23 · Jutjar a mà 30 pistes de la IA**
Fase 2 · David · ds 20:15 · P1 · Mesures
Què vol dir: Llegim 30 pistes i marquem cadascuna com a útil, inútil o enganyosa. Amb aquest recompte decidim a la Porta 2 si les pistes de la IA entren al producte. Una pista enganyosa és pitjor que cap pista.
Fet quan: El recompte d'útils, inútils i enganyoses és al «Registre de resultats».

**24 · «Torna-m'ho a dir d'una altra manera», en directe**
Fase 2 · Subils, Alex, Dídac · ds 20:00 · P1 · Web
Què vol dir: És el moment de la demo en què es veu la IA de la placa treballant. L'alumne prem un botó i la IA reescriu l'enunciat amb paraules més senzilles, i el text va apareixent a la pantalla. Perquè no trigui, li enviem l'enunciat mentre l'alumne encara l'està llegint.
Fet quan: El text comença a aparèixer en pocs segons, i tenim apuntat quant triga amb aquest truc i sense.

**25 · Perfil de l'alumne**
Fase 2 · Subils · ds 20:00 · P1 · Web
Què vol dir: Una pantalla que ensenya en quins temes i nivells l'alumne va bé i en quins s'encalla. Es guarda a la placa i no en surt: és l'argument de privadesa del projecte.
Fet quan: Després de deu problemes, el perfil ensenya els encerts per tema i el nivell actual.

**26 · Fer que la IA deixi de triar gairebé sempre la D**
Fase 2 · Alex, Dídac · ds 18:30 · P1 · Model
Què vol dir: predict.py és el programa que el jurat passarà a un examen secret. Tal com ve, la IA respon D o A gairebé sempre. Mirant quina seguretat té en cada lletra podem corregir aquesta mania.
Fet quan: Hem mesurat l'encert abans i després amb els mateixos 50 problemes i està apuntat.

**27 · Buscar si el problema de l'examen ja és a M3Kang**
Fase 2 · Alex, Dídac · ds 20:00 · P1 · Model
Què vol dir: Si l'examen secret fa servir problemes del Cangur que ja tenim, potser en un altre idioma, no cal que la IA els resolgui: el busquem a la nostra base de dades i ja sabem la resposta. Si no hi és, la IA contesta com sempre. Ho explicarem obertament al jurat.
Fet quan: Amb un problema que tenim, el programa troba la resposta sol; amb un de nou, no s'inventa res.

**28 · Provar un model una mica més gran per als problemes curts**
Fase 2 · Alex, Dídac · ds 20:30 · P2 · Model
Què vol dir: Hi ha un model més gran que encerta més, però és dues vegades i mitja més lent. Potser hi cap en els 60 segons quan el problema és curt. Només si sobra temps.
Fet quan: Hem mesurat encert i temps amb els mateixos 50 problemes i hem decidit si val la pena.

**29 · Dibuixos de la matriu de LEDs**
Fase 2 · Alex, Dídac · ds 20:00 · P0 · Placa
Què vol dir: La matriu és l'única part física que veurà el jurat. Ha d'ensenyar encert (✓), error (✗), el nivell, la ratxa d'encerts i un dibuix de «pensant» mentre la IA treballa.
Fet quan: Cada un dels cinc dibuixos es veu bé a la placa quan toca.

**30 · Una sola ordre per portar-ho tot a la placa**
Fase 2 · Alex, Dídac · ds 18:00 · P1 · Placa
Què vol dir: Copiarem la web i el servidor a la placa moltes vegades. Si són deu passos a mà, algun cop en fallarà un. Ho deixem en una sola ordre.
Fet quan: Qualsevol dels quatre pot actualitzar la placa amb una ordre i funciona.

**31 · Preparar la feina de nit de la placa i provar-la amb 10 problemes**
Fase 2 · Alex, Dídac · ds 20:30 · P1 · Model
Què vol dir: La IA triga uns 20 segons per pista, massa per fer-ho amb l'alumne esperant. La placa les escriurà totes de nit i les desarà. El programa ha de poder continuar on s'havia quedat si es talla.
Fet quan: Ha escrit 10 pistes a la placa, les ha desat, i en tornar-lo a engegar no les repeteix.

**32 · Porta 2: decidim amb dades**
Fase 2 · Tots · ds 20:30 · P0 · Equip
Què vol dir: Segon punt de control. Amb el recompte de David decidim si les pistes de la IA es queden, es redueixen a reescriure l'enunciat, o cauen. A partir d'aquí ja no es canvia la manera de demanar les pistes.
Fet quan: La decisió està escrita a «Decisions preses» amb els números que la justifiquen.

**33 · Assaig complet a la placa, sense internet**
Fase 3 · Tots · ds 21:30 · P0 · Equip
Què vol dir: Fem tota la demo tal com la veurà el jurat: Wi-Fi apagat i el portàtil només com a pantalla. Apuntem tot el que falla.
Fet quan: Hem fet el recorregut sencer i tenim la llista d'errors per arreglar.

**34 · Examen complet de predict.py durant el sopar**
Fase 3 · Alex, Dídac · ds 21:50 · P1 · Model
Què vol dir: Passem els 281 problemes de validació. Triga uns 45 minuts i la placa no pot fer res més mentrestant, per això ho fem mentre sopem.
Fet quan: L'encert total, per idioma i per nivell, està apuntat.

**35 · Engegar la feina de nit de la placa**
Fase 3 · Alex, Dídac · ds 22:00 · P1 · Model
Què vol dir: A les 22:00 com a molt tard la placa comença a escriure pistes i no es toca fins al matí. Cada hora de retard són unes 190 pistes menys.
Fet quan: El programa corre, ha desat les primeres pistes i ningú no toca la placa.

**36 · Polir la web**
Fase 3 · Subils · dg 01:00 · P1 · Web
Què vol dir: Que es vegi bé i s'entengui sense explicacions: disseny, textos en català i en anglès, i missatges clars quan alguna cosa falla o la IA triga.
Fet quan: Algú de fora de l'equip fa tres problemes sense que li expliquem res.

**37 · Pantalla «Sala de màquines»**
Fase 3 · Subils · dg 01:00 · P2 · Web
Què vol dir: Una pantalla per al jurat que ensenya en directe què fa la placa: la velocitat de la IA, la memòria i que no hi ha connexió a internet. Només si sobra temps.
Fet quan: Els números es mouen en directe mentre la IA treballa.

**38 · Esquelet del README i de l'article de Project Hub**
Fase 3 · David · dg 00:30 · P0 · Documentació i pitch
Què vol dir: Són els dos entregables escrits. Si esperem a diumenge al matí, no hi arribarem. Deixem fets els títols, les seccions, les fotos i tot el que ja sabem; diumenge només hi posem els números finals.
Fet quan: Els dos documents tenen totes les seccions i només hi falten els resultats finals.

**39 · Primera versió del guió del pitch**
Fase 3 · David · dg 00:30 · P1 · Documentació i pitch
Què vol dir: Tenim tres minuts: 20 segons de problema, 90 de demo, 40 de números i 30 del que hem après. Escrivim què es diu i qui ho diu.
Fet quan: El guió llegit en veu alta dura menys de tres minuts.

**40 · Aturar la feina de nit i comptar què ha fet la placa**
Fase 4 · Alex, Dídac · dg 07:45 · P1 · Mesures
Què vol dir: Comptem quantes pistes ha escrit, quantes han passat el filtre i quant ha trigat cadascuna. Són números per al pitch: «la placa ha treballat tantes hores i ha escrit tantes pistes».
Fet quan: Els tres números són al «Registre de resultats».

**41 · Examen final de predict.py**
Fase 4 · Alex, Dídac · dg 08:15 · P0 · Model
Què vol dir: L'última mesura amb la versió definitiva. És el número que posarem al README.
Fet quan: L'encert final està apuntat, i predict.py contesta una lletra per a cada problema en menys de 60 segons.

**42 · Carregar les pistes de la nit a la web**
Fase 4 · Subils · dg 08:30 · P1 · Web
Què vol dir: Les pistes que la placa ha escrit de nit s'han de connectar amb l'escala de pistes, perquè surtin a l'instant quan l'alumne les demana.
Fet quan: En un problema de la demo, la pista de la IA apareix a l'instant.

**43 · Taules d'anàlisi d'errors**
Fase 4 · David, Alex, Dídac · dg 09:30 · P0 · Mesures
Què vol dir: El repte demana explicar on falla la IA: per tema, per idioma i per nivell. Fem tres taules i mirem deu errors un per un per entendre'n el perquè.
Fet quan: Les tres taules i els deu errors comentats són al README.

**44 · Últim assaig: només arreglar errors**
Fase 4 · Tots · dg 10:00 · P0 · Equip
Què vol dir: Ja no s'afegeix res de nou. Repetim la demo sense internet i arreglem només el que es trenca.
Fet quan: Dues demos seguides sense cap error.

**45 · Codi congelat**
Fase 4 · Tots · dg 10:00 · P0 · Equip
Què vol dir: A les 10:00 ningú no toca més el codi. Un canvi d'última hora és la manera més habitual de trencar una demo.
Fet quan: L'última versió és a GitHub i a la placa, i és la mateixa.

**46 · Gravar el vídeo de la demo**
Fase 5 · Subils · dg 10:30 · P0 · Documentació i pitch
Què vol dir: Si la demo falla davant del jurat, ensenyem el vídeo. També va al README.
Fet quan: Tenim un vídeo d'un minut i mig amb la demo sencera funcionant a la placa.

**47 · README final, en anglès**
Fase 5 · David · dg 11:15 · P0 · Documentació i pitch
Què vol dir: És la portada del projecte a GitHub: què fa, com està fet, com repetir-ho pas a pas, resultats, errors, què no ha funcionat i qui som.
Fet quan: Té totes les seccions que demanen els organitzadors i tots els números surten del «Registre de resultats».

**48 · Article a Arduino Project Hub**
Fase 5 · David, Alex, Dídac · dg 11:15 · P0 · Documentació i pitch
Què vol dir: El segon entregable obligatori: un tutorial públic a la web d'Arduino amb fotos, l'esquema i els passos per repetir el projecte.
Fet quan: L'article està publicat i l'enllaç funciona.

**49 · Comprovar que no pugem problemes del Cangur i fer públic el repositori**
Fase 5 · Alex, Dídac · dg 11:30 · P0 · Equip
Què vol dir: La llicència de M3Kang només permet l'ús per a recerca: no podem publicar els problemes, les imatges ni la base de dades. Ho comprovem abans d'obrir el repositori.
Fet quan: La comprovació no troba cap fitxer de dades i el repositori és públic.

**50 · Seguir el README des de zero**
Fase 5 · Subils · dg 11:30 · P1 · Documentació i pitch
Què vol dir: Algú que no l'ha escrit baixa el projecte en una carpeta nova i en segueix les instruccions. Cada pas que falla es corregeix.
Fet quan: Les instruccions funcionen sense haver de preguntar res a ningú.

**51 · Enviar els dos enllaços als organitzadors**
Fase 5 · David · dg 11:30 · P0 · Equip
Què vol dir: L'entrega tanca a les 12:00. Enviem a les 11:30 per tenir mitja hora de marge.
Fet quan: Tenim confirmació que han rebut l'enllaç de GitHub i el de Project Hub.

**52 · Triar i provar els problemes de la demo**
Fase 6 · Tots · dg 12:30 · P0 · Documentació i pitch
Què vol dir: No improvisem. Triem dos o tres problemes que queden bé i els provem a la placa el mateix dia.
Fet quan: Cada problema de la demo ha funcionat a la placa avui.

**53 · Tres assajos del pitch amb cronòmetre**
Fase 6 · Tots · dg 13:45 · P0 · Documentació i pitch
Què vol dir: Tres minuts passen molt de pressa. Assagem amb el rellotge a la vista i amb la placa, no amb diapositives soles.
Fet quan: Tres assajos seguits per sota dels tres minuts.

### Subpàgina «Què construïm»

**El problema.** Les matemàtiques baixen a Catalunya a les proves PISA. Una IA que fa els deures no ajuda a aprendre. I les dades dels alumnes no haurien de sortir de l'aula.

**El que fem.** Un mentor de matemàtiques que viu dins d'una placa Arduino, sense internet. L'alumne practica amb problemes de les proves Cangur. Quan s'encalla, el mentor no li dona la resposta: l'ajuda a arribar-hi.

**La idea que ens fa diferents: l'escala del Cangur.** Tenim 1.747 problemes del Cangur, ordenats en 8 nivells (de 5è de primària a 2n de batxillerat). Per a cada problema sabem quins altres se li assemblen. Quan un alumne s'encalla, li oferim un «problema germà»: semblant, però més fàcil. Quan el resol, torna a l'original amb una idea nova. El mentor és el conjunt de problemes, no la IA.

**Per què no deixem que la IA expliqui.** La IA que hi cap a la placa és molt petita. Tal com ve, encerta el 22,5% dels problemes; respondre sempre la lletra D n'encerta el 25%. Una IA així no pot explicar matemàtiques sense ensenyar errors. Per això només li demanem coses petites que sí que sap fer, i comprovem amb un filtre tot el que escriu.

**Què pot fer l'alumne.**

- Veure un problema del Cangur i respondre A, B, C, D o E. La matriu de LEDs de la placa li diu si ha encertat.
- Rebre el següent problema adaptat: més difícil si encerta, més fàcil si falla.
- Demanar ajuda en quatre graons: una estratègia, un problema germà més fàcil, descartar una opció i, només si ho demana, la solució.
- Demanar a la IA que li torni a dir l'enunciat amb paraules més senzilles.
- Veure el seu perfil: en quins temes va bé i en quins s'encalla.

**Què veurà el jurat en 3 minuts.** Amb el Wi-Fi apagat, un alumne falla un problema, la matriu marca ✗, demana ajuda, rep un problema germà, la IA de la placa li reformula l'enunciat en directe, encerta, la matriu marca ✓ i el perfil s'actualitza. Després, els nostres números.

**Les dues coses que ens puntuen.**

- *Teach* (ensenyar): el mentor, que és el nostre producte.
- *Reason* (raonar): un programa, predict.py, que el jurat passa a un examen secret de problemes. Tots els equips el tenen. El nostre objectiu és superar el 25%.

### Subpàgina «Com funciona per dins»

**La placa té dos cervells.**

- Un ordinador petit amb Linux. Aquí hi viuen la IA, la base de dades dels problemes i la web.
- Un microcontrolador, que és un xip senzill. Només controla la matriu de LEDs.

**El portàtil només fa de pantalla.** Es connecta a la placa per un cable USB i obre la web que la placa li serveix. No hi ha internet enlloc.

**Què passa quan l'alumne respon.**

1. La web envia la lletra triada a la placa.
2. La placa mira a la base de dades si és la correcta.
3. La placa encén un ✓ o una ✗ a la matriu de LEDs.
4. La placa tria el següent problema i l'envia a la web.

Tot això passa en mil·lèsimes de segon, perquè no hi intervé la IA.

**Quan sí que intervé la IA.** Només en dues coses: reescriure l'enunciat amb paraules senzilles (en directe) i escriure una frase de pista per a cada problema (de nit, per endavant). La IA escriu unes 5 paraules per segon, i abans ha de llegir el problema, que li costa entre 7 i 12 segons. Per això tot el que pot es fa sense ella.

**On es desenvolupa.** Gairebé tot es prepara al portàtil, on provar una idea costa segons. La placa es fa servir per a allò que només ella pot dir: quant triga de veritat, si hi cap a la memòria, i la demo.

**Qui fa cada peça.**

| Peça | Què és | Qui |
|---|---|---|
| La web | Les pantalles que veu l'alumne | Subils |
| La lògica i les dades | Quin problema toca, les pistes, el perfil, la base de dades | Subils |
| La placa | Que tot hi corri, la matriu de LEDs, la memòria | Alex i Dídac |
| La IA | Fer-la anar, les pistes, predict.py | Alex i Dídac |
| El contingut i les mesures | Targetes d'estratègia, jutjar pistes, registre de números | David |
| La documentació i el pitch | README, Project Hub, guió | David |

### Subpàgina «Calendari de les 24 hores»

| Fase | Quan | Què ha de quedar fet |
|---|---|---|
| 0 · Arrencada | dissabte 12:15 → 13:30 | Preguntes fetes als mentors, repositori creat, placa a punt, web creada |
| 1 · Primer tall | dissabte 13:30 → 16:30 | Una sola cosa de punta a punta: la placa serveix la web, mostra un problema, el corregeix i encén la matriu |
| 2 · Motor del mentor | dissabte 16:30 → 20:30 | El següent problema adaptat, l'escala de pistes, la IA en directe, predict.py millorat |
| 3 · Integració i nit | dissabte 20:30 → diumenge 01:00 | Assaig sense internet; a les 22:00 la placa comença a escriure pistes sola |
| Nit | diumenge 01:00 → 07:30 | La placa treballa. L'equip dorm |
| 4 · Tancament | diumenge 07:30 → 10:00 | Números finals, últim assaig, codi congelat a les 10:00 |
| 5 · Entrega | diumenge 10:00 → 12:00 | README, Project Hub, vídeo. Enllaços enviats a les 11:30 |
| 6 · Pitch | diumenge 12:00 → 14:00 | Problemes de la demo triats i tres assajos amb cronòmetre |

**Els dos punts de control.**

- **Porta 1, dissabte 16:30.** La web servida per la placa mostra un problema real, el corregeix i encén la matriu. Si no funciona, parem tota la resta fins que funcioni.
- **Porta 2, dissabte 20:30.** Decidim amb números si les pistes de la IA entren al producte. A partir d'aquí no es canvia com es demanen.

**L'agenda de la placa.** Només n'hi ha una i la IA atén una sola petició alhora. És el recurs més escàs de l'equip.

| Franja | La placa fa |
|---|---|
| ds 12:15 – 13:30 | Posada a punt |
| ds 13:30 – 16:30 | Prova crítica i punt de partida |
| ds 16:30 – 20:30 | Proves curtes, quan algú les demana |
| ds 20:30 – 21:00 | Assaig complet |
| ds 21:00 – 21:50 | Examen complet de predict.py |
| ds 22:00 – dg 07:30 | Feina de nit: escriure pistes |
| dg 07:30 – 08:15 | Examen final de predict.py |
| dg 08:15 – 14:00 | Assajos i demo |

**Si anem tard, es talla en aquest ordre:** primer tot el P2; després el perfil detallat; després les pistes de la IA (queda la reformulació); després la reformulació en directe. El P0 no es talla.

### Subpàgina «Com treballem»

**Les regles que no es trenquen.**

1. Tot funciona dins de la placa i sense internet. Res al núvol.
2. Els problemes del Cangur no es pugen mai a GitHub. La llicència no ho permet.
3. predict.py no es trenca: una lletra per problema, en menys de 60 segons.
4. La IA no explica matemàtiques ni dona solucions. Tot el que escriu passa pel filtre.
5. Cada número que diem l'hem mesurat i és al «Registre de resultats».
6. Diumenge a les 10:00 no es toca més codi.

**Com fem servir el tauler.**

- Cadascú mou les seves targetes. Quan comences una tasca, a In progress. Quan es compleix el «Fet quan», a Done. No abans.
- Dues tasques In progress per persona com a màxim.
- Si portes 20 minuts encallat, digues-ho en veu alta. No esperis.
- Si surt una tasca nova, qualsevol l'afegeix amb responsable, límit i «Fet quan».
- A cada Porta ens aturem deu minuts tots quatre, drets, davant del tauler.

**Qui fa què.**

- **Subils:** la web, la base de dades i tota la lògica del mentor.
- **Alex i Dídac:** la placa, la IA i predict.py. Es reparteixen les tasques entre ells.
- **David:** el contingut, les mesures, la documentació i el pitch. És una proposta: confirmeu-la a la tasca 01.

### Subpàgina «Preguntes als mentors»

Per fer als mentors de Qualcomm com abans millor. Sota cada pregunta, deixa un espai amb el text «Resposta:» perquè l'equip l'ompli.

1. **L'examen secret.** Els problemes porten les cinc opcions escrites? Porten imatge? En quins idiomes són? Surten de M3Kang o són problemes nous? *Per què importa: decideix com preparem predict.py.*
2. **On s'executa predict.py.** A la nostra placa o en una vostra, baixant el nostre repositori? *Per què importa: si és a la seva, el nostre repositori ha de poder-ho muntar tot sol.*
3. **Quant pesa cada part.** Quant compta el mentor (Teach) i quant l'examen (Reason)? Cal fer les dues coses? *Per què importa: decideix on posem les hores.*
4. **Preparar contingut fora de la placa.** Podem generar pistes amb un model gran al portàtil i carregar-les a la placa, o tot el text ha de sortir de la IA de la placa? *Per què importa: de moment suposem que ha de sortir de la placa.*
5. **La demo.** Val ensenyar la web al nostre portàtil connectat per USB a la placa? *Per què importa: és com la tenim pensada.*

### Subpàgina «Registre de resultats»

Crea-hi una base de dades amb aquestes propietats: Mesura (títol), Valor (text), Com s'ha mesurat (text), Qui (selecció: Subils, Alex, Dídac, David, Organitzadors), On (selecció: Placa, Portàtil), Quan (data amb hora). Vista de taula ordenada per Quan.

A sobre de la taula, aquest text: «Cada número que ensenyem al jurat ha de ser aquí. Si no hi és, no el diem.»

Omple-la amb aquestes files de referència, totes amb Qui = Organitzadors i On = Placa:

| Mesura | Valor | Com s'ha mesurat |
|---|---|---|
| Encert de la IA tal com ve | 22,5% (9 de 40) | 40 problemes en anglès, només text |
| Encert de respondre sempre D | 25% | Sobre el conjunt d'entrenament |
| Temps per respondre una lletra | 8,7 s de mitjana | Els mateixos 40 problemes |
| Velocitat de lectura de la IA | uns 11 tokens per segon | Guia dels organitzadors |
| Velocitat d'escriptura de la IA | uns 5 o 6 tokens per segon | Guia dels organitzadors |
| Memòria útil de la placa | 3,6 GB | Guia dels organitzadors |

### Subpàgina «Riscos i pla B»

| Risc | Què fem |
|---|---|
| L'app de la placa no pot parlar amb la IA | Es prova a la tasca 07. Pla B: el mentor corre com un programa normal a la placa i l'app només controla la matriu |
| No hi cap tot a la memòria | Es mesura a la tasca 08. Pla B: fer servir l'app d'Arduino només per a la matriu |
| Les pistes de la IA són dolentes o en mal català | Es decideix a la Porta 2 amb el recompte de David. El producte funciona sense elles |
| La feina de nit es talla | El programa continua on s'havia quedat. Es prova amb 10 problemes abans de dormir |
| La demo falla davant del jurat | Vídeo gravat, assajos fets i problemes triats i provats el mateix dia |
| Pugem problemes del Cangur a GitHub | Regla de bloqueig des del primer minut i comprovació abans de fer públic el repositori |
| El Wi-Fi de la UPC no funciona a la placa (eduroam no hi va) | Fem servir la xarxa de l'esdeveniment i treballem per USB |
| No queda temps per documentar | El registre s'omple des de dissabte, l'esquelet es fa a la nit i el codi es congela a les 10:00 |

### Subpàgina «Decisions preses»

| Decisió | Per què |
|---|---|
| La web la serveix la placa; no fem servir Vercel | El repte exigeix que tot corri a la placa, i la demo és sense internet |
| Les dades es guarden a la placa (SQLite); no fem servir Supabase | Les dades de l'alumne no poden sortir del dispositiu |
| Ensenyem el problema amb la imatge original del Cangur | Així serveixen els 1.747 problemes, també els que tenen figures |
| La IA no resol ni explica | Encerta el 22,5%: ensenyaria errors |
| Tot el text que veu l'alumne i que ha escrit una IA surt de la IA de la placa | És el que demana el repte |
| Les pistes s'escriuen de nit, per endavant | En directe trigarien uns 20 segons cadascuna |
| Es prepara al portàtil i es mesura a la placa | Provar 50 problemes a la placa són 8 minuts |
| Català primer | El repte parla de Catalunya i de PISA |

Deixa a sota un títol «Decisions noves» perquè l'equip n'hi afegeixi.

### Subpàgina «Glossari»

| Paraula | Què vol dir |
|---|---|
| Placa (Arduino UNO Q) | L'ordinador petit on ha de córrer tot. Té 3,6 GB de memòria útil |
| Matriu de LEDs | La graella de 8 per 13 llumets que porta la placa. És l'única sortida física que tenim |
| Model, o IA | El programa que llegeix i escriu text. El nostre es diu Qwen3.5 0.8B i és molt petit |
| Token | Un tros de paraula. La IA llegeix uns 11 tokens per segon i n'escriu uns 5 |
| M3Kang | El conjunt de 1.747 problemes de les proves Cangur que ens dona Qualcomm, traduïts a molts idiomes |
| Nivell | La dificultat d'un problema del Cangur, de 0 (5è de primària) a 7 (2n de batxillerat) |
| Problema germà | Un problema semblant a un altre però més fàcil. És la nostra manera d'ajudar |
| Embedding | Una manera de convertir un text en números perquè l'ordinador trobi textos que s'assemblen. Amb això sabem quins problemes són germans |
| OCR | Un programa que llegeix el text que hi ha dins d'una imatge. El fem servir per llegir les opcions A–E |
| predict.py | El programa que el jurat passa a un examen secret. Per a cada problema ha de contestar una lletra en menys de 60 segons |
| Punt de partida (baseline) | El resultat abans de millorar res: 22,5% d'encert |
| Examen secret | Els problemes amb què el jurat mesurarà predict.py. No sabem quins són |
| App Lab | El programa d'Arduino per fer apps per a la placa. Les apps hi corren dins d'una capsa aïllada |
| Base de dades (SQLite) | Un fitxer on es guarden els problemes, les pistes i el progrés dels alumnes. Viu a la placa |
| Feina de nit | La placa escrivint pistes sola mentre dormim |
| Filtre | El control automàtic que atura qualsevol frase de la IA que reveli la resposta |
| Teach i Reason | Les dues maneres de puntuar del repte: ensenyar (el mentor) i raonar (l'examen de predict.py) |
| README | La pàgina principal del projecte a GitHub. És un dels entregables |
| Arduino Project Hub | La web d'Arduino on hem de publicar un tutorial del projecte. És l'altre entregable |
| Porta | Un punt de control on ens aturem tots quatre a comprovar que el pla es compleix |

## Quan acabis

Comprova que hi ha 54 tasques (de la 00 a la 53), que cadascuna té responsable, fase, límit, prioritat, àrea i «Fet quan», i que la 00 està a Done i la 05 i la 06 a In progress. Comprova que el tauler mostra les tres columnes.

Després digue'm: l'enllaç de la pàgina central, quantes tasques has creat, i qualsevol cosa que no hagis pogut fer tal com la demano (per exemple, una vista o una propietat que l'eina no t'ha deixat crear). Si alguna cosa no ha sortit, digues-ho clarament en lloc de substituir-la per una altra.
