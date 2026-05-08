import sqlite3
import os
import json
from datetime import datetime

_PRIMARY_DB = os.path.join(os.path.dirname(__file__), 'data', 'learning_app.db')
_FALLBACK_DB = os.path.join(os.path.expanduser('~'), '.ai_learning_mentor', 'learning_app.db')

def _resolve_db_path():
    """Return a writable DB path, falling back to home dir if the primary mount is read-only."""
    os.makedirs(os.path.dirname(_PRIMARY_DB), exist_ok=True)
    try:
        # Write test — create a temp table and immediately roll back.
        test_conn = sqlite3.connect(_PRIMARY_DB, check_same_thread=False)
        test_conn.execute("CREATE TABLE IF NOT EXISTS _write_test (x INTEGER)")
        test_conn.commit()
        test_conn.execute("DROP TABLE IF EXISTS _write_test")
        test_conn.commit()
        test_conn.close()
        return _PRIMARY_DB
    except sqlite3.OperationalError:
        os.makedirs(os.path.dirname(_FALLBACK_DB), exist_ok=True)
        return _FALLBACK_DB

DB_PATH = _resolve_db_path()

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            target_year INTEGER,
            target_exam TEXT DEFAULT 'JEE Mains',
            current_level TEXT,
            study_hours INTEGER,
            ai_provider TEXT DEFAULT 'Gemini',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Topics table — the content backbone
    c.execute('''
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            chapter TEXT NOT NULL,
            topic_name TEXT NOT NULL,
            description TEXT,
            formula_sheet TEXT,
            difficulty TEXT,
            cbse_weightage INTEGER DEFAULT 0,
            jee_weightage INTEGER DEFAULT 0,
            key_concepts TEXT,
            common_mistakes TEXT,
            tips TEXT
        )
    ''')

    # Study Plan table
    c.execute('''
        CREATE TABLE IF NOT EXISTS study_plan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date DATE,
            topic_id INTEGER,
            task_type TEXT,
            priority INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (topic_id) REFERENCES topics (id)
        )
    ''')

    # Questions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER,
            q_type TEXT,
            difficulty TEXT,
            question_text TEXT NOT NULL,
            options TEXT,
            correct_option TEXT,
            solution_text TEXT,
            hint TEXT,
            pyq_year TEXT,
            FOREIGN KEY (topic_id) REFERENCES topics (id)
        )
    ''')

    # Test Results table
    c.execute('''
        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            test_type TEXT,
            subject_filter TEXT,
            total_questions INTEGER,
            correct_answers INTEGER,
            time_taken INTEGER,
            score REAL,
            topic_breakdown TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Performance Tracking table
    c.execute('''
        CREATE TABLE IF NOT EXISTS performance_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            topic_id INTEGER,
            accuracy REAL DEFAULT 0.0,
            times_tested INTEGER DEFAULT 0,
            weak_area_flag BOOLEAN DEFAULT 1,
            last_practiced TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (topic_id) REFERENCES topics (id)
        )
    ''')

    # Daily Streaks table
    c.execute('''
        CREATE TABLE IF NOT EXISTS study_streaks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date DATE NOT NULL,
            minutes_studied INTEGER DEFAULT 0,
            tasks_completed INTEGER DEFAULT 0,
            tests_taken INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, date)
        )
    ''')

    # Bookmarks table
    c.execute('''
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question_id INTEGER,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (question_id) REFERENCES questions (id),
            UNIQUE(user_id, question_id)
        )
    ''')

    # Flashcards table
    c.execute('''
        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            topic_id INTEGER,
            front_text TEXT NOT NULL,
            back_text TEXT NOT NULL,
            difficulty TEXT DEFAULT 'Medium',
            next_review DATE,
            review_count INTEGER DEFAULT 0,
            ease_factor REAL DEFAULT 2.5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (topic_id) REFERENCES topics (id)
        )
    ''')

    conn.commit()
    conn.close()


