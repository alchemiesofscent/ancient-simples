---
status: historical
owner: archive
---

### Methodology for Extracting "Variety / Part / Product"

The extraction logic follows a hierarchical analysis of the Greek text and its English translation to identify specific modifiers that narrow down the general **Lemma**.

1.  **Identification of Anatomical/Botanical Part:**
    *   I scan the text for nouns denoting specific components of the organism.
    *   *Examples:* `ῥίζα` (Root), `σπέρμα` (Seed), `φύλλον` (Leaf), `ἧπαρ` (Liver), `κέρας` (Horn).
    *   If the Lemma is the whole organism (e.g., "The Oak"), the Part column receives the component (e.g., "Bark").

2.  **Identification of Derived Products:**
    *   I look for substances processed or extracted from the source.
    *   *Examples:* `ὀπός` (Juice/Sap), `ἔλαιον` (Oil), `τέφρα` (Ash), `κονία` (Lye), `ἀφέψημα` (Decoction).

3.  **Identification of Taxonomical or Typological Variety:**
    *   I scan for adjectives that distinguish species or types within a genus.
    *   *Examples:* `ἄγριος` (Wild) vs. `ἥμερος` (Cultivated); `μέλας` (Black) vs. `λευκός` (White); Geographic origins (e.g., "Lemnian," "Scythian") only when they denote a distinct sub-type recognized in the materia medica.

4.  **Identification of State/Condition:**
    *   I extract participles or adjectives describing the physical state of the substance if it alters the medicinal property.
    *   *Examples:* `κεκαυμένος` (Burnt), `ξηρός` (Dry), `χλωρός` (Fresh/Green), `πεπλυμένος` (Washed).

5.  **Consolidation:**
    *   If multiple parts or states are listed for a single entry (e.g., "leaves and roots"), they are comma-separated.
    *   The English column translates the Greek extraction using standard botanical/anatomical terminology found in the provided translation text.

---

### Controlled Vocabulary

Below is the controlled vocabulary used for the extraction, categorized by domain.

#### 1. Botanical Parts (Plants)
| English | Greek Term(s) |
| :--- | :--- |
| **Root** | ῥίζα (rhiza) |
| **Seed** | σπέρμα (sperma), κόκκος (kokkos) |
| **Leaf / Foliage** | φύλλον (phullon), κόμη (komē) |
| **Flower / Blossom** | ἄνθος (anthos) |
| **Fruit** | καρπός (karpos) |
| **Bark / Rind** | φλοιός (phloios), λέμμα (lemma) |
| **Shoot / Twig / Branch** | βλαστός (blastos), ἀκρέμων (akremon), κλών (klon) |
| **Stem / Stalk** | καυλός (kaulos) |
| **Pith** | ἐντεριώνη (enteriōne) |
| **Wood** | ξύλον (xulon) |
| **Spike / Ear** | στάχυς (stachys) |
| **Husk / Shell** | κέλυφος (kelyphos), λέπος (lepos) |

#### 2. Anatomical Parts (Animals)
| English | Greek Term(s) |
| :--- | :--- |
| **Blood** | αἷμα (haima) |
| **Liver** | ἧπαρ (hepar) |
| **Lung** | πνεύμων (pneumon) |
| **Brain** | ἐγκέφαλος (enkephalos) |
| **Heart** | καρδία (kardia) |
| **Stomach / Gut** | κοιλία (koilia), γαστήρ (gaster) |
| **Testicles** | ὄρχεις (orcheis) |
| **Kidney** | νεφρός (nephros) |
| **Flesh / Meat** | σάρξ (sarx), κρέας (kreas) |
| **Fat / Suet / Lard** | πιμελή (pimele), στέαρ (stear) |
| **Marrow** | μυελός (myelos) |
| **Bone** | ὀστέον (osteon) |
| **Horn** | κέρας (keras) |
| **Hoof / Claw** | ὄνυξ (onyx) |
| **Skin / Hide** | δέρμα (derma) |
| **Head** | κεφαλή (kephalē) |
| **Wing** | πτερόν (pteron) |
| **Shell (Sea)** | ὄστρακον (ostrakon) |
| **Egg** | ὠόν (oōn) |
| **Yolk** | λέκιθος (lekithos) |
| **White (of egg)** | λευκόν (leukon) |

#### 3. Bodily Fluids & Excretions
| English | Greek Term(s) |
| :--- | :--- |
| **Dung / Excrement** | κόπρος (kopros), ἀφόδευμα (aphodeuma) |
| **Urine** | οὖρον (ouron) |
| **Milk** | γάλα (gala) |
| **Whey** | ὀρρός (orros) |
| **Rennet** | πυτία (pytia) |
| **Bile** | χολή (cholē) |
| **Sweat** | ἱδρώς (hidrōs) |
| **Saliva / Spittle** | σίαλον (sialon), πτύελον (ptyelon) |
| **Dirt / Grease (Wool)** | ῥύπος (rhypos), οἴσυπος (oisypos) |

#### 4. Products & Derivatives
| English | Greek Term(s) |
| :--- | :--- |
| **Oil** | ἔλαιον (elaion) |
| **Juice / Sap / Latex** | ὀπός (opos), χυλός (chylos) |
| **Resin** | ῥητίνη (rhetine) |
| **Gum** | κόμμι (kommi) |
| **Ash** | τέφρα (tephra), σποδός (spodos) |
| **Soot** | λιγνύς (lignus), αἰθάλη (aithalē) |
| **Lye** | κονία (konia) |
| **Wine** | οἶνος (oinos) |
| **Vinegar** | ὄξος (oxos) |
| **Honey** | μέλι (meli) |
| **Wax** | κηρός (keros) |
| **Cheese** | τυρός (tyros) |
| **Butter** | βούτυρος (boutyros) |
| **Meal / Flour** | ἄλευρον (aleuron), ἄλφιτον (alphiton) |
| **Brine** | ἅλμη (halmē) |

#### 5. States & Conditions (Descriptors)
| English | Greek Term(s) |
| :--- | :--- |
| **Wild** | ἄγριος (agrios) |
| **Cultivated / Garden** | ἥμερος (hemeros), κηπευτός (kepeutos) |
| **Burnt / Roasted** | κεκαυμένος (kekaumenos), ὀπτός (optos), φρυκτός (phryktos) |
| **Dried / Dry** | ξηρός (xeros) |
| **Fresh / Green** | χλωρός (chloros), πρόσφατος (prosphatos) |
| **Washed** | πεπλυμένος (peplymenos) |
| **Unwashed** | ἄπλυτος (aplytos) |
| **Male** | ἄρρην (arren) |
| **Female** | θῆλυς (thelys) |
| **White** | λευκός (leukos) |
| **Black** | μέλας (melas) |
| **Old** | παλαιός (palaios) |
| **Salted / Pickled** | ταριχηρός (taricheros) |
