# Offerings in Leviticus 
#biblestudy/devotionals/leviticus

```mermaid
flowchart TD
    %% 1. GLOBAL STARTING POINT
    Start([Worshipper Brings an Offering]) --> OfferType{What type of
    offering is it?}

    %% ==========================================
    %% BRANCH A: BURNT OFFERING (Leviticus 1)
    %% ==========================================
    OfferType -- Burnt Offering --> BurntAnimal{What animal?}
    BurntAnimal -- Herd / Flock --> BurntMale[Bring a male without blemish]
    BurntMale --> HandHead[Worshipper lays hand on the animal's head]
    BurntMale --> KillNorth[Kill it at the north side of the altar]

    %% ==========================================
    %% BRANCH B: PEACE / THANK OFFERING (Leviticus 3)
    %% ==========================================
    OfferType -- Peace / Thank Offering --> PeaceAnimal{What animal?}
    PeaceAnimal -- Herd / Flock --> PeaceChoice[Bring male or female without blemish]
    PeaceChoice --> HandHead %% Reusing the same HandHead node!
    PeaceChoice --> KillDoor[Kill it at the door of the Tabernacle]

    %% ==========================================
    %% BRANCH C: SIN OFFERING (Leviticus 4)
    %% ==========================================
    OfferType -- Sin Offering --> SinRuler[Ruler brings a male goat without blemish]
    SinRuler --> HandHead %% Reusing the same HandHead node!
    SinRuler --> KillDoor %% Reusing the same KillDoor node!

    %% ==========================================
    %% MERGING ENTRANCES TO SHARED RITUALS
    %% ==========================================
    
    %% All blood rituals funnel into shared altar destinations
    KillNorth --> AltarSides[Priests sprinkle blood ALL AROUND the Altar]
    KillDoor --> AltarSides
    
    %% Sin offering has a unique blood ritual but merges later
    HandHead --> SinRulerKill[Kill sin offering] --> AltarHorns[Priest puts blood on the HORNS of the Altar]

    %% Funneling everything to the final burning processes
    AltarSides --> CutAndWash[Cut animal into pieces and wash entrails]
    CutAndWash --> BurnAll([Priest burns the WHOLE animal on the Altar])

    AltarHorns --> BurnFat[Priest burns only the FAT portions on the Altar]
    PeaceChoice --> PeaceBlood[Sprinkle blood all around] --> BurnFat %% Peace offering fat goes here too!

    BurnFat --> RitualEnd([Atonement made / Fellowship restored])
```


## Instruction for using Mermaid code
See [[Using Mermaid Diagrams in Markdown]].

### Overview of types of offerings

# Overzicht van de offers in Leviticus 1–7

Hieronder een zo compleet mogelijk overzicht van de vijf hoofdtypen offers uit Leviticus 1–7, met hun ondersoorten. Elk offertype heeft een eigen tabel omdat de details (dier, geslacht, onderdelen, bloedhandeling) per categorie sterk verschillen.

---

## 1. Brandoffer (Hebreeuws: *olah*, "wat opstijgt") — Leviticus 1; 6:8-13

Vrijwillig offer van volledige toewijding. Het hele dier gaat in rook op — vandaar de naam.

| Onderdeel | Rund | Schaap/geit | Vogel (tortelduif/jonge duif) |
|---|---|---|---|
| **Geslacht** | Mannelijk, zonder gebrek | Mannelijk, zonder gebrek | Niet gespecificeerd (armen-variant) |
| **Wie brengt** | Iedere Israëliet, naar draagkracht | Idem | Wie geen rund of kleinvee kan betalen |
| **Reden** | Vrijwillige toewijding, algemene verzoening, aangename geur voor de Heer | Idem | Idem |
| **Plaats van slachten** | Ingang tent der samenkomst, noordzijde van het altaar (Lev. 1:11) | Idem | Bij het altaar |
| **Bloedhandeling** | Rondom tegen de zijkanten van het altaar gesprenkeld door de priester | Idem | Priester knijpt de nek door en laat bloed tegen de altaarwand lopen |
| **Op altaar verbrand** | Kop, vet, gewassen ingewanden en poten — alles behalve de huid | Idem | Alles, na verwijdering van krop en veren |
| **Voor de priester** | De huid (Lev. 7:8) | De huid | — |
| **Voor de offeraar** | Niets — het hele dier is voor God | Niets | Niets |
| **Speciale handelingen** | Handoplegging op de kop (identificatie), villen, in stukken verdelen, priester rangschikt hout en stukken op het altaar; het vuur mag nooit doven (Lev. 6:9-13) | Idem | Nek doorknijpen (niet volledig onthoofden), niet villen |