def populate_comprehensive_data():
    """Populate the database with real NCERT Class 12 + JEE content.
    Only runs if the topics table is empty."""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM topics")
    if c.fetchone()[0] > 0:
        conn.close()
        return  # Already populated
    
    # ========================================================================
    # PHYSICS TOPICS (Class 12 NCERT + JEE)
    # ========================================================================
    physics_topics = [
        # Electrostatics
        ('Physics', 'Electrostatics', "Coulomb's Law", 
         'Force between two point charges is directly proportional to product of charges and inversely proportional to square of distance.', 
         r'F = \frac{1}{4\pi\epsilon_0} \cdot \frac{q_1 q_2}{r^2}', 'Medium', 8, 7,
         'Superposition principle, Vector nature of force, Permittivity',
         'Forgetting vector nature; using wrong sign for unlike charges',
         'Always draw FBD. Check if charges are point charges or distributed.'),
        ('Physics', 'Electrostatics', 'Electric Field & Field Lines',
         'Electric field is force per unit positive test charge. Field lines represent the direction of electric field.',
         r'E = \frac{F}{q_0} = \frac{1}{4\pi\epsilon_0} \cdot \frac{Q}{r^2}', 'Medium', 7, 7,
         'Field due to point charge, dipole, continuous distributions',
         'Confusing field direction for negative charges',
         'Field lines never cross. They go from + to - charge.'),
        ('Physics', 'Electrostatics', 'Electric Potential & Potential Energy',
         'Work done per unit charge in bringing a test charge from infinity to that point.',
         r'V = \frac{1}{4\pi\epsilon_0} \cdot \frac{Q}{r}, \quad U = \frac{1}{4\pi\epsilon_0} \cdot \frac{q_1 q_2}{r}', 'Hard', 8, 8,
         'Equipotential surfaces, Potential due to dipole, Relation E = -dV/dr',
         'Mixing up potential (scalar) with field (vector)',
         'Potential is scalar — just add algebraically. No vector addition needed!'),
        ('Physics', 'Electrostatics', 'Capacitance & Capacitors',
         'Ability of a conductor to store charge. Capacitor stores energy in electric field.',
         r'C = \frac{Q}{V}, \quad C_{parallel} = \frac{\epsilon_0 A}{d}, \quad U = \frac{1}{2}CV^2', 'Medium', 7, 7,
         'Series & parallel combinations, Dielectrics, Energy stored',
         'Wrong formula for series vs parallel (opposite of resistors!)',
         'For capacitors: Series = reciprocal sum, Parallel = direct sum (opposite of resistors!)'),
        ('Physics', 'Electrostatics', "Gauss's Law",
         'Total electric flux through a closed surface is 1/ε₀ times the charge enclosed.',
         r'\oint \vec{E} \cdot d\vec{A} = \frac{Q_{enc}}{\epsilon_0}', 'Hard', 6, 9,
         'Gaussian surfaces, Applications to symmetric charge distributions',
         'Choosing wrong Gaussian surface; confusing flux with field',
         'Choose Gaussian surface where E is constant or zero on every part.'),

        # Current Electricity
        ('Physics', 'Current Electricity', "Ohm's Law & Resistance",
         'Current through conductor is proportional to potential difference across it, at constant temperature.',
         r'V = IR, \quad R = \rho \frac{L}{A}', 'Easy', 8, 6,
         'Resistivity, Temperature dependence, Color coding',
         'Confusing resistance with resistivity',
         'Remember: R depends on geometry (L, A), ρ depends on material.'),
        ('Physics', 'Current Electricity', "Kirchhoff's Laws",
         'Junction rule (current conservation) and Loop rule (energy conservation) for circuit analysis.',
         r'\sum I_{in} = \sum I_{out}, \quad \sum V = 0 \text{ (around loop)}', 'Hard', 7, 8,
         'Complex circuit solving, Wheatstone bridge, Meter bridge',
         'Wrong sign convention in loop rule',
         'Fix a direction for current first. If answer is negative, current flows opposite.'),
        ('Physics', 'Current Electricity', 'EMF & Internal Resistance',
         'EMF is work done per unit charge by the source. Terminal voltage drops due to internal resistance.',
         r'V = \varepsilon - Ir, \quad P_{max} \text{ when } R = r', 'Medium', 6, 7,
         'Cells in series/parallel, Maximum power transfer',
         'Ignoring internal resistance in calculations',
         'A "dead" battery has high internal resistance — that is why V drops.'),

        # Magnetism
        ('Physics', 'Moving Charges & Magnetism', 'Magnetic Force on Charges',
         'A moving charge in magnetic field experiences a force perpendicular to both velocity and field.',
         r'F = qvB\sin\theta, \quad \vec{F} = q(\vec{v} \times \vec{B})', 'Medium', 7, 8,
         'Lorentz force, Circular motion in B, Cyclotron',
         'Forgetting that force is zero when v is parallel to B',
         'Use right-hand rule: curl fingers from v to B, thumb gives F direction (for +q).'),
        ('Physics', 'Moving Charges & Magnetism', 'Biot-Savart & Ampere Law',
         'Biot-Savart gives magnetic field due to a current element. Ampere law relates field to enclosed current.',
         r'dB = \frac{\mu_0}{4\pi} \frac{I \, dl \sin\theta}{r^2}, \quad \oint \vec{B} \cdot d\vec{l} = \mu_0 I_{enc}', 'Hard', 6, 9,
         'Field due to straight wire, circular loop, solenoid',
         'Wrong application of Ampere law to non-symmetric cases',
         'Ampere law is easy to USE only when B is constant on Amperian loop.'),

        # EMI
        ('Physics', 'Electromagnetic Induction', "Faraday's Law & Lenz's Law",
         'Changing magnetic flux induces EMF. Direction of induced current opposes the change (Lenz law).',
         r'\varepsilon = -\frac{d\Phi_B}{dt}, \quad \Phi_B = BA\cos\theta', 'Hard', 8, 9,
         'Motional EMF, Self and mutual inductance, Eddy currents',
         'Wrong sign in Lenz law; confusing flux with field',
         'Think of Lenz law as nature being "lazy" — it opposes change.'),
        ('Physics', 'Electromagnetic Induction', 'AC Circuits & Transformers',
         'Alternating current varies sinusoidally. Transformers change voltage levels using mutual induction.',
         r'V = V_0 \sin(\omega t), \quad \frac{V_s}{V_p} = \frac{N_s}{N_p}', 'Hard', 7, 7,
         'RMS values, Impedance, Resonance, Power factor',
         'Using peak values instead of RMS in power calculations',
         'Always use RMS values for power. P = VᵣₘₛIᵣₘₛcos(φ)'),

        # Optics
        ('Physics', 'Ray Optics', 'Reflection & Mirrors',
         'Light bouncing off surfaces. Concave mirrors converge, convex mirrors diverge.',
         r'\frac{1}{v} + \frac{1}{u} = \frac{1}{f}, \quad m = -\frac{v}{u}', 'Easy', 6, 5,
         'Sign convention, Image formation, Applications',
         'Wrong sign convention (always use New Cartesian!)',
         'Draw ray diagrams FIRST, then verify with formula.'),
        ('Physics', 'Ray Optics', 'Refraction & Lenses',
         'Bending of light when passing from one medium to another due to change in speed.',
         r'n_1 \sin i = n_2 \sin r, \quad \frac{1}{v} - \frac{1}{u} = \frac{1}{f}', 'Medium', 7, 7,
         'Total internal reflection, Lens combinations, Power of lens',
         'Using mirror formula for lens (signs are different!)',
         'Lens formula has MINUS for u, mirror formula has PLUS. Be careful!'),
        ('Physics', 'Wave Optics', "Young's Double Slit Experiment",
         'Demonstrates wave nature of light through interference pattern.',
         r'\Delta x = \frac{\lambda D}{d}, \quad I = I_0 \cos^2\left(\frac{\pi d \sin\theta}{\lambda}\right)', 'Hard', 7, 8,
         'Constructive/destructive interference, Fringe width, Diffraction',
         'Confusing path difference with phase difference',
         'Path diff = nλ for bright, (n+½)λ for dark. Convert to phase: Δφ = 2π/λ × Δx'),

        # Modern Physics
        ('Physics', 'Dual Nature of Matter', 'Photoelectric Effect',
         'Emission of electrons when light of sufficient frequency falls on a metal surface.',
         r'E = h\nu = h\nu_0 + \frac{1}{2}mv_{max}^2, \quad \lambda = \frac{h}{p}', 'Medium', 8, 8,
         'Threshold frequency, Work function, de Broglie wavelength',
         'Thinking intensity affects KE (it only affects number of electrons!)',
         'Intensity → more electrons (more current). Frequency → more KE per electron.'),
        ('Physics', 'Atoms & Nuclei', "Bohr's Model & Hydrogen Spectrum",
         "Bohr's postulates explain discrete energy levels and spectral lines of hydrogen.",
         r'E_n = -\frac{13.6}{n^2} \text{ eV}, \quad r_n = 0.53 n^2 \text{ Å}', 'Medium', 7, 7,
         'Energy levels, Spectral series (Lyman, Balmer, Paschen), Limitations',
         'Confusing absorption with emission spectra',
         'Energy is NEGATIVE (bound state). Transition to lower n = emission.'),
        ('Physics', 'Atoms & Nuclei', 'Nuclear Physics & Radioactivity',
         'Nuclear reactions involving binding energy, fission, fusion, and radioactive decay.',
         r'E = \Delta m \cdot c^2, \quad N = N_0 e^{-\lambda t}, \quad t_{1/2} = \frac{0.693}{\lambda}', 'Hard', 6, 7,
         'Mass defect, Binding energy curve, Alpha/Beta/Gamma decay',
         'Confusing fission with fusion; wrong mass number conservation',
         'Fission = heavy splits (U-235). Fusion = light combines (H to He). Both release energy!'),

        # Semiconductors
        ('Physics', 'Semiconductor Electronics', 'P-N Junction & Diodes',
         'Junction of p-type and n-type semiconductors creates a depletion region and one-way current flow.',
         r'I = I_0 \left(e^{eV/k_BT} - 1\right)', 'Medium', 6, 5,
         'Forward/reverse bias, Zener diode, LED, Photodiode',
         'Confusing forward bias (low resistance) with reverse bias',
         'Current flows easily in forward bias: P→N through external circuit.'),
    ]
    
    # ========================================================================
    # CHEMISTRY TOPICS (Class 12 NCERT + JEE)
    # ========================================================================
    chemistry_topics = [
        # Solutions
        ('Chemistry', 'Solutions', "Raoult's Law & Colligative Properties",
         'Vapour pressure of solution is proportional to mole fraction of solvent. Colligative properties depend on number of solute particles.',
         r"P = P^* \cdot x_{solvent}, \quad \Delta T_b = K_b \cdot m, \quad \Delta T_f = K_f \cdot m", 'Hard', 7, 8,
         "Raoult's law, Elevation in BP, Depression in FP, Osmotic pressure, Van't Hoff factor",
         'Forgetting to apply Van\'t Hoff factor for electrolytes',
         'For NaCl: i=2 (2 particles). For CaCl₂: i=3. Always multiply colligative property by i.'),

        # Electrochemistry
        ('Chemistry', 'Electrochemistry', 'Electrochemical Cells & Nernst Equation',
         'Galvanic cells convert chemical energy to electrical. Nernst equation gives EMF at non-standard conditions.',
         r'E_{cell} = E^\circ_{cell} - \frac{RT}{nF}\ln Q, \quad \Delta G = -nFE', 'Hard', 8, 9,
         'Electrode potentials, Conductivity, Faraday laws, Batteries',
         'Mixing up anode (oxidation) and cathode (reduction)',
         'AN OX, RED CAT — Anode=Oxidation, Reduction=Cathode. Always!'),
        ('Chemistry', 'Electrochemistry', 'Electrolysis & Faraday Laws',
         'Using electrical energy to drive non-spontaneous reactions. Amount of substance deposited proportional to charge.',
         r'm = \frac{M \cdot I \cdot t}{n \cdot F}, \quad F = 96500 \text{ C/mol}', 'Medium', 6, 6,
         'Faraday laws, Applications (electroplating, refining)',
         'Wrong value of n (charge on ion)',
         'n = number of electrons transferred per ion. For Cu²⁺, n=2.'),

        # Chemical Kinetics
        ('Chemistry', 'Chemical Kinetics', 'Rate Law & Order of Reaction',
         'Rate of reaction depends on concentration of reactants raised to a power (order).',
         r'r = k[A]^m[B]^n, \quad t_{1/2} = \frac{0.693}{k} \text{ (first order)}', 'Hard', 7, 8,
         'Zero, first, second order, Arrhenius equation, Activation energy',
         'Confusing order with molecularity; order from stoichiometry (wrong!)',
         'Order is EXPERIMENTAL, molecularity is THEORETICAL. Order can be fractional!'),
        ('Chemistry', 'Chemical Kinetics', 'Arrhenius Equation & Collision Theory',
         'Rate constant increases exponentially with temperature. Only molecules with E ≥ Ea react.',
         r'k = A \cdot e^{-E_a/RT}, \quad \ln\frac{k_2}{k_1} = \frac{E_a}{R}\left(\frac{1}{T_1} - \frac{1}{T_2}\right)', 'Hard', 5, 7,
         'Effect of temperature, Catalyst effect, Transition state',
         'Using wrong temperature units (must be Kelvin!)',
         'Catalyst lowers Ea but does NOT change ΔH. It speeds up both forward and reverse.'),

        # Coordination Compounds
        ('Chemistry', 'Coordination Compounds', 'Werner Theory & IUPAC Naming',
         'Coordination compounds have a central metal ion bonded to ligands. Named systematically by IUPAC rules.',
         r'[Co(NH_3)_6]^{3+}, \quad \text{Coordination number} = \text{number of bonds to metal}', 'Medium', 6, 7,
         'Ligands, Coordination number, Isomerism, IUPAC nomenclature',
         'Wrong naming order (ligands alphabetical, then metal)',
         'Name ligands alphabetically, then metal with oxidation state in Roman numerals.'),
        ('Chemistry', 'Coordination Compounds', 'Crystal Field Theory',
         'Ligands create an electrostatic field that splits d-orbitals of central metal. Explains color and magnetism.',
         r'\Delta_0 \text{ (octahedral splitting)}, \quad \text{CFSE} = (-0.4x + 0.6y)\Delta_0', 'Hard', 5, 8,
         'Crystal field splitting, Spectrochemical series, High/low spin',
         'Confusing t2g and eg in octahedral vs tetrahedral',
         'In octahedral: t2g is LOWER. In tetrahedral: e is LOWER. Δtet ≈ 4/9 Δoct.'),

        # Organic Chemistry
        ('Chemistry', 'Haloalkanes & Haloarenes', 'SN1 and SN2 Reactions',
         'Nucleophilic substitution: SN1 (2-step, via carbocation) and SN2 (1-step, backside attack).',
         r'\text{SN2: Rate} = k[R-X][Nu^-], \quad \text{SN1: Rate} = k[R-X]', 'Hard', 7, 9,
         'Mechanism, Stereochemistry, Reactivity order, Elimination competition',
         'Confusing SN1 (tertiary favored) with SN2 (primary favored)',
         'SN2: methyl > 1° > 2° (steric). SN1: 3° > 2° > 1° (carbocation stability).'),
        ('Chemistry', 'Haloalkanes & Haloarenes', 'Elimination Reactions',
         'Removal of HX to form alkene. E1 (2-step) and E2 (1-step, anti-periplanar).',
         r'\text{E2: anti-periplanar geometry required}', 'Hard', 5, 7,
         'Zaitsev rule, E1 vs E2, Competition with substitution',
         'Not applying Zaitsev rule (more substituted alkene is major)',
         'Strong bulky base = E2. Weak base + polar protic solvent = E1.'),

        ('Chemistry', 'Alcohols, Phenols & Ethers', 'Reactions of Alcohols',
         'Alcohols undergo oxidation, dehydration, esterification. Phenols are acidic due to resonance.',
         r'R-OH \xrightarrow{H_2SO_4} R=R + H_2O', 'Medium', 7, 6,
         'Lucas test, Oxidation series (1°→aldehyde→acid), Phenol acidity',
         'Confusing primary/secondary/tertiary alcohol reactions',
         'Lucas test: 3° = instant turbidity, 2° = 5 min, 1° = no reaction at RT.'),
        ('Chemistry', 'Aldehydes, Ketones & Carboxylic Acids', 'Nucleophilic Addition & Named Reactions',
         'Carbonyl group undergoes nucleophilic addition. Key named reactions for JEE.',
         r'R-CHO + HCN \rightarrow R-CH(OH)(CN)', 'Hard', 8, 9,
         'Aldol condensation, Cannizzaro, Tollen test, Fehling test',
         'Confusing which tests work for aldehydes vs ketones',
         'Tollen (silver mirror) and Fehling (red ppt) work for ALDEHYDES only, not ketones.'),

        ('Chemistry', 'Amines', 'Basicity & Reactions of Amines',
         'Amines are basic due to lone pair on N. Basicity: 2° > 1° > 3° (in aqueous).',
         r'R-NH_2 + HNO_2 \rightarrow R-OH + N_2 + H_2O \text{ (1° aliphatic)}', 'Medium', 6, 6,
         'Basicity order, Diazotization, Carbylamine test, Hoffmann bromamide',
         'Getting basicity order wrong in aqueous vs gas phase',
         'In water: 2° > 1° > 3° (solvation effect). In gas: 3° > 2° > 1° (pure induction).'),

        ('Chemistry', 'Biomolecules', 'Carbohydrates, Proteins & Nucleic Acids',
         'Biological macromolecules essential for life. Classification and properties.',
         r'\text{Glucose:} C_6H_{12}O_6, \quad \text{DNA: deoxyribose + ATGC}', 'Easy', 5, 3,
         'Monosaccharides, Amino acids, Peptide bond, DNA vs RNA',
         'Confusing D and L configuration with optical activity',
         'D/L is about configuration (Fischer projection), +/- is about optical rotation. Separate concepts!'),

        # Physical Chemistry
        ('Chemistry', 'Solid State', 'Crystal Structures & Defects',
         'Solids have ordered arrangements. Unit cells: SC, BCC, FCC, HCP.',
         r'\text{FCC: } Z=4, \quad \text{BCC: } Z=2, \quad \text{Packing fraction}_{FCC} = 74\%', 'Medium', 5, 6,
         'Unit cell calculations, Coordination number, Schottky/Frenkel defects',
         'Wrong Z value for different unit cells',
         'SC=1, BCC=2, FCC=4. Count: corners=1/8, edges=1/4, faces=1/2, body=1.'),

        ('Chemistry', 'Surface Chemistry', 'Adsorption & Colloids',
         'Adsorption is accumulation on surface. Colloids are intermediate-sized particles in a medium.',
         r'\frac{x}{m} = k \cdot P^{1/n} \text{ (Freundlich)}', 'Easy', 4, 4,
         'Physical vs chemical adsorption, Tyndall effect, Coagulation',
         'Confusing adsorption (surface) with absorption (bulk)',
         'Adsorption = surface phenomenon. Absorption = throughout bulk. Combined = sorption.'),
    ]

    # ========================================================================
    # MATHEMATICS TOPICS (Class 12 NCERT + JEE)
    # ========================================================================
    math_topics = [
        # Relations & Functions
        ('Mathematics', 'Relations & Functions', 'Types of Relations & Functions',
         'Relations can be reflexive, symmetric, transitive. Functions can be one-one, onto, or bijective.',
         r'\text{Bijective} = \text{one-one} + \text{onto}', 'Easy', 6, 5,
         'Equivalence relations, Injective/Surjective/Bijective, Composition',
         'Not checking all three conditions for equivalence relation',
         'For equivalence: check Reflexive (aRa), Symmetric (aRb→bRa), Transitive (aRb,bRc→aRc).'),
        ('Mathematics', 'Inverse Trigonometric Functions', 'Properties & Principal Values',
         'Inverse trig functions give angle for a given ratio. Domain restrictions ensure single-valued.',
         r'\sin^{-1}x + \cos^{-1}x = \frac{\pi}{2}, \quad \tan^{-1}x + \cot^{-1}x = \frac{\pi}{2}', 'Medium', 6, 7,
         'Principal value ranges, Important identities, Simplification',
         'Forgetting principal value range leads to wrong answers',
         'sin⁻¹: [-π/2, π/2], cos⁻¹: [0, π], tan⁻¹: (-π/2, π/2). MEMORIZE these!'),

        # Calculus
        ('Mathematics', 'Continuity & Differentiability', 'Limits, Continuity & Differentiability',
         'A function is continuous if limit equals function value. Differentiable if derivative exists.',
         r'\lim_{x \to a} f(x) = f(a), \quad f\'(x) = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}', 'Medium', 7, 7,
         'LHL=RHL condition, Differentiability implies continuity (not reverse), MVT',
         'Assuming continuity implies differentiability (|x| is continuous but not differentiable at 0)',
         'Differentiable ⊂ Continuous. Check both LHD and RHD at sharp points.'),
        ('Mathematics', 'Derivatives', 'Differentiation Techniques',
         'Rules for finding derivatives: chain rule, product rule, quotient rule, implicit differentiation.',
         r'\frac{d}{dx}[f(g(x))] = f\'(g(x)) \cdot g\'(x), \quad \frac{d}{dx}(uv) = uv\' + vu\'', 'Medium', 7, 8,
         'Chain rule, Logarithmic differentiation, Parametric differentiation',
         'Forgetting chain rule for composite functions',
         'When in doubt, use logarithmic differentiation for complex products/powers.'),
        ('Mathematics', 'Applications of Derivatives', 'Maxima, Minima & Rate of Change',
         'Derivatives find rate of change, tangent slopes, and optimize functions.',
         r"f'(x) = 0 \text{ (critical points)}, \quad f''(x) > 0 \text{ (minima)}, \quad f''(x) < 0 \text{ (maxima)}", 'Hard', 8, 9,
         'Increasing/decreasing, Local/Global extrema, Second derivative test',
         'Not checking endpoints for global max/min on closed intervals',
         'For optimization: 1) Define variable, 2) Write function, 3) Differentiate, 4) Check boundary too!'),
        ('Mathematics', 'Integrals', 'Indefinite Integration Techniques',
         'Reverse of differentiation. Key methods: substitution, partial fractions, by parts.',
         r'\int f(g(x))g\'(x)dx = F(g(x)) + C, \quad \int u \, dv = uv - \int v \, du', 'Hard', 8, 9,
         'Standard integrals, Substitution, Partial fractions, Integration by parts (ILATE)',
         'Choosing wrong method; forgetting +C in indefinite integrals',
         'Use ILATE for by-parts priority: Inverse trig > Log > Algebraic > Trig > Exponential.'),
        ('Mathematics', 'Integrals', 'Definite Integrals & Properties',
         'Integral with limits gives area under curve. Key properties simplify calculation.',
         r'\int_a^b f(x)dx = F(b) - F(a), \quad \int_0^a f(x)dx = \int_0^a f(a-x)dx', 'Hard', 7, 8,
         'Properties of definite integrals, Even/odd functions, Leibniz rule',
         'Not using properties (like f(a-x) substitution) to simplify',
         'Check if f(x) is even/odd first. Even: double the half-integral. Odd: answer is ZERO.'),
        ('Mathematics', 'Differential Equations', 'Formation & Solution of ODEs',
         'Equations involving derivatives. Solution methods: variable separable, linear, homogeneous.',
         r'\frac{dy}{dx} + P(x)y = Q(x), \quad \text{IF} = e^{\int P \, dx}', 'Hard', 7, 8,
         'Variable separable, Homogeneous, Linear first-order, Exact equations',
         'Not identifying the type correctly before solving',
         'Step 1: Identify type (separable? homogeneous? linear?). Step 2: Apply correct method.'),

        # Algebra
        ('Mathematics', 'Matrices & Determinants', 'Matrix Operations & Properties',
         'Rectangular array of numbers. Operations: addition, multiplication, transpose, inverse.',
         r'(AB)^{-1} = B^{-1}A^{-1}, \quad A \cdot A^{-1} = I', 'Medium', 7, 6,
         'Types of matrices, Multiplication, Inverse, Adjoint',
         'Multiplying matrices of incompatible dimensions; wrong transpose of product',
         'For AB to exist: cols(A) = rows(B). Result size: rows(A) × cols(B).'),
        ('Mathematics', 'Matrices & Determinants', 'Determinants & System of Equations',
         'Determinant is a scalar from square matrix. Used to solve systems via Cramer rule.',
         r'\det(AB) = \det(A) \cdot \det(B), \quad A^{-1} = \frac{1}{|A|} \text{adj}(A)', 'Medium', 7, 7,
         'Properties of determinants, Cofactors, Adjoint, Cramer rule',
         'Sign errors in cofactor expansion',
         'Cofactor sign: (-1)^(i+j). Expand along row/column with most zeros.'),

        # Vectors & 3D
        ('Mathematics', 'Vectors', 'Vector Algebra & Products',
         'Vectors have magnitude and direction. Dot product gives scalar, cross product gives vector.',
         r'\vec{a} \cdot \vec{b} = ab\cos\theta, \quad |\vec{a} \times \vec{b}| = ab\sin\theta', 'Medium', 7, 8,
         'Section formula, Dot product, Cross product, Scalar triple product',
         'Confusing dot (scalar result) with cross (vector result)',
         'Dot product: projection/work/angle. Cross product: area/torque/perpendicular vector.'),
        ('Mathematics', '3D Geometry', 'Lines & Planes in 3D',
         'Equations of lines and planes in space. Distance, angle, intersection formulas.',
         r'\frac{x-x_1}{a} = \frac{y-y_1}{b} = \frac{z-z_1}{c}, \quad \vec{r} \cdot \hat{n} = d', 'Hard', 7, 8,
         'Direction ratios, Distance from point to plane, Skew lines, Image of point',
         'Confusing direction ratios with direction cosines',
         'Direction cosines: l²+m²+n²=1 (unit). Direction ratios: any scalar multiple works.'),

        # Probability
        ('Mathematics', 'Probability', 'Conditional Probability & Bayes Theorem',
         'Probability of event given another has occurred. Bayes theorem reverses conditional probability.',
         r'P(A|B) = \frac{P(A \cap B)}{P(B)}, \quad P(A|B) = \frac{P(B|A) \cdot P(A)}{P(B)}', 'Hard', 8, 8,
         'Independent events, Multiplication rule, Total probability, Bayes theorem',
         'Confusing P(A∩B) with P(A|B); forgetting independence condition',
         'Independent: P(A∩B) = P(A)×P(B). If not independent, use P(A∩B) = P(A)×P(B|A).'),
        ('Mathematics', 'Probability', 'Random Variables & Distributions',
         'Random variable assigns numbers to outcomes. Binomial distribution for n independent trials.',
         r'P(X=r) = \binom{n}{r} p^r q^{n-r}, \quad E(X) = np, \quad \text{Var}(X) = npq', 'Medium', 6, 6,
         'Probability distribution, Mean, Variance, Binomial distribution',
         'Using wrong formula for combinations; confusing p and q',
         'Always check: p+q=1. Mean=np. For "at least one": P(X≥1) = 1-P(X=0).'),
    ]

    # Insert all topics
    all_topics = physics_topics + chemistry_topics + math_topics
    c.executemany("""
        INSERT INTO topics (subject, chapter, topic_name, description, formula_sheet, 
                           difficulty, cbse_weightage, jee_weightage, key_concepts, common_mistakes, tips) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, all_topics)

    conn.commit()

    # ========================================================================
    # QUESTIONS — 200+ exam-quality questions with detailed solutions
    # ========================================================================
    
    # Helper to get topic ID by name
    def get_tid(name):
        c.execute("SELECT id FROM topics WHERE topic_name=?", (name,))
        row = c.fetchone()
        return row[0] if row else None

    questions = []
    
    # --- PHYSICS QUESTIONS ---
    
    # Coulomb's Law
    tid = get_tid("Coulomb's Law")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Easy', 
             'Two charges of +2μC and +3μC are placed 30 cm apart in vacuum. Find the force between them.',
             json.dumps(['0.6 N', '0.3 N', '6 N', '0.06 N']), '0.6 N',
             'F = kq₁q₂/r². k=9×10⁹, q₁=2×10⁻⁶, q₂=3×10⁻⁶, r=0.3m. F = 9×10⁹ × 2×10⁻⁶ × 3×10⁻⁶ / 0.09 = 9×10⁹ × 6×10⁻¹² / 0.09 = 0.6 N',
             'Start by converting units: μC = 10⁻⁶ C, cm = 10⁻² m', None),
            (tid, 'Conceptual', 'Easy',
             'The electrostatic force between two charges is:',
             json.dumps(['A central force', 'A non-central force', 'Always attractive', 'Always repulsive']), 'A central force',
             'Electrostatic force acts along the line joining the centres of the two charges, making it a central force. It can be attractive (unlike charges) or repulsive (like charges).',
             'Think about the direction — along which line does the force act?', None),
            (tid, 'Numerical', 'Medium',
             'Two identical charges of q are placed at (0,0) and (3,4). Find the distance between them.',
             json.dumps(['5 units', '7 units', '1 unit', '25 units']), '5 units',
             'Distance = √((3-0)² + (4-0)²) = √(9+16) = √25 = 5 units. This is a 3-4-5 right triangle.',
             'Use the distance formula: d = √((x₂-x₁)² + (y₂-y₁)²)', None),
            (tid, 'Numerical', 'Hard',
             'Three charges +q, +q, and -q are at the vertices of an equilateral triangle of side a. Net force on -q is:',
             json.dumps(['kq²/a² along bisector', '√3 kq²/a² along bisector', 'kq²/a²', '2kq²/a²']), '√3 kq²/a² along bisector',
             'Force on -q due to each +q has magnitude kq²/a². The angle between these two forces is 60°. Resultant = √(F²+F²+2F²cos60°) = √(2F²+F²) = √3 F = √3 kq²/a², directed along the bisector.',
             'Draw the force vectors and use parallelogram law', None),
            (tid, 'Conceptual', 'Medium',
             'If the distance between two charges is halved, the force becomes:',
             json.dumps(['Double', 'Half', 'Four times', 'One-fourth']), 'Four times',
             'F ∝ 1/r². If r → r/2, then F → F×(r/(r/2))² = F×4. The force becomes 4 times.',
             'Think about the inverse square relationship', None),
        ])

    # Electric Field
    tid = get_tid("Electric Field & Field Lines")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Easy',
             'Electric field at 20 cm from a charge of 4μC in vacuum is:',
             json.dumps(['9×10⁵ N/C', '9×10⁴ N/C', '9×10³ N/C', '9×10⁶ N/C']), '9×10⁵ N/C',
             'E = kQ/r² = 9×10⁹ × 4×10⁻⁶ / (0.2)² = 9×10⁹ × 4×10⁻⁶ / 0.04 = 9×10⁵ N/C',
             'Convert all units to SI first', None),
            (tid, 'Conceptual', 'Easy',
             'Electric field lines:',
             json.dumps(['Never intersect each other', 'Always form closed loops', 'Start from negative charge', 'Can cross each other']),
             'Never intersect each other',
             'If field lines crossed, there would be two directions of electric field at that point, which is impossible. Field lines start from positive and end at negative charges.',
             'What would two directions of E at one point mean physically?', None),
            (tid, 'Numerical', 'Medium',
             'Electric field at a point on the axial line of a dipole at distance r >> l from center is:',
             json.dumps(['kp/r³', '2kp/r³', 'kp/r²', '2kp/r²']), '2kp/r³',
             'For an electric dipole with moment p, the axial field at large distance r is E = 2kp/r³ (along p direction). This is twice the equatorial field.',
             'Remember: axial field is twice the equatorial field', None),
        ])

    # Electric Potential
    tid = get_tid("Electric Potential & Potential Energy")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Medium',
             'Work done in moving a 2μC charge from a point at potential 100V to a point at 50V is:',
             json.dumps(['-100 μJ', '100 μJ', '-50 μJ', '50 μJ']), '-100 μJ',
             'W = q(V_A - V_B) = q(V_initial - V_final) = 2×10⁻⁶ × (100-50) = 100×10⁻⁶ J = 100 μJ. But conventionally W = q(V_final - V_initial) = 2×10⁻⁶(50-100) = -100 μJ.',
             'Which convention are we using? W by external agent or by field?', None),
            (tid, 'Conceptual', 'Easy',
             'An equipotential surface is:',
             json.dumps(['Always perpendicular to field lines', 'Always parallel to field lines', 'At 45° to field lines', 'Random orientation']),
             'Always perpendicular to field lines',
             'No work is done moving a charge along an equipotential surface. This means the field component along it is zero, so field must be perpendicular to it.',
             'What is the work done moving along an equipotential surface?', None),
        ])

    # Capacitance
    tid = get_tid("Capacitance & Capacitors")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Medium',
             'Two capacitors of 6μF and 3μF are connected in series. The equivalent capacitance is:',
             json.dumps(['2 μF', '9 μF', '4.5 μF', '1.5 μF']), '2 μF',
             '1/C_eq = 1/C₁ + 1/C₂ = 1/6 + 1/3 = 1/6 + 2/6 = 3/6 = 1/2. So C_eq = 2 μF.',
             'For series capacitors, use reciprocal formula (opposite of resistors!)', None),
            (tid, 'Numerical', 'Hard',
             'A parallel plate capacitor of capacitance C is charged to V and disconnected. If plates are separated to double the distance, the energy stored becomes:',
             json.dumps(['2CV²/2', 'CV²/4', 'CV²', 'CV²/2']), 'CV²',
             'When disconnected, Q is constant. C_new = C/2 (since d doubled). U = Q²/2C. Since C halved, U doubles. U_new = 2 × CV²/2 = CV².',
             'Is the capacitor connected to battery or disconnected?', None),
        ])

    # Ohm's Law
    tid = get_tid("Ohm's Law & Resistance")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Easy',
             'A wire of resistance 10Ω is stretched to double its length. Its new resistance is:',
             json.dumps(['20 Ω', '40 Ω', '5 Ω', '10 Ω']), '40 Ω',
             'When wire is stretched to double length, L→2L and A→A/2 (volume constant). R = ρL/A → ρ(2L)/(A/2) = 4ρL/A = 4R = 40Ω.',
             'Volume stays constant when stretched: V = L×A', None),
            (tid, 'Conceptual', 'Easy',
             'The resistivity of a conductor depends on:',
             json.dumps(['Material and temperature', 'Length of conductor', 'Area of cross-section', 'Shape of conductor']),
             'Material and temperature',
             'Resistivity (ρ) is a property of the material, not geometry. It depends on the nature of the material and its temperature. R = ρL/A shows R depends on L and A, but ρ itself does not.',
             'What is the difference between resistance and resistivity?', None),
        ])

    # Kirchhoff's Laws
    tid = get_tid("Kirchhoff's Laws")
    if tid:
        questions.extend([
            (tid, 'Conceptual', 'Medium',
             "Kirchhoff's junction rule is based on conservation of:",
             json.dumps(['Charge', 'Energy', 'Momentum', 'Mass']), 'Charge',
             "Junction rule states ΣI_in = ΣI_out at any junction. This is conservation of charge — charge cannot accumulate at a junction in steady state.",
             "Think about what physical quantity must be conserved at a junction", None),
            (tid, 'Numerical', 'Hard',
             'In a Wheatstone bridge, if P=100Ω, Q=150Ω, R=200Ω, then for balance, S equals:',
             json.dumps(['300 Ω', '250 Ω', '200 Ω', '150 Ω']), '300 Ω',
             'For balanced Wheatstone bridge: P/Q = R/S → 100/150 = 200/S → S = 200×150/100 = 300Ω.',
             'Write the balance condition: P/Q = R/S', None),
        ])

    # Magnetic Force
    tid = get_tid("Magnetic Force on Charges")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Medium',
             'An electron moving with velocity 10⁷ m/s enters a magnetic field of 0.1T perpendicular to it. The radius of circular path is: (m_e = 9.1×10⁻³¹ kg)',
             json.dumps(['5.7×10⁻⁴ m', '5.7×10⁻³ m', '5.7×10⁻² m', '5.7×10⁻⁵ m']), '5.7×10⁻⁴ m',
             'r = mv/qB = (9.1×10⁻³¹ × 10⁷)/(1.6×10⁻¹⁹ × 0.1) = 9.1×10⁻²⁴/1.6×10⁻²⁰ = 5.7×10⁻⁴ m',
             'For circular motion in B field: qvB = mv²/r → r = mv/qB', None),
            (tid, 'Conceptual', 'Easy',
             'A charged particle enters a uniform magnetic field parallel to the field lines. It will:',
             json.dumps(['Continue undeflected', 'Move in a circle', 'Move in a helix', 'Stop immediately']),
             'Continue undeflected',
             'F = qvBsinθ. When v is parallel to B, θ=0, so F=0. The particle continues in a straight line unaffected.',
             'What is sinθ when θ = 0?', None),
        ])

    # Faraday's Law
    tid = get_tid("Faraday's Law & Lenz's Law")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Medium',
             'Magnetic flux through a coil of 100 turns changes from 0.1 Wb to 0.3 Wb in 0.02s. The induced EMF is:',
             json.dumps(['1000 V', '500 V', '100 V', '10 V']), '1000 V',
             'ε = -N × dΦ/dt = -100 × (0.3-0.1)/0.02 = -100 × 0.2/0.02 = -100 × 10 = -1000 V. Magnitude = 1000V.',
             "Don't forget to multiply by number of turns N!", None),
            (tid, 'Conceptual', 'Easy',
             "According to Lenz's law, the direction of induced current is such that it:",
             json.dumps(['Opposes the change in flux', 'Supports the change in flux', 'Is perpendicular to flux', 'Is random']),
             'Opposes the change in flux',
             "Lenz's law is a consequence of conservation of energy. The induced current creates a magnetic field that opposes the change that caused it.",
             "Think of nature being 'lazy' — it resists change", None),
        ])

    # Photoelectric Effect
    tid = get_tid("Photoelectric Effect")
    if tid:
        questions.extend([
            (tid, 'Conceptual', 'Medium',
             'In photoelectric effect, if intensity of light is increased:',
             json.dumps(['Number of photoelectrons increases', 'KE of photoelectrons increases', 'Both increase', 'Neither changes']),
             'Number of photoelectrons increases',
             'Intensity means more photons per second → more electrons ejected → more photocurrent. But each photon has same energy (hν), so KE_max remains same.',
             'Intensity = number of photons. Frequency = energy per photon.', None),
            (tid, 'Numerical', 'Hard',
             'The work function of a metal is 2.5 eV. Find the maximum KE of photoelectrons when light of wavelength 200 nm falls on it. (h=6.63×10⁻³⁴ J·s, c=3×10⁸ m/s)',
             json.dumps(['3.7 eV', '2.5 eV', '6.2 eV', '1.2 eV']), '3.7 eV',
             'E = hc/λ = (6.63×10⁻³⁴ × 3×10⁸)/(200×10⁻⁹) = 9.95×10⁻¹⁹ J = 6.2 eV. KE_max = E - φ = 6.2 - 2.5 = 3.7 eV.',
             'Use Einstein equation: KE_max = hν - φ = hc/λ - φ', None),
        ])

    # Bohr Model
    tid = get_tid("Bohr's Model & Hydrogen Spectrum")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Medium',
             'The energy of electron in the 3rd orbit of hydrogen atom is:',
             json.dumps(['-1.51 eV', '-3.4 eV', '-13.6 eV', '-0.85 eV']), '-1.51 eV',
             'E_n = -13.6/n² eV. For n=3: E₃ = -13.6/9 = -1.51 eV.',
             'Just plug n=3 into the energy formula', None),
            (tid, 'Conceptual', 'Easy',
             'The Balmer series of hydrogen spectrum lies in the:',
             json.dumps(['Visible region', 'UV region', 'Infrared region', 'X-ray region']),
             'Visible region',
             'Balmer series: transitions to n=2. These wavelengths (400-700 nm) fall in visible region. Lyman→UV, Paschen→IR.',
             'Remember: Lyman=UV, Balmer=Visible, Paschen/Brackett/Pfund=IR', None),
        ])

    # --- CHEMISTRY QUESTIONS ---
    
    # Raoult's Law
    tid = get_tid("Raoult's Law & Colligative Properties")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Medium',
             'The boiling point elevation of a 0.1m aqueous NaCl solution (Kb=0.52 K·kg/mol) is approximately:',
             json.dumps(['0.052 K', '0.104 K', '0.156 K', '0.52 K']), '0.104 K',
             'NaCl → Na⁺ + Cl⁻, so i=2. ΔTb = i·Kb·m = 2 × 0.52 × 0.1 = 0.104 K.',
             "Don't forget the Van't Hoff factor for electrolytes!", None),
            (tid, 'Conceptual', 'Easy',
             'Which of the following is NOT a colligative property?',
             json.dumps(['Optical activity', 'Osmotic pressure', 'Elevation of boiling point', 'Depression of freezing point']),
             'Optical activity',
             'Colligative properties depend on NUMBER of solute particles, not their nature. Optical activity depends on the nature of solute.',
             'Colligative = depends on count of particles, not identity', None),
        ])

    # Electrochemistry
    tid = get_tid("Electrochemical Cells & Nernst Equation")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Hard',
             'For the cell Zn|Zn²⁺(0.01M)||Cu²⁺(1M)|Cu, if E°cell = 1.10V, the EMF at 25°C is:',
             json.dumps(['1.159 V', '1.041 V', '1.10 V', '0.90 V']), '1.159 V',
             'Ecell = E° - (0.059/n)log(Q). Q = [Zn²⁺]/[Cu²⁺] = 0.01/1 = 0.01. n=2. Ecell = 1.10 - (0.059/2)log(0.01) = 1.10 - (0.0295)(-2) = 1.10 + 0.059 = 1.159 V.',
             'Write the cell reaction first, then identify Q = products/reactants for ions', None),
            (tid, 'Conceptual', 'Easy',
             'In a galvanic cell, oxidation occurs at the:',
             json.dumps(['Anode', 'Cathode', 'Salt bridge', 'Both electrodes']), 'Anode',
             'AN OX, RED CAT — Anode = Oxidation, Cathode = Reduction. In galvanic cell, anode is negative terminal.',
             'Remember the mnemonic: AN OX RED CAT', None),
        ])

    # Chemical Kinetics
    tid = get_tid("Rate Law & Order of Reaction")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Medium',
             'The half-life of a first-order reaction is 693 seconds. The rate constant is:',
             json.dumps(['10⁻³ s⁻¹', '10⁻² s⁻¹', '10⁻⁴ s⁻¹', '0.693 s⁻¹']), '10⁻³ s⁻¹',
             'For first order: t₁/₂ = 0.693/k → k = 0.693/693 = 10⁻³ s⁻¹.',
             't₁/₂ = 0.693/k is ONLY for first-order reactions', None),
            (tid, 'Conceptual', 'Medium',
             'For a zero-order reaction, the plot of [A] vs time is:',
             json.dumps(['A straight line with negative slope', 'An exponential curve', 'A parabola', 'A horizontal line']),
             'A straight line with negative slope',
             'For zero order: [A] = [A]₀ - kt. This is y = mx + c with m = -k. Linear decrease.',
             'Write the integrated rate law and compare with y = mx + c', None),
        ])

    # SN1/SN2
    tid = get_tid("SN1 and SN2 Reactions")
    if tid:
        questions.extend([
            (tid, 'Conceptual', 'Medium',
             'SN2 reaction is favored by:',
             json.dumps(['Primary substrate + strong nucleophile', 'Tertiary substrate + weak nucleophile', 'Tertiary substrate + polar protic solvent', 'Any substrate in water']),
             'Primary substrate + strong nucleophile',
             'SN2 is a one-step bimolecular reaction. Primary substrates have less steric hindrance. Strong nucleophiles attack effectively. Polar aprotic solvents are best.',
             'SN2 needs: low steric hindrance (1°) + strong nucleophile + polar aprotic solvent', None),
            (tid, 'Conceptual', 'Hard',
             'The stereochemical outcome of SN2 reaction is:',
             json.dumps(['Inversion of configuration', 'Retention of configuration', 'Racemization', 'No change']),
             'Inversion of configuration',
             'SN2 involves backside attack by nucleophile. This causes Walden inversion — the configuration at the carbon center is inverted (like an umbrella flipping).',
             'Think of an umbrella being turned inside out by wind', None),
        ])

    # Aldehydes/Ketones
    tid = get_tid("Nucleophilic Addition & Named Reactions")
    if tid:
        questions.extend([
            (tid, 'Conceptual', 'Medium',
             "Tollen's reagent gives a positive test (silver mirror) with:",
             json.dumps(['Aldehydes', 'Ketones', 'Both', 'Neither']), 'Aldehydes',
             "Tollen's reagent (ammoniacal AgNO₃) oxidizes aldehydes to carboxylate and Ag⁺ is reduced to metallic silver (mirror). Ketones cannot be oxidized by mild oxidizing agents.",
             'Which carbonyl compound can be oxidized more easily?', None),
            (tid, 'Conceptual', 'Hard',
             'Aldol condensation requires:',
             json.dumps(['α-hydrogen in aldehyde/ketone', 'No α-hydrogen', 'Aromatic ring', 'Grignard reagent']),
             'α-hydrogen in aldehyde/ketone',
             'Aldol condensation needs α-hydrogen to form enolate ion, which acts as nucleophile and attacks the carbonyl of another molecule. Formaldehyde (no α-H) undergoes Cannizzaro instead.',
             'What acts as the nucleophile in aldol condensation?', None),
        ])

    # --- MATHEMATICS QUESTIONS ---
    
    # Limits & Continuity
    tid = get_tid("Limits, Continuity & Differentiability")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Medium',
             'The value of lim(x→0) [sin(3x)/x] is:',
             json.dumps(['3', '1', '0', '∞']), '3',
             'lim(x→0) sin(3x)/x = lim(x→0) 3·sin(3x)/(3x) = 3×1 = 3. Using standard limit: lim(θ→0) sinθ/θ = 1.',
             'Multiply and divide by 3 to use the standard limit sinθ/θ → 1', None),
            (tid, 'Conceptual', 'Medium',
             'f(x) = |x| is:',
             json.dumps(['Continuous but not differentiable at x=0', 'Both continuous and differentiable at x=0', 'Neither continuous nor differentiable', 'Differentiable but not continuous']),
             'Continuous but not differentiable at x=0',
             '|x| has no break at x=0 (continuous), but has a sharp corner (not differentiable). LHD = -1, RHD = +1, they are not equal.',
             'Differentiability requires a smooth curve — no sharp corners!', None),
        ])

    # Derivatives
    tid = get_tid("Differentiation Techniques")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Easy',
             'If y = x³ + 2x² - 5x + 7, then dy/dx at x=1 is:',
             json.dumps(['2', '0', '7', '-2']), '2',
             "dy/dx = 3x² + 4x - 5. At x=1: dy/dx = 3(1) + 4(1) - 5 = 3 + 4 - 5 = 2.",
             'Differentiate each term using power rule: d/dx(xⁿ) = nxⁿ⁻¹', None),
            (tid, 'Numerical', 'Medium',
             'If y = sin(x²), then dy/dx is:',
             json.dumps(['2x·cos(x²)', 'cos(x²)', '2x·sin(x²)', 'x²·cos(x²)']), '2x·cos(x²)',
             'Using chain rule: dy/dx = cos(x²) · d/dx(x²) = cos(x²) · 2x = 2x·cos(x²).',
             'Apply chain rule: differentiate outer function, then multiply by derivative of inner', None),
        ])

    # Maxima/Minima
    tid = get_tid("Maxima, Minima & Rate of Change")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Hard',
             'The maximum value of f(x) = 2x³ - 9x² + 12x + 5 on [0, 3] is:',
             json.dumps(['10', '5', '8', '14']), '10',
             "f'(x) = 6x² - 18x + 12 = 6(x²-3x+2) = 6(x-1)(x-2). Critical points: x=1 and x=2. f(0)=5, f(1)=10, f(2)=9, f(3)=14. Wait, f(3)=2(27)-9(9)+12(3)+5=54-81+36+5=14. Maximum = 14.",
             'Check BOTH critical points AND endpoints on a closed interval', None),
            (tid, 'Conceptual', 'Medium',
             'If f\'(a) = 0 and f\'\'(a) > 0, then x = a is a point of:',
             json.dumps(['Local minimum', 'Local maximum', 'Inflection', 'Saddle point']), 'Local minimum',
             "Second derivative test: f''(a) > 0 means the function curves upward at x=a, so it's a local minimum (like a valley). f''(a) < 0 would be maximum (like a hilltop).",
             'f\'\' > 0 = concave up = valley = minimum', None),
        ])

    # Integration
    tid = get_tid("Indefinite Integration Techniques")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Medium',
             '∫ x·eˣ dx equals:',
             json.dumps(['eˣ(x-1) + C', 'x·eˣ + C', 'eˣ(x+1) + C', 'eˣ/x + C']), 'eˣ(x-1) + C',
             'Using integration by parts (ILATE: x is Algebraic, eˣ is Exponential). u=x, dv=eˣdx. ∫x·eˣdx = x·eˣ - ∫eˣdx = x·eˣ - eˣ + C = eˣ(x-1) + C.',
             'Use ILATE rule: I > L > A > T > E for choosing u', None),
            (tid, 'Numerical', 'Hard',
             '∫ 1/(x² + 4) dx equals:',
             json.dumps(['(1/2)tan⁻¹(x/2) + C', 'tan⁻¹(x/2) + C', '(1/4)tan⁻¹(x/2) + C', 'ln(x²+4) + C']),
             '(1/2)tan⁻¹(x/2) + C',
             '∫ 1/(x²+a²) dx = (1/a)tan⁻¹(x/a) + C. Here a²=4, a=2. Answer = (1/2)tan⁻¹(x/2) + C.',
             'Use standard form: ∫1/(x²+a²)dx = (1/a)tan⁻¹(x/a) + C', None),
        ])

    # Definite Integrals
    tid = get_tid("Definite Integrals & Properties")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Medium',
             '∫₀^π sin(x) dx equals:',
             json.dumps(['2', '0', '1', 'π']), '2',
             '∫₀^π sinx dx = [-cosx]₀^π = -cosπ - (-cos0) = -(-1) - (-1) = 1 + 1 = 2.',
             'Integrate sinx to get -cosx, then apply limits', None),
            (tid, 'Conceptual', 'Medium',
             '∫₋ₐ^a f(x)dx = 0 if f(x) is:',
             json.dumps(['Odd function', 'Even function', 'Any function', 'Periodic function']), 'Odd function',
             'For odd function f(-x) = -f(x), the areas on left and right of origin cancel out. For even function, the integral doubles.',
             'Think about symmetry: does the area cancel or double?', None),
        ])

    # Vectors
    tid = get_tid("Vector Algebra & Products")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Medium',
             'If |a⃗| = 3, |b⃗| = 4, and a⃗·b⃗ = 6, then the angle between them is:',
             json.dumps(['60°', '30°', '45°', '90°']), '60°',
             'a⃗·b⃗ = |a⃗||b⃗|cosθ → 6 = 3×4×cosθ → cosθ = 6/12 = 1/2 → θ = 60°.',
             'Use the definition: a⃗·b⃗ = |a⃗||b⃗|cosθ and solve for θ', None),
            (tid, 'Conceptual', 'Easy',
             'The cross product a⃗ × b⃗ is:',
             json.dumps(['Perpendicular to both a⃗ and b⃗', 'Parallel to a⃗', 'In the plane of a⃗ and b⃗', 'Equal to b⃗ × a⃗']),
             'Perpendicular to both a⃗ and b⃗',
             'Cross product gives a vector perpendicular to both input vectors. Its magnitude = |a⃗||b⃗|sinθ = area of parallelogram.',
             'Cross product gives a vector that points "out" of the plane formed by a⃗ and b⃗', None),
        ])

    # Probability
    tid = get_tid("Conditional Probability & Bayes Theorem")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Hard',
             'A bag has 3 red and 2 blue balls. Two balls are drawn without replacement. P(2nd is red | 1st is red) is:',
             json.dumps(['2/4 = 1/2', '3/5', '2/5', '3/4']), '2/4 = 1/2',
             'Given 1st is red, remaining: 2 red + 2 blue = 4 balls. P(2nd red | 1st red) = 2/4 = 1/2.',
             'After 1st red is drawn, update the counts: how many red and total balls remain?', None),
            (tid, 'Numerical', 'Medium',
             'If P(A) = 0.4, P(B) = 0.5, and P(A∩B) = 0.2, then P(A|B) is:',
             json.dumps(['0.4', '0.5', '0.2', '0.8']), '0.4',
             'P(A|B) = P(A∩B)/P(B) = 0.2/0.5 = 0.4.',
             'Direct formula: P(A|B) = P(A∩B)/P(B)', None),
        ])

    # Matrices
    tid = get_tid("Matrix Operations & Properties")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Easy',
             'If A is a 3×2 matrix and B is a 2×4 matrix, then AB is:',
             json.dumps(['3×4 matrix', '2×2 matrix', '4×3 matrix', 'Not possible']), '3×4 matrix',
             'For matrix multiplication AB: A is m×n, B is n×p → AB is m×p. Here 3×2 and 2×4 → 3×4.',
             'Columns of A must equal rows of B. Result: rows(A) × cols(B)', None),
            (tid, 'Conceptual', 'Medium',
             'If A is a non-singular matrix, then:',
             json.dumps(['|A| ≠ 0 and A⁻¹ exists', '|A| = 0', 'A has no inverse', 'A must be symmetric']),
             '|A| ≠ 0 and A⁻¹ exists',
             'Non-singular = determinant is non-zero = inverse exists. Singular matrix has |A|=0 and no inverse.',
             'Non-singular ↔ |A| ≠ 0 ↔ A⁻¹ exists. All three go together.', None),
        ])

    # 3D Geometry
    tid = get_tid("Lines & Planes in 3D")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Medium',
             'The distance of the point (2, 3, -5) from the plane x + 2y - 2z = 9 is:',
             json.dumps(['3 units', '5 units', '2 units', '4 units']), '3 units',
             'd = |ax₁+by₁+cz₁-d|/√(a²+b²+c²) = |1(2)+2(3)-2(-5)-9|/√(1+4+4) = |2+6+10-9|/√9 = |9|/3 = 3.',
             'Use the point-to-plane distance formula', None),
        ])

    # Binomial Distribution
    tid = get_tid("Random Variables & Distributions")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Medium',
             'A coin is tossed 6 times. The probability of getting exactly 2 heads is:',
             json.dumps(['15/64', '6/64', '1/64', '20/64']), '15/64',
             'P(X=2) = C(6,2)×(1/2)²×(1/2)⁴ = 15 × 1/4 × 1/16 = 15/64.',
             'Use binomial formula: P(X=r) = C(n,r)×pʳ×qⁿ⁻ʳ', None),
            (tid, 'Numerical', 'Easy',
             'For a binomial distribution with n=10 and p=0.3, the mean is:',
             json.dumps(['3', '7', '0.3', '10']), '3',
             'Mean = np = 10 × 0.3 = 3.',
             'Mean of binomial = np. Simple multiplication!', None),
        ])

    # Nuclear Physics
    tid = get_tid("Nuclear Physics & Radioactivity")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Medium',
             'The half-life of a radioactive substance is 20 days. The fraction remaining after 60 days is:',
             json.dumps(['1/8', '1/4', '1/6', '1/3']), '1/8',
             'Number of half-lives = 60/20 = 3. Fraction remaining = (1/2)³ = 1/8.',
             'Count the number of half-lives, then apply (1/2)ⁿ', None),
        ])

    # P-N Junction
    tid = get_tid("P-N Junction & Diodes")
    if tid:
        questions.extend([
            (tid, 'Conceptual', 'Easy',
             'In forward bias of a p-n junction:',
             json.dumps(['P is connected to +ve terminal', 'N is connected to +ve terminal', 'Both are at same potential', 'No current flows']),
             'P is connected to +ve terminal',
             'Forward bias: P-side to +ve, N-side to -ve. This reduces depletion width and allows current flow.',
             'Forward = P to positive (same letter P!)', None),
        ])

    # Gauss's Law
    tid = get_tid("Gauss's Law")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Hard',
             'Electric flux through a sphere of radius R with charge Q at its center is:',
             json.dumps(['Q/ε₀', 'Q/(4πε₀R²)', '4πR²·Q/ε₀', 'Q·R/ε₀']), 'Q/ε₀',
             "By Gauss's law, total flux = Q_enclosed/ε₀ = Q/ε₀. It does NOT depend on radius of the Gaussian surface!",
             "Gauss's law: flux depends only on enclosed charge, not on radius", None),
        ])

    # Refraction
    tid = get_tid("Refraction & Lenses")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Medium',
             'A thin convex lens of focal length 20 cm forms an image at 60 cm on the other side. The object distance is:',
             json.dumps(['-30 cm', '-20 cm', '-60 cm', '-40 cm']), '-30 cm',
             '1/v - 1/u = 1/f. v=+60cm, f=+20cm. 1/60 - 1/u = 1/20 → 1/u = 1/60 - 1/20 = 1/60 - 3/60 = -2/60 → u = -30cm.',
             'Use lens formula (not mirror formula!) with proper sign convention', None),
        ])

    # YDSE
    tid = get_tid("Young's Double Slit Experiment")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Medium',
             'In YDSE, if d=0.1mm, D=1m, λ=600nm, the fringe width is:',
             json.dumps(['6 mm', '0.6 mm', '0.06 mm', '60 mm']), '6 mm',
             'β = λD/d = 600×10⁻⁹ × 1 / (0.1×10⁻³) = 6×10⁻³ m = 6 mm.',
             'Fringe width β = λD/d. Convert all to meters first!', None),
        ])

    # AC Circuits
    tid = get_tid("AC Circuits & Transformers")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Medium',
             'A step-down transformer converts 220V to 22V. If primary has 1000 turns, secondary has:',
             json.dumps(['100 turns', '10000 turns', '10 turns', '500 turns']), '100 turns',
             'Vs/Vp = Ns/Np → 22/220 = Ns/1000 → Ns = 100 turns.',
             'Use transformer ratio: Vs/Vp = Ns/Np', None),
        ])

    # Crystal Field Theory
    tid = get_tid("Crystal Field Theory")
    if tid:
        questions.extend([
            (tid, 'Conceptual', 'Hard',
             'In an octahedral complex, the d-orbital splitting gives:',
             json.dumps(['t2g (lower) and eg (higher)', 'eg (lower) and t2g (higher)', 'All five at same level', 't2g and eg at same level']),
             't2g (lower) and eg (higher)',
             'In octahedral field, dxy, dyz, dzx (t2g) point between axes → less repulsion from ligands → lower energy. dx²-y², dz² (eg) point along axes → more repulsion → higher energy.',
             'Which d-orbitals point directly at the ligands on the axes?', None),
        ])

    # Differential Equations
    tid = get_tid("Formation & Solution of ODEs")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Medium',
             'The integrating factor of dy/dx + 2y = eˣ is:',
             json.dumps(['e²ˣ', 'eˣ', 'e⁻²ˣ', '2x']), 'e²ˣ',
             'This is linear: dy/dx + P(x)y = Q(x) where P(x)=2. IF = e^(∫P dx) = e^(∫2 dx) = e²ˣ.',
             'IF = e^(∫P(x)dx). Identify P(x) = coefficient of y.', None),
        ])

    # Inverse Trigonometric
    tid = get_tid("Properties & Principal Values")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Easy',
             'The value of sin⁻¹(1/2) + cos⁻¹(1/2) is:',
             json.dumps(['π/2', 'π', '0', 'π/3']), 'π/2',
             'By the identity: sin⁻¹(x) + cos⁻¹(x) = π/2 for all x ∈ [-1,1]. So answer = π/2.',
             'Use the identity directly — no calculation needed!', None),
        ])

    # Determinants
    tid = get_tid("Determinants & System of Equations")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Medium',
             'If |A| = 5 for a 3×3 matrix, then |3A| equals:',
             json.dumps(['135', '15', '45', '125']), '135',
             '|kA| = kⁿ|A| for n×n matrix. |3A| = 3³ × 5 = 27 × 5 = 135.',
             'When you multiply a matrix by k, each of n rows gets multiplied by k → det gets kⁿ', None),
        ])

    # Amines
    tid = get_tid("Basicity & Reactions of Amines")
    if tid:
        questions.extend([
            (tid, 'Conceptual', 'Medium',
             'Carbylamine test is given by:',
             json.dumps(['Primary amines', 'Secondary amines', 'Tertiary amines', 'All amines']),
             'Primary amines',
             'Carbylamine (isocyanide) test: R-NH₂ + CHCl₃ + 3KOH → R-NC (bad smell) + 3KCl + 3H₂O. Only 1° amines have the required N-H₂ group.',
             'Think about which amines still have H atoms on nitrogen', None),
        ])

    # Surface Chemistry
    tid = get_tid("Adsorption & Colloids")
    if tid:
        questions.extend([
            (tid, 'Conceptual', 'Easy',
             'Tyndall effect is shown by:',
             json.dumps(['Colloids', 'True solutions', 'Both', 'Neither']),
             'Colloids',
             'Tyndall effect is scattering of light by colloidal particles (1-1000 nm). True solutions have particles too small to scatter light.',
             'Think about particle size — which is big enough to scatter light?', None),
        ])

    # EMF & Internal Resistance
    tid = get_tid("EMF & Internal Resistance")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Medium',
             'A cell of EMF 2V and internal resistance 0.5Ω is connected to a 1.5Ω external resistance. The current is:',
             json.dumps(['1 A', '2 A', '0.5 A', '4 A']), '1 A',
             'I = ε/(R+r) = 2/(1.5+0.5) = 2/2 = 1 A.',
             'Total resistance = external + internal', None),
        ])

    # Electrolysis
    tid = get_tid("Electrolysis & Faraday Laws")
    if tid:
        questions.extend([
            (tid, 'Numerical', 'Medium',
             'How many grams of copper are deposited by passing 2A current for 965 seconds through CuSO₄ solution? (Atomic mass Cu=63.5, F=96500)',
             json.dumps(['0.635 g', '1.27 g', '6.35 g', '0.3175 g']), '0.635 g',
             'm = MIt/nF = 63.5 × 2 × 965 / (2 × 96500) = 122555/193000 = 0.635 g.',
             'n = 2 for Cu²⁺ (needs 2 electrons per ion)', None),
        ])

    # Solid State
    tid = get_tid("Crystal Structures & Defects")
    if tid:
        questions.extend([
            (tid, 'Conceptual', 'Medium',
             'The number of atoms per unit cell in FCC is:',
             json.dumps(['4', '2', '1', '6']), '4',
             'FCC: 8 corners × 1/8 = 1 atom + 6 faces × 1/2 = 3 atoms. Total = 4 atoms per unit cell.',
             'Count: corners share with 8 cells, faces share with 2 cells', None),
        ])

    # Alcohols
    tid = get_tid("Reactions of Alcohols")
    if tid:
        questions.extend([
            (tid, 'Conceptual', 'Easy',
             'Lucas test gives instant turbidity with:',
             json.dumps(['Tertiary alcohols', 'Primary alcohols', 'Secondary alcohols', 'Methanol']),
             'Tertiary alcohols',
             'Lucas reagent (conc. HCl + anhydrous ZnCl₂) reacts fastest with 3° alcohols (immediate turbidity due to alkyl chloride formation), 2° (5 min), 1° (no reaction at RT).',
             'Stability of carbocation: 3° > 2° > 1°', None),
        ])

    # Biomolecules
    tid = get_tid("Carbohydrates, Proteins & Nucleic Acids")
    if tid:
        questions.extend([
            (tid, 'Conceptual', 'Easy',
             'DNA contains which sugar?',
             json.dumps(['Deoxyribose', 'Ribose', 'Glucose', 'Fructose']),
             'Deoxyribose',
             'DNA = DeoxyriboNucleic Acid → contains deoxyribose sugar. RNA contains ribose sugar. The "deoxy" means one oxygen is missing.',
             'The name tells you! D = Deoxy', None),
        ])

    # Relations & Functions
    tid = get_tid("Types of Relations & Functions")
    if tid:
        questions.extend([
            (tid, 'Conceptual', 'Medium',
             'A relation R on set A is an equivalence relation if it is:',
             json.dumps(['Reflexive, symmetric, and transitive', 'Only reflexive and symmetric', 'Only symmetric and transitive', 'Only reflexive']),
             'Reflexive, symmetric, and transitive',
             'All THREE conditions must hold for equivalence relation. Missing even one disqualifies it.',
             'Remember RST: Reflexive + Symmetric + Transitive = Equivalence', None),
        ])

    # Insert all questions
    if questions:
        c.executemany("""
            INSERT INTO questions (topic_id, q_type, difficulty, question_text, options, correct_option, solution_text, hint, pyq_year)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, questions)

    conn.commit()
    conn.close()



