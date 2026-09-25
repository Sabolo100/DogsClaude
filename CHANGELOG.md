# Változásnapló – Pacsi by DarwinAI

A verziószám a `VERSION` fájlban van, szemantikus verziózással (FŐ.MELLÉK.JAVÍTÁS). A build mellé rövid build-azonosítót is számol a forrás tartalmából. Mindkettő látszik az appban:
- **Mobilon:** a Tippek panel névjegykártyáján.
- **Asztalon:** a bal oldali panel alján.

## 1.5.0 – 2026-09-25
- **Új: nyitó ablak az első látogatáskor.** Mielőtt a szűrők és a felhő elé kerülsz, egy nagy, látványos ablak mondja el a lényeget: „Válaszd ki a neked való kutyafajtát, hogy mindketten azt kapjátok, amire vágytok.”
  - A képernyő kb. felét takarja, körülötte látszik az app (a felhő közben kipattan mögötte).
  - Nagy „pacsi” illusztráció óriás buborékban: az ember keze és a kabala mancsa összeér. Köré rajzolódik a korall illeszkedési gyűrű, lebegő fajtabuborékok veszik körül, és szívecskék pattannak ki.
  - A „Kezdjük!” gomb (vagy Esc) zárja be, és utána indul a bemutató.
- **A bemutató tippjei jól látszanak:**
  - A kiemelt rész (felhő, szűrők, kvíz) reflektorfényt és lüktető korall gyűrűt kap, a képernyő többi része elsötétül. A kattintás átmegy rajta.
  - A tippbuborék korall keretet kapott, és a Pacsi kabala „mondja”. Fölötte „Tipp 1/3” jelzés, minden lépésnél újra beugrik.
  - Magától továbblép, ha megcsinálod, amit kér (buborékot nyitsz, szűrőt kapcsolsz, kvízt indítasz).
  - Nyitott fajtakártya, szűrőlap vagy fiók fölé nem ugrik.
- **Újraindítás:** Tippek → „Bemutató újra”, vagy a `?bemutato` URL-paraméter (telepített appban is). A `?nocoach` továbbra is kihagyja.

## 1.4.1 – 2026-09-24
- **Felhő nézet:** szűrés után (pl. csak „Gyerek”) a felhő közepe már nem kavarog. Az ütközés a lendületet is fékezi (a frissen megkavart buborékokat kivéve), és „Csak találatok” módban kisebb a középre húzás. A mérés szerint a középső rész mozgása képkockánként 1,3–2,5 px-ről kb. 0,03 px-re csökkent.

## 1.4.0 – 2026-09-24
- **Verziózás:**
  - látható verziószám és build-azonosító az appban;
  - a service worker gyorsítótárának neve is tartalmazza a verziót;
  - változásnapló.
- **Kártyanyitás telefonon – javítva:** ha a jobb szélen lévő, hosszú nevű fajtára koppintottál, az oldal „kicsinyedett”. Emiatt a kártya eltolódott, a bezáró ✕ kilógott a képből, és a kinyílás rossz helyről indulhatott.
  - Koppintásra már nem jelenik meg a névcímke.
  - A színpad vízszintesen nem lóg ki, és az oldal nem kicsinyíthető.
- **Kinyílás és bezárás:** a kör alakú mozgást képkockánként a kód vezérli. Mindig a buborékból indul, és a végén a vágás biztosan lekerül.
- **Portré:** a buborék megérintésekor előre dekódolódik, így nincs üres kör a kinyílás elején.

## 1.3.0 – 2026-09-24 · `c285485`
- A „Csak találatok” az alapértelmezett szűrési mód mindkét platformon.
- **Kevés találatnál asztalon:** kisebb buborékok, visszafogottabb gyűrű és ragyogás.
- **Térkép:** kis kijelzőn is nyugodt, megszűnt a rángás.
- **Mobil kártyanyitás:** nincs akadás (számláló-hiba javítva, a lenti tartalom később töltődik, előzetes bemelegítés).

## 1.2.1 – 2026-09-24 · `cef3c64`
- **Kavarás:** a hullámkörök a buborékok fölött látszanak.

## 1.2.0 – 2026-09-24 · `2537fc8`
- **Mobil villogás javítva:** a grafikus memória 465 MB-ról kb. 40 MB-ra csökkent.
- **Új:** ujjal kavarás a felhőn.
- **Sötét mód:**
  - olvasható kitöltött gombok és telepítési értesítés;
  - tömör bezáró gomb;
  - javított státuszsáv-szín.

## 1.1.0 – 2026-09-24 · `b02fc98`, `749824d`
- Közzététel GitHub Pagesen, automatikus frissítéssel.
- **Lista nézet:** nem maradnak kint peremkörök.
- „Párkereső kvíz” gyorsparancs, megbízhatóbb PWA-frissítés.

## 1.0.0 – 2026-09-24 · `f15c66c`
- **Első kiadás:**
  - 124 fajta élő felhőben, szűrőkkel;
  - Felhő, Csoportok, Térkép és Lista nézet;
  - fajtakártya, Párkereső kvíz, kedvencek, összehasonlítás;
  - sötét mód, telepíthető PWA, teljesítmény-optimalizálás.