---

## 2. Graanoffer (Hebreeuws: *minchah*, "geschenk") — Leviticus 2; 6:14-23

Het enige onbloedige offer van de vijf; geen dier.

| Onderdeel | Details |
|---|---|
| **Basis** | Fijn tarwemeel, olijfolie, wierook |
| **Verboden ingrediënten** | Zuurdesem (gist) en honing mogen niet verbrand worden (Lev. 2:11) |
| **Verplicht ingrediënt** | Zout ("zout van het verbond", Lev. 2:13) |
| **Varianten** | Ongebakken meel met olie en wierook / gebakken in de oven (ongezuurde koeken of platte broden met olie) / gebakken in de pan / geroosterde verse aren (eerstelingenoffer, Lev. 2:14) |
| **Reden** | Erkenning dat levensonderhoud van God komt; begeleidt vaak het brandoffer of vredeoffer |
| **Op altaar verbrand** | Alleen het "gedenkdeel" (*azkarah*): een handvol meel/deeg met alle wierook |
| **Voor de priester** | De rest van het meel/deeg — ongezuurd gegeten op een heilige plaats (Lev. 6:16-18) |
| **Voor de offeraar** | Niets |
| **Speciale handelingen** | Geen handoplegging (geen dier); priester neemt het gedenkdeel met de hand |

---

## 3. Vredeoffer / dankoffer (Hebreeuws: *shelamim* of *zebach*) — Leviticus 3; 7:11-36

Het enige offer waarvan de offeraar zelf ook mag eten — een gemeenschapsmaaltijd met God.

| Onderdeel | Rund | Schaap | Geit |
|---|---|---|---|
| **Geslacht** | Mannelijk of vrouwelijk, zonder gebrek | Mannelijk of vrouwelijk | Mannelijk of vrouwelijk |
| **Reden** | Dank (*todah*), gelofte (*neder*), of vrijwillig (*nedabah*) — Lev. 7:11-16 | Idem | Idem |
| **Plaats van slachten** | Ingang tent der samenkomst | Idem | Idem |
| **Bloedhandeling** | Rondom tegen het altaar gesprenkeld | Idem | Idem |
| **Op altaar verbrand (vet)** | Net over de ingewanden, al het vet aan de ingewanden, beide nieren met niervet, de leverlob | Zelfde vetdelen **plus** de hele vette staart (Lev. 3:9) | Zelfde vetdelen als bij rund |
| **Voor de priester** | Borststuk (beweegoffer) en rechterbout (hefoffer) — Lev. 7:30-34 | Idem | Idem |
| **Voor de offeraar** | Rest van het vlees | Idem | Idem |
| **Eettermijn** | Dankoffer: zelfde dag; gelofte/vrijwillig: dag + volgende dag; op de derde dag verbranden (Lev. 7:15-18) | Idem | Idem |
| **Speciale handelingen** | Handoplegging, "bewegen" (heen en weer bewegen) van borststuk voor het aangezicht van de Heer | Idem | Idem |

---

## 4. Zondoffer / reinigingsoffer (Hebreeuws: *chatat*) — Leviticus 4:1–5:13; 6:24-30

Verplicht offer voor onopzettelijke zonde. Getrapt naar wie zondigt — hoe hoger de verantwoordelijkheid, hoe zwaarder het offer én hoe het karkas verwerkt wordt.

