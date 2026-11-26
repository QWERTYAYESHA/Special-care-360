import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn
import os

def create_clinical_evaluation_docx():
    doc = Document()
    
    # Page Margins (0.75 in)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    # Styles & Fonts
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(10.5)
    normal_style.font.color.rgb = RGBColor(0x22, 0x22, 0x22)

    # Color Palette
    PRIMARY = RGBColor(0x1B, 0x36, 0x5D)      # Deep Navy
    SECONDARY = RGBColor(0x00, 0x66, 0x99)    # Ocean Blue
    ACCENT = RGBColor(0x00, 0x80, 0x80)       # Teal
    GRAY_TEXT = RGBColor(0x55, 0x55, 0x55)
    LIGHT_BG_HEX = "F0F4F8"
    BORDER_HEX = "CCCCCC"

    # Header Title
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(2)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run("SPECIAL CARE 360 — CLINICAL EVALUATION FORM")
    title_run.bold = True
    title_run.font.size = Pt(18)
    title_run.font.color.rgb = PRIMARY

    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_before = Pt(0)
    sub_p.paragraph_format.space_after = Pt(12)
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = sub_p.add_run("Expert Review of AI-Generated IEP Goals, Multi-Pillar Correlation & Therapy Suggestions")
    sub_run.font.size = Pt(11)
    sub_run.font.bold = True
    sub_run.font.color.rgb = SECONDARY

    # Overview Box (Table with 1 cell)
    info_table = doc.add_table(rows=1, cols=1)
    info_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = info_table.cell(0, 0)
    cell.width = Inches(7.0)
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{LIGHT_BG_HEX}"/>')
    cell._tc.get_or_add_tcPr().append(shading)

    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="6" w:space="0" w:color="006699"/>
            <w:left w:val="single" w:sz="24" w:space="0" w:color="006699"/>
            <w:bottom w:val="single" w:sz="6" w:space="0" w:color="006699"/>
            <w:right w:val="single" w:sz="6" w:space="0" w:color="006699"/>
        </w:tcBorders>
    ''')
    cell._tc.get_or_add_tcPr().append(borders)

    cp = cell.paragraphs[0]
    cp.paragraph_format.space_before = Pt(4)
    cp.paragraph_format.space_after = Pt(2)
    r = cp.add_run("Target System: ")
    r.bold = True
    cp.add_run("Special Care 360 (Special Education Centre Management Platform)\n")

    r = cp.add_run("Target Scope (4 Core Neurodevelopmental & Neuromotor Disorders):\n")
    r.bold = True
    cp.add_run("  1. Autism Spectrum Disorder (ASD)\n  2. ADHD (Attention-Deficit / Hyperactivity Disorder)\n  3. Cerebral Palsy (CP)\n  4. Down Syndrome (Trisomy 21)\n")

    r = cp.add_run("Target Age Qualification: ")
    r.bold = True
    cp.add_run("Pediatric to Adolescent (0 to 16 Years)\n")

    r = cp.add_run("Evaluator Profile: ")
    r.bold = True
    cp.add_run("University Counselor / Clinical Psychologist / Special Education Expert / Speech & OT Therapist\n")

    r = cp.add_run("Clinical Grounding: ")
    r.bold = True
    cp.add_run("Tri-Pillar Architecture (Pillar 1: Medical Diagnosis | Pillar 2: ABC Tracker Incidents | Pillar 3: Skill Regressions)\n")

    r = cp.add_run("Safety Rule in Backend Code (Line 346): ")
    r.bold = True
    r_ital = cp.add_run('"Do NOT invent outside medical conditions. Do NOT prescribe medical drugs. All suggestions are DRAFTS for licensed therapist approval."')
    r_ital.italic = True

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # Section 1 Header
    h1 = doc.add_paragraph()
    h1.paragraph_format.space_before = Pt(14)
    h1.paragraph_format.space_after = Pt(6)
    r1 = h1.add_run("SECTION 1: 13 CLINICALLY GROUNDED EVALUATION CASE STUDIES")
    r1.bold = True
    r1.font.size = Pt(14)
    r1.font.color.rgb = PRIMARY

    # Helper function for cases
    def add_case_box(group_title, case_title, details):
        if group_title:
            gh = doc.add_paragraph()
            gh.paragraph_format.space_before = Pt(12)
            gh.paragraph_format.space_after = Pt(4)
            gr = gh.add_run(group_title)
            gr.bold = True
            gr.font.size = Pt(12)
            gr.font.color.rgb = SECONDARY

        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        c = tbl.cell(0, 0)
        c.width = Inches(7.0)
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="FAFBFD"/>')
        c._tc.get_or_add_tcPr().append(shd)

        tborders = parse_xml(f'''
            <w:tcBorders {nsdecls("w")}>
                <w:top w:val="single" w:sz="4" w:space="0" w:color="006699"/>
                <w:left w:val="single" w:sz="18" w:space="0" w:color="006699"/>
                <w:bottom w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
                <w:right w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
            </w:tcBorders>
        ''')
        c._tc.get_or_add_tcPr().append(tborders)

        p = c.paragraphs[0]
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(case_title + "\n")
        r.bold = True
        r.font.size = Pt(11)
        r.font.color.rgb = PRIMARY

        for k, v in details:
            p2 = c.add_paragraph()
            p2.paragraph_format.space_before = Pt(1)
            p2.paragraph_format.space_after = Pt(2)
            rk = p2.add_run(k + ": ")
            rk.bold = True
            rk.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
            rv = p2.add_run(v)
            if k.startswith("AI Unified") or k.startswith("AI Suggested"):
                rv.italic = True
                rv.font.color.rgb = RGBColor(0x00, 0x40, 0x80)
            elif k.startswith("Correlation"):
                rv.bold = True
                rv.font.color.rgb = ACCENT

        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # 13 Cases Data
    cases = [
        # Group A: ASD
        ("GROUP A: AUTISM SPECTRUM DISORDER (ASD) CASES",
         "CASE 1 (ASD — DUAL-INCIDENT CLUSTER): Ahmed Hassan",
         [
             ("Core Diagnosis", "Autism Spectrum Disorder (ASD Level 2), Active Seizure Protocol (Place on side, do not restrain, call nurse), Peanut Allergy."),
             ("INCIDENT 1 (Auditory Sensory Overload)", "Antecedent (A): Loud announcement blasted through classroom intercom speaker unexpectedly.\nBehavior (B): Covered both ears tightly, screamed loudly, started rocking vigorously (Severity: 3/5, Duration: 8 mins, Classroom A).\nConsequence (C): Teacher escorted Ahmed to quiet sensory corner until crying subsided."),
             ("INCIDENT 2 (Rigid Routine & Unannounced Transition)", "Antecedent (A): Teacher announced sudden switch from preferred drawing activity to math desk work without visual warning.\nBehavior (B): Swept drawing materials off table, threw crayons onto floor, refused to move (Severity: 4/5, Duration: 15 mins, Location: Classroom A).\nConsequence (C): Staff provided one-on-one verbal calming prompts and presented a visual timer."),
             ("AI Unified SMART Goal (Synthesizes Both ASD Triggers)", '"In 3 months, when loud intercom announcements or unexpected classroom transitions occur, Ahmed will independently don noise-cancelling headphones or follow a personal 3-step visual schedule, reducing disruptive screaming/throwing meltdowns from 4 times/week to 1 time/week."'),
             ("3 Sequential Milestones", "1. Put on noise-cancelling headphones within 30 seconds of an intercom alarm with minimal verbal cueing.\n2. Follow an individualized 3-step visual picture transition schedule when switching classroom tasks.\n3. Present a visual 'Quiet Card' to staff to take a calm 2-minute break in 4 out of 5 distress situations."),
             ("Correlation Metrics", "Multi-Pillar Sensory & Transition (Pillars 1 & 2) | Correlation Match: 93%")
         ]),
        (None,
         "CASE 2 (ASD — SINGLE AUDITORY FOCUS): Zohaib Khan",
         [
             ("Core Diagnosis", "Autism Spectrum Disorder (ASD), Auditory Defensive Sensitivity."),
             ("ABC Incident Logged", "School bell rang unexpectedly → Screaming, covering ears, bilateral body rocking (Severity: 3/5) → Escorted to quiet room."),
             ("AI Suggested Goal", '"In 3 months, when loud bells ring, Zohaib will wear his noise-cancelling headphones or show a break card, reducing screaming from 4 times a week to 1 time."'),
             ("3 Milestones", "1. Wear headphones for 5 minutes before scheduled bell with teacher guidance.\n2. Point to 'Quiet Card' when ambient classroom room is too noisy.\n3. Walk calmly in hallway wearing headphones during school bell."),
             ("Correlation Metrics", "Behavioral (Pillar 2) | Correlation Match: 92%")
         ]),
        (None,
         "CASE 3 (ASD — SENSORY TACTILE OVERLOAD & ALLERGEN SAFETY): Bilal Farooq",
         [
             ("Core Diagnosis", "Autism Spectrum Disorder (Level 2), Severe Peanut Allergy."),
             ("ABC Incident Logged", "Mixed-texture lunch served (rice with lentils/sauce) → Oral sensory gagging, pushing plate off table → Skipped meal."),
             ("AI Suggested Goal", '"In 4 months, the child will tolerate smelling, touching, and tasting 2 new safe non-allergenic food textures during snack time without distress."'),
             ("3 Milestones", "1. Tolerate new safe non-allergenic food resting on discovery plate for 10 minutes.\n2. Touch the food texture using a spoon or fork for 1 minute.\n3. Lick or take 1 small trial bite of safe texture on 3 separate therapy days."),
             ("Correlation Metrics", "Sensory & Allergen Safety (Pillars 1 & 2) | Correlation Match: 89%")
         ]),
        (None,
         "CASE 4 (ASD — ELOPEMENT & FLIGHT RISK): Zayan Tariq",
         [
             ("Core Diagnosis", "Autism Spectrum Disorder Level 3 (Non-verbal, Minimal Danger Awareness)."),
             ("ABC Incident Logged", "Classroom doorway unlatched for recess → Bolted instantly into hallway toward exit staircase (Severity: 5/5 Emergency) → Staff physical intercept."),
             ("AI Suggested Goal", '"In 3 months, during open door transitions, the child will stop at visual threshold floor markers and hold a transition ring with staff with 0 unescorted elopements."'),
             ("3 Milestones", "1. Stop feet on a red visual 'STOP' line painted on the doorway floor upon prompt.\n2. Hold teacher's transition escort ring before stepping into corridor.\n3. Walk from room to playground beside staff without breaking escort grasp in 9 of 10 opportunities."),
             ("Correlation Metrics", "Immediate Life Safety (Pillar 2) | Correlation Match: 96%")
         ]),
        (None,
         "CASE 5 (ASD — RIGID SCREEN TRANSITION MELTDOWN): Hamza Raza",
         [
             ("Core Diagnosis", "Autism Spectrum Disorder Level 1, Rigid Routine Adherence."),
             ("ABC Incident Logged", "Educational tablet time expired → Screaming loudly, throwing tablet onto floor (Severity: 4/5) → Device confiscated, 25-min dysregulation."),
             ("AI Suggested Goal", '"In 3 months, using dual 5-minute and 2-minute visual countdown timers, the student will turn off tablet and transition to study desk within 2 minutes peacefully in 4 of 5 sessions."'),
             ("3 Milestones", "1. Acknowledge the 5-minute visual timer alarm with a thumbs-up gesture.\n2. Place tablet into physical charging dock when final alarm chimes.\n3. Walk to study table using daily visual picture schedule with zero aggression."),
             ("Correlation Metrics", "Transition Flexibility (Pillar 2) | Correlation Match: 89%")
         ]),
        (None,
         "CASE 6 (ASD — PRAGMATIC SOCIAL ISOLATION): Daniyal Ali",
         [
             ("Core Diagnosis", "Autism Spectrum Disorder (High-Functioning / Asperger profile), Social Communication Deficit."),
             ("ABC Incident Logged", "Collaborative pair group assignment in class → Sat with head on desk, zero verbal engagement with assigned peer partner (Severity: 2/5)."),
             ("AI Suggested Goal", '"In 4 months, during pair classroom activities, the student will ask 2 project-related questions to a peer partner using structured conversation cue cards in 3 out of 4 collaborative sessions."'),
             ("3 Milestones", "1. Practice 2 project inquiry questions with speech therapist in 1-on-1 prep session.\n2. Ask partner 1 structured question during paired activity using a script prompt card.\n3. Exchange 2 reciprocating comments with partner concerning their shared class drawing."),
             ("Correlation Metrics", "Pragmatic Communication (Pillars 1 & 3) | Correlation Match: 86%")
         ]),
        (None,
         "CASE 7 (ASD — MULTI-INPUT: BEHAVIORAL INCIDENT + ADAPTIVE SKILL REGRESSION): Mustafa Kamal",
         [
             ("Core Diagnosis", "Autism Spectrum Disorder (Level 2), Sensory Tactile Defensive."),
             ("INPUT 1 (ABC Behavioral Incident)", "High ambient noise and crowding in cafeteria during lunch transition → Covered ears, high-pitched screaming, dropped to floor (Severity: 4/5)."),
             ("INPUT 2 (Active Skill Regression Alert)", "Regressed Skill: 'Independent Shoe-Tying & Adaptive Dressing' declined sharply from 75% baseline down to 25% due to sensory defensive tactile regression."),
             ("AI Unified SMART Goal (Sensory Coping + Dressing Skill Recovery)", '"In 3 months, during noisy transitional routines, Mustafa will independently put on noise-cancelling earmuffs and utilize adaptive Velcro lacing, reducing meltdowns from 4 times/week to 1 time/week and rehabilitating independent footwear dressing from 25% to 70%."'),
             ("3 Sequential Milestones", "1. Don noise-cancelling earmuffs within 30 seconds of high ambient hallway noise with minimal prompt.\n2. Practice securing adaptive loop fasteners on sensory footwear with 50% independence in OT sessions.\n3. Put on and fasten shoes independently before outdoor recess in 4 of 5 school days, restoring baseline self-care mastery."),
             ("Correlation Metrics", "Cross-Pillar: Behavioral & Skill Regression (Pillars 2 & 3) | Correlation Match: 94%")
         ]),

        # Group B: ADHD
        ("GROUP B: ADHD (ATTENTION-DEFICIT / HYPERACTIVITY DISORDER) CASES",
         "CASE 8 (ADHD — DUAL-INCIDENT CLUSTER): Sara Ahmed",
         [
             ("Core Diagnosis", "ADHD (Combined Inattentive & Hyperactive-Impulsive Type)."),
             ("INCIDENT 1 (Sedentary Academic Fatigue)", "Antecedent (A): Continuous desk writing assignment lasting longer than 10 minutes.\nBehavior (B): Tipped chair back, got out of seat, wandered around classroom, interrupted peers (Severity: 2/5, Duration: 5 mins, Location: Classroom B).\nConsequence (C): Teacher gave a 1-minute movement break then verbally prompted her to resume task."),
             ("INCIDENT 2 (Environmental Sensory Distraction)", "Antecedent (A): Desk positioned adjacent to classroom window overlooking active playground during independent math worksheet.\nBehavior (B): Tapped pencil loudly on desk, stared outdoors, refused to begin worksheet (Severity: 2/5, Duration: 8 mins, Location: Classroom B).\nConsequence (C): Teacher moved desk orientation away from window and repeated instructions."),
             ("AI Unified SMART Goal (Synthesizes Both Incidents)", '"In 3 months, during structured desk activities, Sara will sustain seated on-task attention for 15 continuous minutes using an active sensory cushion, window visual shielding, and a visual sand timer in 4 of 5 sessions."'),
             ("3 Sequential Milestones", "1. Maintain seated engagement on a dynamic wobble balance cushion utilizing a 10-minute visual sand timer for desk work.\n2. Utilize a silent handheld tactile fidget tool at an interior-facing desk to complete 1 worksheet without vocal or pencil tapping.\n3. Proactively display a 'Movement Pass' to request a 1-minute scheduled motor break instead of wandering off-seat."),
             ("Correlation Metrics", "Behavioral & Attention Regulation (Pillar 2) | Correlation Match: 89%")
         ]),
        (None,
         "CASE 9 (ADHD — SINGLE SEDENTARY FOCUS): Ayla Noor",
         [
             ("Core Diagnosis", "ADHD (Predominantly Hyperactive Type)."),
             ("ABC Incident Logged", "During 30-min quiet desk work → Repeatedly leaves seat, taps desk incessantly, wanders to peer desks → Teacher verbal reminder."),
             ("AI Suggested Goal", '"In 3 months, Ayla will remain seated and engaged in desk activities for 15 continuous minutes using a sensory seat cushion and sand timer."'),
             ("3 Milestones", "1. Sit for 5 minutes with a silent desk fidget tool.\n2. Complete 1 worksheet using a 10-minute visual sand timer.\n3. Ask for a 1-minute movement break using a picture card instead of leaving desk without asking."),
             ("Correlation Metrics", "Behavioral & Attention (Pillar 2) | Correlation Match: 88%")
         ]),
        (None,
         "CASE 10 (ADHD — HYPERACTIVE PROPRIOCEPTIVE CRASHING): Rayan Kashif",
         [
             ("Core Diagnosis", "ADHD with Sensory Processing Seeking (High Physical Motor Energy)."),
             ("ABC Incident Logged", "Morning circle time gathering on carpet → Crashing body into classmates, rolling violently on floor (Severity: 3/5) → Removed from circle."),
             ("AI Suggested Goal", '"In 3 months, the student will complete 5 minutes of \'heavy-work\' proprioceptive exercises before circle time to remain seated calmly on a wobble cushion for 12 minutes without peer collision."'),
             ("3 Milestones", "1. Push a 6-lb weighted therapy ball across gym for 3 minutes before class starts.\n2. Sit on an active balance cushion for 10 minutes during group story without crashing into peers.\n3. Squeeze a classroom resistance stress dough when feeling the urge to jump."),
             ("Correlation Metrics", "Sensory Regulation (Pillars 1 & 2) | Correlation Match: 91%")
         ]),

        # Group C: Down Syndrome
        ("GROUP C: DOWN SYNDROME CASES",
         "CASE 11 (DOWN SYNDROME — PEER TURN-TAKING & ARTICULATION DELAY): Omar Malik",
         [
             ("Core Diagnosis", "Down Syndrome (Trisomy 21), Moderate Speech Delay & Articulation Impairment."),
             ("ABC Incident Logged", "Peer took drawing crayon during group art → Omar physically pushed peer and cried loudly (Severity: 3/5) → Crayon removed by teacher."),
             ("AI Suggested Goal", '"In 3 months, when Omar wants a shared toy/crayon, he will use his AAC speech tablet or hand a \'My Turn\' picture card in 80% of situations."'),
             ("3 Milestones", "1. Touch 'Turn' button on speech tablet with hand guidance during therapy sessions.\n2. Hand 'My Turn' PECS card to teacher when wanting a shared object.\n3. Wait patiently for 30 seconds after asking before getting the toy in 4 of 5 trials."),
             ("Correlation Metrics", "Clinical & Speech Delay (Pillars 1 & 2) | Correlation Match: 90%")
         ]),
        (None,
         "CASE 12 (DOWN SYNDROME — ROUTINE CHANGE RESISTANCE & CLEANUP): Zainab Shah",
         [
             ("Core Diagnosis", "Down Syndrome, Cognitive Developmental Delay."),
             ("ABC Incident Logged", "Cleanup bell sounded and toy box presented → Threw toy box onto carpet, screamed 'No!', flopped to floor (Severity: 3/5) → Hand-over-hand teacher support."),
             ("AI Suggested Goal", '"In 3 months, during structured activity cleanup transitions, Zainab will follow a 3-step \'First Pack-Up, Then Snack\' visual schedule to put away 3 toys cooperatively in 4 of 5 opportunities."'),
             ("3 Milestones", "1. Pick up and place 1 toy into storage bin with hand-over-hand physical prompt.\n2. Put away 3 toys independently following verbal prompt and visual token board.\n3. Transition calmly to snack table upon pack-up completion with zero flopping."),
             ("Correlation Metrics", "Behavioral & Transition (Pillar 2) | Correlation Match: 88%")
         ]),

        # Group D: Cerebral Palsy
        ("GROUP D: CEREBRAL PALSY CASES",
         "CASE 13 (CEREBRAL PALSY — ACTIVE FINE MOTOR UTENSIL REGRESSION ALERT): Zara Khan",
         [
             ("Core Diagnosis", "Cerebral Palsy (Spastic Diplegia), Wheelchair User, Fine Motor Palmar Limitation."),
             ("Active Regression Alert (Pillar 3)", "Regressed Skill: 'Palmar Utensil Grasp for Self-Feeding' dropped from 80% baseline down to 35% after extended holiday absence."),
             ("ABC Incident Logged (Pillar 2)", "Cafeteria lunch → Struggled to hold standard spoon, dropped food, threw utensil in frustration and cried (Severity: 3/5, Cafeteria)."),
             ("AI Unified SMART Goal (Targets Utensil Incident & Reverses Motor Regression)", '"In 6 months, Zara will independently eat snack/lunch using an angled ergonomic adaptive spoon for 15 minutes, rehabilitating self-feeding grasp proficiency from 35% to 75%."'),
             ("3 Sequential Milestones", "1. Practice hand-grasp squeeze exercise with soft therapeutic putty for 3 minutes before lunch.\n2. Scoop 5 bites of food independently using an angled wide-grip adaptive spoon with less than 2 drops.\n3. Complete 75% of full snack meal independently with standby supervision."),
             ("Correlation Metrics", "Skill Regression Remediation (Pillar 3 Priority) | Correlation Match: 95%")
         ])
    ]

    for g_title, c_title, dtls in cases:
        add_case_box(g_title, c_title, dtls)

    # Section 2: Rubric Table
    doc.add_page_break()
    h2 = doc.add_paragraph()
    h2.paragraph_format.space_before = Pt(6)
    h2.paragraph_format.space_after = Pt(4)
    r2 = h2.add_run("SECTION 2: EXPERT SCORING RUBRIC (Please rate each case from 1 to 5)")
    r2.bold = True
    r2.font.size = Pt(13)
    r2.font.color.rgb = PRIMARY

    p_scale = doc.add_paragraph()
    p_scale.paragraph_format.space_after = Pt(6)
    r_scale = p_scale.add_run("Rating Scale:  1 = Poor  |  2 = Needs Work  |  3 = Acceptable  |  4 = Good  |  5 = Excellent")
    r_scale.bold = True
    r_scale.font.size = Pt(9.5)
    r_scale.font.color.rgb = GRAY_TEXT

    table_data = [
        ["Case #", "Student Name", "Core Disorder", "1. Safety", "2. Rel.", "3. SMART", "4. Pract.", "5. Pos.", "6. Corr.", "Overall (Out of 5)"],
        ["01", "Ahmed Hassan", "Autism Spectrum Disorder (ASD)", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[    ] / 5"],
        ["02", "Zohaib Khan", "Autism Spectrum Disorder (ASD)", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[    ] / 5"],
        ["03", "Bilal Farooq", "Autism Spectrum Disorder (ASD)", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[    ] / 5"],
        ["04", "Zayan Tariq", "Autism Spectrum Disorder (ASD)", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[    ] / 5"],
        ["05", "Hamza Raza", "Autism Spectrum Disorder (ASD)", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[    ] / 5"],
        ["06", "Daniyal Ali", "Autism Spectrum Disorder (ASD)", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[    ] / 5"],
        ["07", "Mustafa Kamal", "Autism Spectrum Disorder (ASD)", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[    ] / 5"],
        ["08", "Sara Ahmed", "ADHD (Inattentive/Hyperactive)", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[    ] / 5"],
        ["09", "Ayla Noor", "ADHD (Inattentive/Hyperactive)", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[    ] / 5"],
        ["10", "Rayan Kashif", "ADHD (Sensory/Motor Seeking)", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[    ] / 5"],
        ["11", "Omar Malik", "Down Syndrome (Trisomy 21)", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[    ] / 5"],
        ["12", "Zainab Shah", "Down Syndrome (Trisomy 21)", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[    ] / 5"],
        ["13", "Zara Khan", "Cerebral Palsy (Spastic Diplegia)", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[    ] / 5"],
        ["AVG", "ALL CASES COMPOSITE AVERAGE", "Multi-Disorder Benchmark", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[  ]", "[    ] / 5.0"]
    ]

    rubric_tbl = doc.add_table(rows=len(table_data), cols=10)
    rubric_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    col_widths = [Inches(0.55), Inches(1.2), Inches(1.6), Inches(0.45), Inches(0.45), Inches(0.45), Inches(0.45), Inches(0.45), Inches(0.45), Inches(0.85)]

    for row_idx, row_content in enumerate(table_data):
        row = rubric_tbl.rows[row_idx]
        is_header = (row_idx == 0)
        is_footer = (row_idx == len(table_data) - 1)

        for col_idx, cell_value in enumerate(row_content):
            c = row.cells[col_idx]
            c.width = col_widths[col_idx]
            cp = c.paragraphs[0]
            cp.paragraph_format.space_before = Pt(3)
            cp.paragraph_format.space_after = Pt(3)

            run = cp.add_run(cell_value)
            run.font.size = Pt(8.5)

            if is_header:
                run.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="1B365D"/>')
                c._tc.get_or_add_tcPr().append(shd)
            elif is_footer:
                run.bold = True
                run.font.color.rgb = PRIMARY
                shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="E2EDF8"/>')
                c._tc.get_or_add_tcPr().append(shd)
            else:
                if row_idx % 2 == 1:
                    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F9FBFD"/>')
                    c._tc.get_or_add_tcPr().append(shd)

            # Center text for rating checkboxes and Case #
            if col_idx in [0, 3, 4, 5, 6, 7, 8, 9]:
                cp.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Cell borders
            borders = parse_xml(f'''
                <w:tcBorders {nsdecls("w")}>
                    <w:top w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
                    <w:left w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
                    <w:bottom w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
                    <w:right w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>
                </w:tcBorders>
            ''')
            c._tc.get_or_add_tcPr().append(borders)

    # Section 3: Expert Sign-Off
    h3 = doc.add_paragraph()
    h3.paragraph_format.space_before = Pt(16)
    h3.paragraph_format.space_after = Pt(4)
    r3 = h3.add_run("SECTION 3: EXPERT FEEDBACK & OFFICIAL SIGN-OFF")
    r3.bold = True
    r3.font.size = Pt(13)
    r3.font.color.rgb = PRIMARY

    sign_box = doc.add_table(rows=1, cols=1)
    sign_box.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = sign_box.cell(0, 0)
    c.width = Inches(7.0)
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{LIGHT_BG_HEX}"/>')
    c._tc.get_or_add_tcPr().append(shd)

    borders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="6" w:space="0" w:color="006699"/>
            <w:left w:val="single" w:sz="18" w:space="0" w:color="006699"/>
            <w:bottom w:val="single" w:sz="6" w:space="0" w:color="006699"/>
            <w:right w:val="single" w:sz="6" w:space="0" w:color="006699"/>
        </w:tcBorders>
    ''')
    c._tc.get_or_add_tcPr().append(borders)

    p = c.paragraphs[0]
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run("Is the AI suggestion safe and suitable as a Clinical Assistant / Co-Pilot for therapists?\n")
    r.bold = True
    p.add_run("[   ] Yes, Approved\n[   ] Approved with minor therapist adjustments\n[   ] Not Approved\n\n")

    r = p.add_run("Expert Comments / Qualitative Remarks:\n")
    r.bold = True
    p.add_run("_________________________________________________________________________________\n" * 4)
    p.add_run("\n")

    r = p.add_run("Evaluator Information & Institutional Endorsement:\n")
    r.bold = True
    p.add_run("Doctor / Psychologist / Expert Name: ___________________________________________________\n")
    p.add_run("Designation / Role: __________________________________________________________________\n")
    p.add_run("Department / University / Hospital: ___________________________________________________\n")
    p.add_run("Date: ________________________               Signature & Official Stamp: __________________\n")

    out_path = r"c:\Users\HP\Downloads\fyp\docs\CLINICAL_EVALUATION_FORM.docx"
    doc.save(out_path)
    print(f"Document saved successfully at: {out_path}")

if __name__ == "__main__":
    create_clinical_evaluation_docx()