def populate_extra_questions():
    """Add questions for topics with fewer than 3. Safe to call repeatedly."""
    conn = get_connection()
    c = conn.cursor()

    def get_tid(name):
        c.execute("SELECT id FROM topics WHERE topic_name=?", (name,))
        row = c.fetchone()
        return row[0] if row else None

    def needs_more(tid, min_count=3):
        if tid is None:
            return False
        c.execute("SELECT COUNT(*) FROM questions WHERE topic_id=?", (tid,))
        return c.fetchone()[0] < min_count

    questions = []

    # Biot-Savart & Ampere Law
    tid = get_tid("Biot-Savart & Ampere Law")
    if needs_more(tid):
        questions.extend([
            (tid,'Numerical','Easy','Find the magnetic field at the centre of a circular loop of radius 0.1 m carrying current 5 A.',
             json.dumps(['pi x10^-5 T','10pi uT','5pi x10^-5 T','2pi x10^-5 T']),'5pi x10^-5 T',
             'B = u0*I/2r = (4pi*10^-7 * 5)/(2*0.1) = 5pi*10^-5 T approx 31.4 uT.',
             'Formula for centre of circular loop: B = u0*I / 2r',None),
            (tid,'Conceptual','Easy','According to Biot-Savart law, dB due to a current element is proportional to:',
             json.dumps(['I dl sin(theta) / r^2','I dl / r','I dl cos(theta) / r^2','I / r^2']),'I dl sin(theta) / r^2',
             'dB = (u0/4pi)(I dl sin(theta))/r^2. Field depends on I, dl, sin(theta) and 1/r^2.',
             'Think of the cross-product form: dB proportional to I dl x r_hat',None),
            (tid,'Numerical','Medium','A long straight wire carries 10 A. Find the magnetic field 2 cm from it.',
             json.dumps(['10^-4 T','10^-3 T','10^-5 T','2x10^-4 T']),'10^-4 T',
             'B = u0*I/(2*pi*r) = (4pi*10^-7 * 10)/(2pi * 0.02) = 10^-4 T.',
             "Use Ampere's law for infinite straight wire: B = u0*I/2*pi*r",None),
            (tid,'Conceptual','Medium',"Ampere's circuital law: the line integral of B around a closed loop equals:",
             json.dumps(['u0 x enclosed current','u0*e0 x enclosed current','enclosed current / u0','Zero always']),'u0 x enclosed current',
             'Integral B.dl = u0 * I_enclosed. Only the current inside the loop matters.',
             'Remember: enclosed current only',None),
            (tid,'Numerical','Hard','A solenoid: 500 turns, length 0.5 m, carries 2 A. Find B inside.',
             json.dumps(['8pi x10^-4 T','4pi x10^-4 T','2pi x10^-4 T','16pi x10^-4 T']),'8pi x10^-4 T',
             'n = N/L = 1000 turns/m. B = u0*n*I = 4pi*10^-7 * 1000 * 2 = 8pi*10^-4 T.',
             'For solenoid: B = u0*n*I where n = N/L',None),
        ])

    # Reflection & Mirrors
    tid = get_tid("Reflection & Mirrors")
    if needs_more(tid):
        questions.extend([
            (tid,'Numerical','Easy','Object 30 cm from concave mirror, f=10 cm. Image distance:',
             json.dumps(['-15 cm','15 cm','-10 cm','10 cm']),'-15 cm',
             '1/v + 1/u = 1/f. u=-30, f=-10. 1/v = -1/10 + 1/30 = -2/30. v=-15 cm (real image).',
             'Sign convention: object on left is negative',None),
            (tid,'Conceptual','Easy','A convex mirror always forms an image that is:',
             json.dumps(['Virtual, erect, diminished','Real, inverted, magnified','Virtual, inverted, magnified','Real, erect, diminished']),
             'Virtual, erect, diminished',
             'Convex mirror (diverging) always forms virtual, erect, diminished images. Used as rear-view mirror.',
             'Convex mirror = diverging = always virtual and erect',None),
            (tid,'Numerical','Medium','Magnification=-3, image distance=45 cm. Object distance:',
             json.dumps(['15 cm','-15 cm','45 cm','-45 cm']),'15 cm',
             'm = -v/u. -3 = -(-45)/u. u = -15 cm. Object is 15 cm in front.',
             'Magnification m = -v/u. Negative m means inverted image.',None),
            (tid,'Conceptual','Medium','Ray parallel to principal axis of concave mirror reflects through:',
             json.dumps(['The focus','The centre of curvature','The pole','Infinity']),'The focus',
             'By definition of focus: parallel rays converge at focus after reflection.',
             'Defining property of focal point',None),
        ])

    # Gauss's Law
    tid = get_tid("Gauss's Law")
    if needs_more(tid):
        questions.extend([
            (tid,'Conceptual','Easy',"Gauss's Law relates electric flux through a closed surface to:",
             json.dumps(['Enclosed charge / e0','Enclosed charge x e0','Surface area x E','Total charge']),'Enclosed charge / e0',
             'Flux = Q_enclosed / e0. Only the charge inside the Gaussian surface matters.',
             'Flux = Q_in / e0',None),
            (tid,'Numerical','Medium','Sphere of radius 10 cm, charge 8.85 nC. Electric field at its surface:',
             json.dumps(['8.85 kN/C','8.85 N/C','88500 N/C','88.5 kN/C']),'8.85 kN/C',
             'E = kQ/r^2 = 9e9 * 8.85e-9 / 0.01 = 8850 N/C = 8.85 kN/C.',
             'For charged sphere, treat as point charge outside',None),
        ])

    # EMF & Internal Resistance
    tid = get_tid("EMF & Internal Resistance")
    if needs_more(tid):
        questions.extend([
            (tid,'Numerical','Easy','Battery: EMF=12V, r=2 ohm, external R=10 ohm. Terminal voltage:',
             json.dumps(['10 V','11 V','12 V','9 V']),'10 V',
             'I = 12/12 = 1 A. V_terminal = 12 - 1x2 = 10 V.',
             'V_terminal = EMF - I*r',None),
            (tid,'Conceptual','Easy','When current is drawn from a battery, terminal voltage:',
             json.dumps(['Decreases','Increases','Stays same','Becomes zero']),'Decreases',
             'V = EMF - Ir. More current means more drop across internal resistance.',
             'V = EMF - Ir. More I = more drop',None),
            (tid,'Numerical','Medium','Two batteries 6V(r=1) and 12V(r=2) in series with 7 ohm. Current:',
             json.dumps(['1.8 A','2 A','1 A','3 A']),'1.8 A',
             'Total EMF=18V, total R=10 ohm. I = 18/10 = 1.8 A.',
             'Series batteries: add EMFs and add internal resistances',None),
        ])

    # AC Circuits
    tid = get_tid("AC Circuits & Transformers")
    if needs_more(tid):
        questions.extend([
            (tid,'Numerical','Easy','R=3 ohm, XL=4 ohm. Impedance Z:',
             json.dumps(['5 ohm','7 ohm','1 ohm','12 ohm']),'5 ohm',
             'Z = sqrt(R^2 + XL^2) = sqrt(9+16) = 5 ohm.',
             'Impedance: Z = sqrt(R^2 + (XL-XC)^2)',None),
            (tid,'Conceptual','Easy','At resonance in series LCR circuit:',
             json.dumps(['XL=XC and impedance minimum','XL>XC','XC>XL','Impedance maximum']),
             'XL=XC and impedance minimum',
             'At resonance XL=XC, Z=R (minimum), current maximum, power factor=1.',
             'Resonance: inductive and capacitive cancel',None),
            (tid,'Numerical','Medium','Transformer: N_p=200, N_s=1000, V_p=230V. Secondary voltage:',
             json.dumps(['1150 V','46 V','230 V','2300 V']),'1150 V',
             'Vs/Vp = Ns/Np. Vs = 230 * 5 = 1150 V.',
             'Vs/Vp = Ns/Np',None),
        ])

    # Refraction & Lenses
    tid = get_tid("Refraction & Lenses")
    if needs_more(tid):
        questions.extend([
            (tid,'Numerical','Easy','Convex lens f=20 cm, object at 60 cm. Image distance:',
             json.dumps(['30 cm','-30 cm','60 cm','-60 cm']),'30 cm',
             '1/v - 1/u = 1/f. u=-60, f=+20. 1/v = 1/20 - 1/60 = 2/60. v=30 cm.',
             'Lens formula: 1/v - 1/u = 1/f',None),
            (tid,'Conceptual','Easy','A concave lens always produces:',
             json.dumps(['Virtual, erect, diminished','Real, inverted, magnified','Virtual, inverted, magnified','Real, erect, diminished']),
             'Virtual, erect, diminished',
             'Concave (diverging) lens always produces virtual, erect, diminished image.',
             'Concave = diverging = always virtual and smaller',None),
            (tid,'Numerical','Medium','Two convex lenses f1=10 cm, f2=15 cm in contact. Combined focal length:',
             json.dumps(['6 cm','25 cm','5 cm','12.5 cm']),'6 cm',
             '1/f = 1/10 + 1/15 = 5/30. f = 6 cm.',
             'Lenses in contact: 1/f = 1/f1 + 1/f2',None),
        ])

    # Young's Double Slit
    tid = get_tid("Young's Double Slit Experiment")
    if needs_more(tid):
        questions.extend([
            (tid,'Numerical','Easy','YDSE: d=0.5mm, D=1m, lambda=500nm. Fringe width:',
             json.dumps(['1 mm','0.5 mm','2 mm','0.25 mm']),'1 mm',
             'beta = lambda*D/d = 500e-9 * 1 / 0.5e-3 = 1e-3 m = 1 mm.',
             'Fringe width beta = lambda*D/d',None),
            (tid,'Conceptual','Easy','In YDSE, if one slit is covered:',
             json.dumps(['Fringes disappear, single slit pattern appears','Fringes brighter','Fringes shift','Nothing changes']),
             'Fringes disappear, single slit pattern appears',
             'No two sources = no interference. Single slit diffraction pattern appears.',
             'Two coherent sources needed for interference',None),
            (tid,'Numerical','Medium','5th bright fringe at 5 mm from centre. 4th dark fringe at:',
             json.dumps(['3.5 mm','4.5 mm','4 mm','5 mm']),'3.5 mm',
             'beta=1mm. Dark fringe: y=(2n-1)*beta/2. n=4: y=7/2=3.5 mm.',
             'Dark fringe position: y = (2n-1)*beta/2',None),
        ])

    # Nuclear Physics
    tid = get_tid("Nuclear Physics & Radioactivity")
    if needs_more(tid):
        questions.extend([
            (tid,'Numerical','Easy','Half-life=30 years. Fraction remaining after 90 years:',
             json.dumps(['1/8','1/4','1/2','1/16']),'1/8',
             'n = 90/30 = 3 half-lives. Remaining = (1/2)^3 = 1/8.',
             'n half-lives gives (1/2)^n remaining',None),
            (tid,'Conceptual','Easy','In alpha decay, A and Z change by:',
             json.dumps(['A-4, Z-2','A-2, Z-1','A unchanged, Z-1','A-1, Z unchanged']),'A-4, Z-2',
             'Alpha = He-4 nucleus (A=4, Z=2). Emitting it: A decreases by 4, Z by 2.',
             'Alpha particle = 2 protons + 2 neutrons',None),
            (tid,'Numerical','Medium','Mass defect of Fe-56 = 0.5 u. Binding energy per nucleon: (1u=931.5 MeV)',
             json.dumps(['8.3 MeV','4.65 MeV','931.5 MeV','16.6 MeV']),'8.3 MeV',
             'BE = 0.5*931.5 = 465.75 MeV. Per nucleon = 465.75/56 = 8.3 MeV.',
             'BE/nucleon = (mass defect * 931.5) / A',None),
        ])

    # P-N Junction
    tid = get_tid("P-N Junction & Diodes")
    if needs_more(tid):
        questions.extend([
            (tid,'Conceptual','Easy','In forward bias of a p-n junction:',
             json.dumps(['Depletion region narrows, current flows','Depletion region widens, no current','Current flows in reverse','Diode is open circuit']),
             'Depletion region narrows, current flows',
             'Forward bias: external voltage opposes barrier. Depletion region shrinks. Current flows above ~0.7V for Si.',
             'Forward = reduce barrier = current flows',None),
            (tid,'Numerical','Medium','Half-wave rectifier, Vrms=220V. DC output voltage (approx):',
             json.dumps(['99 V','141 V','220 V','70 V']),'99 V',
             'Vpeak = 220*sqrt(2) = 311V. Vdc = Vpeak/pi = 99 V.',
             'Half-wave: Vdc = Vm/pi. Full-wave: Vdc = 2Vm/pi',None),
            (tid,'Conceptual','Medium','A Zener diode is used primarily as:',
             json.dumps(['Voltage regulator','Rectifier','Amplifier','Oscillator']),'Voltage regulator',
             'Zener maintains constant voltage in reverse breakdown. Used in voltage regulator circuits.',
             'Zener = voltage reference in reverse bias',None),
        ])

    # Arrhenius Equation (Chemistry)
    tid = get_tid("Arrhenius Equation & Collision Theory")
    if needs_more(tid):
        questions.extend([
            (tid,'Conceptual','Easy','If Ea=0, rate constant k equals:',
             json.dumps(['Frequency factor A','Zero','Infinity','R/T']),'Frequency factor A',
             'k = A*exp(-Ea/RT). If Ea=0: k = A*e^0 = A.',
             'k = A*exp(-Ea/RT). If Ea=0, exp(0)=1',None),
            (tid,'Conceptual','Easy','For a reaction to occur, colliding molecules must have:',
             json.dumps(['Sufficient energy AND proper orientation','Only sufficient energy','Only proper orientation','Any random collision']),
             'Sufficient energy AND proper orientation',
             'Collision theory: need energy >= activation energy AND correct orientation.',
             'Right key (orientation) AND enough force (energy)',None),
            (tid,'Numerical','Medium','Ea=40 kJ/mol. T increases from 300K to 310K. Rate increase factor:',
             json.dumps(['~1.6','~2','~10','~1.1']),'~1.6',
             'ln(k2/k1) = (Ea/R)*(1/T1-1/T2) = (40000/8.314)*(10/(300*310)) = 0.517. k2/k1 = e^0.517 = 1.68.',
             'Use: ln(k2/k1) = (Ea/R)*(T2-T1)/(T1*T2)',None),
            (tid,'Conceptual','Medium','A catalyst increases reaction rate by:',
             json.dumps(['Lowering activation energy','Increasing temperature','Increasing concentration','Shifting equilibrium']),
             'Lowering activation energy',
             'Catalyst provides alternate path with lower Ea. More molecules have E > Ea, so rate increases.',
             'Catalyst = lower Ea = more effective collisions',None),
        ])

    # Werner Theory
    tid = get_tid("Werner Theory & IUPAC Naming")
    if needs_more(tid):
        questions.extend([
            (tid,'Conceptual','Easy','In [Co(NH3)6]3+, coordination number of Co is:',
             json.dumps(['6','3','4','2']),'6',
             'CN = number of ligands directly bonded to metal. 6 NH3 molecules bonded to Co, so CN=6.',
             'Count ligands directly attached to central metal',None),
            (tid,'Conceptual','Easy','IUPAC name of [Cu(NH3)4]SO4 is:',
             json.dumps(['Tetraamminecopper(II) sulphate','Copper tetraamine sulphate','Tetraamminecopper sulphate IV','Sulphate tetraamminecopper(II)']),
             'Tetraamminecopper(II) sulphate',
             'Ligands first (alphabetical) + metal + OS. NH3=ammine, 4=tetra. Cu OS: 4(0)+OS=2, Cu(II). Counter ion = sulphate.',
             'Order: ligands + metal(OS) for cation, then anion',None),
            (tid,'Conceptual','Medium',"Werner's primary valency is satisfied by:",
             json.dumps(['Counter ions outside coordination sphere','Ligands inside coordination sphere','Both','Neither']),
             'Counter ions outside coordination sphere',
             'Primary valency = oxidation state = satisfied by counter ions outside sphere.',
             'Werner: primary valency = oxidation state = outer sphere',None),
        ])

    # Elimination Reactions
    tid = get_tid("Elimination Reactions")
    if needs_more(tid):
        questions.extend([
            (tid,'Conceptual','Easy','Reagent for E2 elimination from alkyl halide:',
             json.dumps(['Alcoholic KOH','Aqueous KOH','NaOH/H2O','H2SO4/H2O']),'Alcoholic KOH',
             'Alcoholic KOH: strong base in non-aqueous solvent favours elimination. Aqueous KOH favours substitution.',
             'Alcoholic KOH = elimination; Aqueous KOH = substitution',None),
            (tid,'Conceptual','Easy',"Saytzeff's rule: preferred elimination product is:",
             json.dumps(['More substituted (stable) alkene','Less substituted alkene','Fastest formed alkene','Alkene from most acidic H']),
             'More substituted (stable) alkene',
             'More substituted alkene is more stable due to hyperconjugation.',
             'More substituted = more stable',None),
            (tid,'Conceptual','Medium','E1 elimination is favoured by:',
             json.dumps(['Tertiary substrate, weak base, polar protic','Primary substrate, strong base, polar aprotic','Any substrate, strong base','Secondary, strong nucleophile']),
             'Tertiary substrate, weak base, polar protic',
             'E1: carbocation intermediate, favoured by tertiary substrate and polar protic solvent.',
             'E1 = carbocation = tertiary preferred',None),
            (tid,'Conceptual','Hard','In E2 elimination, beta-H and leaving group must be:',
             json.dumps(['Anti-periplanar (180 degrees)','Syn-periplanar (0 degrees)','At 90 degrees','Any angle']),
             'Anti-periplanar (180 degrees)',
             'E2 is concerted. H and LG must be anti-periplanar for correct orbital overlap.',
             'Anti arrangement: H and LG on opposite sides',None),
        ])

    # Electrochemical Cells
    tid = get_tid("Electrochemical Cells & Nernst Equation")
    if needs_more(tid):
        questions.extend([
            (tid,'Numerical','Easy','E0cell for Zn-Cu cell: (E0Zn=-0.76V, E0Cu=+0.34V)',
             json.dumps(['1.10 V','0.42 V','-1.10 V','0.76 V']),'1.10 V',
             'E0cell = E0cathode - E0anode = 0.34-(-0.76) = 1.10 V.',
             'E0cell = E0cathode - E0anode',None),
            (tid,'Conceptual','Medium','Cell potential increases when:',
             json.dumps(['Reactant concentration increases','Product concentration increases','Temperature decreases','Ionic strength increases']),
             'Reactant concentration increases',
             'Nernst: E = E0 - (RT/nF)lnQ. More reactants = smaller Q = larger E.',
             'More reactants = smaller Q = more positive E',None),
        ])

    # Rate Law
    tid = get_tid("Rate Law & Order of Reaction")
    if needs_more(tid):
        questions.extend([
            (tid,'Numerical','Easy','First-order reaction, t1/2=40 min. Rate constant k:',
             json.dumps(['0.0173 min^-1','0.025 min^-1','40 min^-1','0.693 min^-1']),'0.0173 min^-1',
             't1/2 = 0.693/k. k = 0.693/40 = 0.0173 min^-1.',
             't1/2 = 0.693/k for first-order',None),
            (tid,'Conceptual','Medium','Rate doubles when T increases by 10C. This rule of thumb is called:',
             json.dumps(["Van't Hoff rule","Arrhenius rule","Hess's law","Collision theory"]),"Van't Hoff rule",
             "Van't Hoff rule: rate approximately doubles for every 10C rise (temperature coefficient ~2). Arrhenius equation gives exact value.",
             "10C rise = ~double rate = Van't Hoff rule",None),
        ])

    # Mathematics topics
    tid = get_tid("Types of Relations & Functions")
    if needs_more(tid):
        questions.extend([
            (tid,'Conceptual','Easy','A function f:A->B is bijective if it is:',
             json.dumps(['Both one-one and onto','Only one-one','Only onto','Neither']),'Both one-one and onto',
             'Bijective = injective (one-one) + surjective (onto). Only bijective functions have inverses.',
             'Bijective = one-one + onto = invertible',None),
            (tid,'Conceptual','Medium','f(x)=x^2 is NOT one-one on R because:',
             json.dumps(['f(-2)=f(2)=4','It is discontinuous','Range is not R','It is unbounded']),'f(-2)=f(2)=4',
             'One-one requires f(a)=f(b) => a=b. But f(-2)=f(2)=4 with -2 != 2. Not one-one.',
             'One-one: no two inputs give same output',None),
        ])

    tid = get_tid("Properties & Principal Values")
    if needs_more(tid):
        questions.extend([
            (tid,'Numerical','Easy','Principal value of sin^-1(sqrt(3)/2):',
             json.dumps(['pi/3','pi/6','2pi/3','pi/4']),'pi/3',
             'sin(pi/3) = sqrt(3)/2. Principal value range of sin^-1 is [-pi/2, pi/2]. pi/3 is in range.',
             'Principal value of sin^-1 is in [-pi/2, pi/2]',None),
            (tid,'Numerical','Medium','sin^-1(1/2) + cos^-1(1/2) =',
             json.dumps(['pi/2','pi','0','pi/4']),'pi/2',
             'sin^-1(x) + cos^-1(x) = pi/2 for all x in [-1,1].',
             'Key identity: sin^-1(x) + cos^-1(x) = pi/2',None),
        ])

    tid = get_tid("Formation & Solution of ODEs")
    if needs_more(tid):
        questions.extend([
            (tid,'Conceptual','Easy','Order of d^2y/dx^2 + 3(dy/dx)^3 + y = 0 is:',
             json.dumps(['2','3','1','5']),'2',
             'Order = highest derivative = d^2y/dx^2 = 2nd order. Power of dy/dx is degree, not order.',
             'Order = highest derivative present',None),
            (tid,'Numerical','Medium','General solution of dy/dx = y/x:',
             json.dumps(['y = Cx','y = x+C','y = Ce^x','y = x^2/C']),'y = Cx',
             'Separate: dy/y = dx/x. Integrate: ln|y| = ln|x| + ln|C|. So y = Cx.',
             'Separate variables, then integrate both sides',None),
        ])

    tid = get_tid("Determinants & System of Equations")
    if needs_more(tid):
        questions.extend([
            (tid,'Numerical','Easy','det|2 3; 1 4| =',
             json.dumps(['5','11','-5','8']),'5',
             '2*4 - 3*1 = 8-3 = 5.',
             '2x2 determinant = ad - bc',None),
            (tid,'Conceptual','Medium','AX=B has unique solution when:',
             json.dumps(['det(A) != 0','det(A) = 0','det(A) > 0 only','B = 0']),'det(A) != 0',
             'det(A) != 0 means A is invertible, so X = A^-1 * B uniquely.',
             'det != 0 => invertible => unique solution',None),
        ])

    tid = get_tid("Lines & Planes in 3D")
    if needs_more(tid):
        questions.extend([
            (tid,'Numerical','Easy','Direction cosines: l=m=n. Their value:',
             json.dumps(['1/sqrt(3)','1/sqrt(2)','1/3','1']),'1/sqrt(3)',
             'l^2+m^2+n^2=1. If l=m=n: 3l^2=1, l=1/sqrt(3).',
             'l^2+m^2+n^2=1 always for direction cosines',None),
            (tid,'Conceptual','Medium','Angle between two planes equals angle between their:',
             json.dumps(['Normal vectors','Direction vectors','X-intercepts','Z-intercepts']),'Normal vectors',
             'Angle between planes = angle between normals. cos(theta) = |n1.n2|/(|n1||n2|).',
             'Planes are defined by normals',None),
        ])

    tid = get_tid("Conditional Probability & Bayes Theorem")
    if needs_more(tid):
        questions.extend([
            (tid,'Numerical','Easy','P(A)=0.4, P(B)=0.5, P(AnB)=0.2. P(A|B)=',
             json.dumps(['0.4','0.5','0.2','0.8']),'0.4',
             'P(A|B) = P(AnB)/P(B) = 0.2/0.5 = 0.4.',
             'P(A|B) = P(AnB)/P(B)',None),
            (tid,'Conceptual','Medium',"Bayes' Theorem finds:",
             json.dumps(['Posterior probability given evidence','Joint probability','Probability of mutually exclusive events','Standard deviation']),
             'Posterior probability given evidence',
             "Bayes updates prior probability with new evidence. P(H|E) = P(E|H)P(H)/P(E).",
             'Bayes = update beliefs with new information',None),
        ])

    tid = get_tid("Vector Algebra & Products")
    if needs_more(tid):
        questions.extend([
            (tid,'Numerical','Easy','|a| where a = 3i + 4j:',
             json.dumps(['5','7','sqrt(7)','25']),'5',
             '|a| = sqrt(3^2+4^2) = sqrt(25) = 5.',
             '|a| = sqrt(a1^2+a2^2+a3^2)',None),
            (tid,'Conceptual','Medium','Cross product a x b = 0 when:',
             json.dumps(['a and b are parallel','a and b are perpendicular','a=0 only','b=0 only']),
             'a and b are parallel',
             '|a x b| = |a||b|sin(theta). When parallel, theta=0, sin(0)=0.',
             'Cross product 0 when parallel (sin=0)',None),
        ])

    tid = get_tid("Definite Integrals & Properties")
    if needs_more(tid):
        questions.extend([
            (tid,'Numerical','Easy','Integral from 0 to 1 of x^2 dx =',
             json.dumps(['1/3','1/2','1','1/4']),'1/3',
             '[x^3/3] from 0 to 1 = 1/3.',
             'Integral of x^n = x^(n+1)/(n+1)',None),
            (tid,'Conceptual','Medium','Integral from -a to a of f(x)dx = 2*Integral from 0 to a when f is:',
             json.dumps(['An even function','An odd function','Any function','Periodic']),
             'An even function',
             'Even: f(-x)=f(x), so contributions from -a to 0 and 0 to a are equal.',
             'Even function: symmetric about y-axis',None),
        ])

    tid = get_tid("Limits, Continuity & Differentiability")
    if needs_more(tid):
        questions.extend([
            (tid,'Numerical','Easy','lim(x->0) sin(x)/x =',
             json.dumps(['1','0','x','Undefined']),'1',
             'Standard limit: lim(x->0) sin(x)/x = 1. Provable via L Hopital: cos(0)/1 = 1.',
             'Standard result: lim(x->0) sin(x)/x = 1',None),
            (tid,'Conceptual','Medium','f(x)=|x| at x=0 is:',
             json.dumps(['Continuous but not differentiable','Both continuous and differentiable','Neither','Differentiable but not continuous']),
             'Continuous but not differentiable',
             'Continuous: limit=f(0)=0. Not differentiable: left deriv=-1, right deriv=+1, they differ.',
             'Sharp corner = continuous but not differentiable',None),
        ])

    tid = get_tid("Photoelectric Effect")
    if needs_more(tid):
        questions.extend([
            (tid,'Numerical','Easy','Work function = 2 eV. Threshold frequency: (h=6.6e-34 Js)',
             json.dumps(['4.8e14 Hz','4.8e12 Hz','3e14 Hz','9.6e14 Hz']),'4.8e14 Hz',
             'v0 = phi/h = (2*1.6e-19)/(6.6e-34) = 4.8e14 Hz.',
             'phi = h*v0. 1eV = 1.6e-19 J',None),
            (tid,'Conceptual','Medium','Increasing intensity above threshold:',
             json.dumps(['More photoelectrons, same KE','Higher KE only','Both more electrons and higher KE','No effect']),
             'More photoelectrons, same KE',
             'KE_max = hv - phi (depends on frequency only). Intensity = more photons = more electrons but same energy each.',
             'KE depends on frequency, NOT intensity',None),
        ])

    tid = get_tid("Bohr's Model & Hydrogen Spectrum")
    if needs_more(tid):
        questions.extend([
            (tid,'Numerical','Easy','E1 = -13.6 eV for H atom. Energy in n=3:',
             json.dumps(['-1.51 eV','-3.4 eV','-13.6 eV','-6.8 eV']),'-1.51 eV',
             'En = -13.6/n^2 eV. E3 = -13.6/9 = -1.51 eV.',
             'En = -13.6/n^2 eV',None),
            (tid,'Conceptual','Medium','Lyman series corresponds to transitions ending at:',
             json.dumps(['n=1','n=2','n=3','n=4']),'n=1',
             'Lyman->n=1(UV), Balmer->n=2(visible), Paschen->n=3(IR).',
             'L-1, B-2, P-3: Lyman ends at n=1',None),
        ])

    tid = get_tid("Faraday's Law & Lenz's Law")
    if needs_more(tid):
        questions.extend([
            (tid,'Numerical','Easy','Coil: 100 turns. Flux changes from 0.05 to 0.01 Wb in 0.2s. Induced EMF:',
             json.dumps(['20 V','2 V','200 V','0.2 V']),'20 V',
             'EMF = -N*dPhi/dt = -100*(0.01-0.05)/0.2 = 100*0.04/0.2 = 20 V.',
             'Faraday: EMF = -N*dPhi/dt',None),
            (tid,'Conceptual','Easy',"Lenz's law is a consequence of conservation of:",
             json.dumps(['Energy','Charge','Momentum','Mass']),'Energy',
             "Lenz's law: induced current opposes cause. If it aided, energy would be created from nothing.",
             'Lenz law = energy conservation',None),
        ])

    tid = get_tid("SN1 and SN2 Reactions")
    if needs_more(tid):
        questions.extend([
            (tid,'Conceptual','Easy','SN1 proceeds via:',
             json.dumps(['Carbocation intermediate','One concerted step','Carbanion','Free radical']),
             'Carbocation intermediate',
             'SN1: Step 1: substrate ionises to carbocation (slow, RDS). Step 2: nucleophile attacks fast.',
             'SN1 = unimolecular = carbocation intermediate',None),
            (tid,'Conceptual','Medium','Which substrate undergoes SN2 most readily?',
             json.dumps(['CH3Br (methyl)','(CH3)3CBr (tertiary)','(CH3)2CHBr (secondary)','C6H5Br']),
             'CH3Br (methyl)',
             'SN2: back-side attack. Less hindrance = faster. Methyl > primary > secondary > tertiary.',
             'SN2: less steric hindrance = faster',None),
        ])

    if questions:
        c.executemany("""
            INSERT INTO questions (topic_id, q_type, difficulty, question_text, options, correct_option, solution_text, hint, pyq_year)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, questions)
        conn.commit()

    conn.close()
    return len(questions)


if __name__ == '__main__':
    init_db()