| Wie zondigt | Dier | Geslacht | Bloedhandeling | Op altaar verbrand | Rest van het dier | Bijbeltekst |
|---|---|---|---|---|---|---|
| **Gezalfde priester** | Jonge stier | Mannelijk, zonder gebrek | 7x gesprenkeld vóór het voorhangsel + gestreken op de hoorns van het **reukofferaltaar** binnen; rest uitgegoten aan de voet van het brandofferaltaar | Alleen het vet (net, nieren, niervet, leverlob) | Huid, vlees, kop, poten, ingewanden, mest — **buiten de legerplaats** verbrand op een reine plaats | Lev. 4:3-12 |
| **Hele gemeenschap Israël** | Jonge stier | Mannelijk | Zelfde procedure als bij de priester | Alleen het vet | Zelfde als bij de priester — buiten de legerplaats verbrand | Lev. 4:13-21 |
| **Leider (nasi)** | Geitenbok | Mannelijk, zonder gebrek | Gestreken op de hoorns van het **brandofferaltaar** (buiten); rest aan de voet uitgegoten — bloed komt niet in het heiligdom | Alleen het vet | Vlees is voor de priester om te eten, op een heilige plaats (Lev. 6:26) | Lev. 4:22-26 |
| **Gewoon persoon** | Geit of ooilam | Vrouwelijk, zonder gebrek | Zelfde als bij de leider | Alleen het vet | Vlees voor de priester, te eten | Lev. 4:27-35 |
| **Arme (kan geen kleinvee betalen)** | 2 tortelduiven of jonge duiven | — | Eén als zondoffer (nek doorgeknepen, bloed tegen altaarwand gesprenkeld), één als brandoffer | Zondoffer-vogel: verbrand; brandoffer-vogel: geheel verbrand | Vlees voor priester | Lev. 5:7-10 |
| **Zeer arme (kan zelfs geen vogels betalen)** | 1/10 efa fijn meel, **zonder** olie of wierook | — | Geen bloedhandeling (geen dier) | Handvol als gedenkdeel verbrand | Rest voor priester | Lev. 5:11-13 |

---

## 5. Schuldoffer (Hebreeuws: *asham*) — Leviticus 5:14–6:7; 7:1-10

Voor heiligschennis of bedrog waarbij naast verzoening ook schadevergoeding nodig is.

| Onderdeel | Details |
|---|---|
| **Dier** | Ram |
| **Geslacht** | Mannelijk, zonder gebrek, met een door de priester getaxeerde waarde in zilveren sikkels |
| **Situaties** | Onopzettelijke overtreding tegen heilige gaven (Lev. 5:15-16); onzekerheid of men gezondigd heeft (Lev. 5:17-19); bedrog, diefstal, verduistering, valse eed (Lev. 6:1-7) |
| **Extra verplichting** | Volledige terugbetaling van de schade **plus** een vijfde erbovenop, aan de benadeelde (Lev. 6:5) |
| **Plaats van slachten** | Op de plaats waar het brandoffer wordt geslacht |
| **Bloedhandeling** | Rondom tegen het altaar gesprenkeld (zoals brandoffer) |
| **Op altaar verbrand** | Het vet (net, nieren, niervet, leverlob) — zoals bij het vredeoffer |
| **Voor de priester** | Het vlees — zeer heilig, te eten door mannelijke priesters op een heilige plaats |
| **Voor de offeraar** | Niets |
| **Speciale handelingen** | Geen handoplegging vermeld; nadruk ligt op taxatie en schadevergoeding |

---

## Samenvattend overzicht

| Offertype | Vrijwillig / verplicht | Dier(en) | Geslacht | Wie eet mee? | Hoofddoel |
|---|---|---|---|---|---|
| Brandoffer (*olah*) | Vrijwillig | Rund, schaap, geit, duif | Mannelijk | Niemand — geheel verbrand | Volledige toewijding |
| Graanoffer (*minchah*) | Vrijwillig | Geen dier (meel) | — | Priester | Erkenning van Gods voorzienigheid |
| Vredeoffer (*shelamim*) | Vrijwillig | Rund, schaap, geit | Mannelijk of vrouwelijk | Priester én offeraar | Gemeenschap, dank |
| Zondoffer (*chatat*) | Verplicht | Stier, bok, ooi, duif, meel | Wisselt per status offeraar | Priester (bij lagere status) / niemand (bij priester of volk) | Reiniging van onopzettelijke zonde |
| Schuldoffer (*asham*) | Verplicht | Ram | Mannelijk | Priester | Herstel na heiligschennis/bedrog + schadevergoeding |

---

### Bronvermelding
Samengesteld op basis van de tekst van Leviticus 1–7 (NBV21/HSV), aangevuld met inzichten uit commentaren zoals Kingcomments en het overzichtsartikel "Verschillende offers uit de Bijbel" (EO). Zie ook Hebreeën 13:11-12 voor de nieuwtestamentische typologie van het "buiten de legerplaats verbranden" bij het zondoffer.
