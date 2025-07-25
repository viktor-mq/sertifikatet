# 3.1 Bremselengde og Reaksjonstid - Sammendrag 🛑

## Hovedpoeng
Din totale stopplengde er summen av reaksjonslengde og bremselengde. Å forstå disse er avgjørende for sikker kjøring og for å unngå ulykker. Mange faktorer påvirker hvor lang tid og avstand du trenger for å stoppe bilen.

## Reaksjonstid: Før Handling

### 1. **Hva er det?**
- Tiden fra du oppdager en fare til du begynner å handle (f.eks. flytte foten til bremsen).
- Gjennomsnitt: **0,8 - 1 sekund** for en opplagt sjåfør.

### 2. **Påvirkende faktorer:**
- **Førerens tilstand:** Trøtthet, rus, sykdom, distraksjoner (mobilbruk).
- **Sikt:** Dårlig vær, mørke, uoversiktlige veier.

### 3. **Reaksjonslengde:**
- Avstanden bilen tilbakelegger i løpet av reaksjonstiden.
- Ved 80 km/t tilbakelegger du ca. 22 meter *før* du begynner å bremse.

## Bremselengde: Selve Stoppet

### 1. **Hva er det?**
- Avstanden bilen tilbakelegger fra du begynner å bremse til den står stille.

### 2. **Påvirkende faktorer:**
- **Hastighet:** Den viktigste faktoren! **Dobler du hastigheten, firedobles bremselengden.**
- **Føreforhold:** Tørr, våt, is, snø, grus. Friksjonen mellom dekk og vei.
- **Dekk:** Mønsterdybde, type (sommer/vinter), lufttrykk.
- **Bilens tilstand:** Bremser, vekt, ABS-system.
- **Veiens helning:** Nedoverbakke øker, oppoverbakke reduserer.

### 3. **Eksempel:**


<div style="font-family: sans-serif; max-width: 400px; margin-top: 1em;">
  <div style="margin-bottom: 8px;">
    <label for="dry"><input type="radio" id="dry" name="surface" value="dry" checked onchange="updateBrakeDistance()"> Tørr asfalt</label>
    <label for="slippery" style="margin-left: 15px;"><input type="radio" id="slippery" name="surface" value="slippery" onchange="updateBrakeDistance()"> Glatt føre</label>
  </div>
  <div style="text-align: center;">
    <label for="speedRange"><strong>Fart (km/t):</strong> <span id="speedValue">50</span></label>
  </div>
  <input type="range" id="speedRange" min="10" max="130" value="50" step="1" oninput="updateBrakeDistance()" style="width: 100%;">
  <p>💡 <strong>Bremselengde (<span id="surfaceLabel">tørr asfalt</span>):</strong> <span id="brakeDistance">12.5</span> meter</p>
  <p><strong>Formel:</strong> (fart / 10) × (fart / 10) ÷ 2 &nbsp;&nbsp; <em>(på glatt føre: ganger resultatet med 4)</em></p>
</div>
- Ved 80 km/t: ca. 32 meter.
<script>
  function updateBrakeDistance() {
    const speed = parseInt(document.getElementById("speedRange").value);
    const x = speed / 10;
    let distance = (x * x) / 2;

    const surface = document.querySelector('input[name="surface"]:checked').value;
    if (surface === "slippery") {
      distance *= 4;
    }

    document.getElementById("speedValue").textContent = speed;
    document.getElementById("brakeDistance").textContent = distance.toFixed(1);
    const surfaceLabel = surface === "slippery" ? "glatt føre" : "tørr asfalt";
    document.getElementById("surfaceLabel").textContent = surfaceLabel;
    const formulaNote = surface === "slippery" ? "(ganger 4 ved glatt føre)" : "";
    document.getElementById("formulaNote").textContent = formulaNote;
  }

  updateBrakeDistance(); // init
</script>

## Total Stopplengde: Reaksjonslengde + Bremselengde

- **80 km/t (tørr asfalt, 1 sek reaksjon):** 22 m (reaksjon) + 40 m (brems) = **62 meter**.
- På is kan stopplengden bli flere hundre meter!

## ⚠️ Viktigst å huske
- **Hastighet:** Den største synderen for lang stopplengde.
- **Hold avstand:** Gi deg selv nok tid og rom til å stoppe.
- **Tilpass farten:** Kjør alltid etter forholdene, ikke bare fartsgrensen.

## Sjekkliste for Sikker Stopp
✅ **Uthvilt og fokusert?** Reduser reaksjonstiden.
✅ **God avstand til forankjørende?** Gi deg selv rom.
✅ **Tilpasset fart til forholdene?** Unngå unødvendig lang bremselengde.
✅ **Dekk og bremser i orden?** Sørg for optimalt grep og funksjon.

## Huskeregel
> **"Fart dreper, avstand redder. Bremselengden lyver aldri."**

Forståelse av stopplengde er grunnlaget for defensiv kjøring.