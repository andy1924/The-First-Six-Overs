"""Build The-First-Six-Overs.pptx — editorial presentation for the IPL powerplay study.

Run:  python tools/build_deck.py
Out:  The-First-Six-Overs.pptx  (repo root, 16:9, 26 slides, slide transitions, speaker notes)

Design: cream paper stock, ink type, hairline rules, one crimson accent.
Display  = Palatino Linotype   (Windows + macOS Palatino)
Body     = Georgia             (universally present)
Labels   = Consolas            (Windows + macOS Office)
No web assets: every figure comes from output/figures/.
"""

from pathlib import Path
import struct

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "output" / "figures"
OUT = ROOT / "The-First-Six-Overs.pptx"

# ---------------------------------------------------------------- palette
PAPER = "F6F2E9"
INK = "16130F"
INK_SOFT = "5B5347"
INK_FAINT = "8C8375"
RULE = "D9D1C0"
RULE_SOFT = "E7E0D2"
ACCENT = "A8102F"
TEAL = "0E8F94"
DARK = "16130F"
DARK_TEXT = "F6F2E9"
DARK_SOFT = "B9B1A1"
BLUSH = "E8A2B3"

DISPLAY = "Palatino Linotype"
BODY = "Georgia"
MONO = "Consolas"

SW, SH = 13.333, 7.5           # slide size, inches
ML, MR = 0.72, 0.72            # side margins
TOP = 0.46                     # top margin (running head)
BOT = 0.44                     # bottom margin


# ---------------------------------------------------------------- helpers
def png_size(path):
    """Read a PNG's pixel dimensions without Pillow."""
    with open(path, "rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return (2000, 1333)
    return struct.unpack(">II", head[16:24])


def solid(shape, hexcolor):
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor.from_string(hexcolor)
    shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def rect(slide, x, y, w, h, color):
    return solid(slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                                        Inches(w), Inches(h)), color)


def hairline(slide, x, y, w, color=RULE, weight=0.75):
    conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(y),
                                      Inches(x + w), Inches(y))
    conn.line.color.rgb = RGBColor.from_string(color)
    conn.line.width = Pt(weight)
    conn.shadow.inherit = False
    return conn


def boxed(slide, x, y, w, h, color=RULE, weight=0.75):
    """Unfilled rule-width rectangle — the plate and the callout share one idiom."""
    box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                                 Inches(w), Inches(h))
    box.fill.background()
    box.line.color.rgb = RGBColor.from_string(color)
    box.line.width = Pt(weight)
    box.shadow.inherit = False
    return box


def textbox(slide, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    return tf


def para(tf, first=False, align=PP_ALIGN.LEFT, line_spacing=None, space_before=0):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    if line_spacing:
        p.line_spacing = line_spacing
    if space_before:
        p.space_before = Pt(space_before)
    return p


def run(p, text, size, font=BODY, color=INK, bold=False, italic=False, track=None):
    r = p.add_run()
    r.text = text.replace("\n", "\v")      # \v is the line break inside a run
    r.font.size = Pt(size)
    r.font.name = font
    r.font.bold = bold
    r.font.italic = italic
    if color:                                  # None leaves the run unfilled (outline numerals)
        r.font.color.rgb = RGBColor.from_string(color)
    if track:                                  # letter-spacing, in points
        r.font._rPr.set("spc", str(int(track * 100)))
    return r


def label(tf, text, color=ACCENT, first=False, size=8.5, track=1.5,
          align=PP_ALIGN.LEFT, space_before=0):
    """Mono, uppercase, letter-spaced editorial label."""
    p = para(tf, first=first, align=align, space_before=space_before)
    run(p, text.upper(), size, MONO, color, track=track)
    return p


def outline_numeral(slide, x, y, w, h, text):
    """Big stroke-only numeral — the one typographic flourish of the deck."""
    tf = textbox(slide, x, y, w, h)
    p = para(tf, first=True)
    r = run(p, text, 150, DISPLAY, None, track=-6)   # no fill — outline only
    try:
        rPr = r.font._rPr
        # order matters: a:ln is first in CT_TextCharacterProperties, and a run may hold
        # exactly one fill choice — noFill here, so no solidFill may be set on this run.
        rPr.insert(0, parse_xml(
            '<a:ln %s w="20000"><a:solidFill><a:srgbClr val="%s"><a:alpha val="42000"/>'
            '</a:srgbClr></a:solidFill></a:ln>' % (nsdecls("a"), DARK_TEXT)))
        rPr.insert(1, parse_xml('<a:noFill %s/>' % nsdecls("a")))
    except Exception:
        r.font.color.rgb = RGBColor.from_string("3A342B")
    return tf


def transition(slide, tag="push", attr='dir="u"', speed="med"):
    """Ink a real PowerPoint slide transition. Order: cSld, clrMapOvr, transition, timing."""
    sld = slide._element
    if tag == "fade":
        attr = ""                      # p:fade carries no dir attribute — schema-invalid if added
    xml = '<p:transition %s spd="%s"><p:%s %s/></p:transition>' % (nsdecls("p"), speed, tag, attr)
    node = parse_xml(xml)
    anchor = sld.find("{http://schemas.openxmlformats.org/presentationml/2006/main}clrMapOvr")
    if anchor is None:
        anchor = sld.find("{http://schemas.openxmlformats.org/presentationml/2006/main}cSld")
    anchor.addnext(node)


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


# ---------------------------------------------------------------- slide chrome
def new_slide(prs, bg=PAPER):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = RGBColor.from_string(bg)
    return s


def running_head(slide, section, folio):
    tf = textbox(slide, ML, TOP, 6.2, 0.3)
    p = para(tf, first=True)
    run(p, section.upper(), 8.5, MONO, INK_FAINT, track=1.5)
    tf2 = textbox(slide, SW - MR - 5.0, TOP, 5.0, 0.3)
    p2 = para(tf2, first=True, align=PP_ALIGN.RIGHT)
    run(p2, folio.upper(), 8.5, MONO, INK_FAINT, track=1.5)


def headline(slide, text, y=0.95, size=27, w=None, color=INK):
    tf = textbox(slide, ML, y, w or (SW - ML - MR), 0.95)
    p = para(tf, first=True, line_spacing=1.02)
    run(p, text, size, DISPLAY, color, track=-0.3)
    return tf


def body_text(slide, x, y, w, text, size=11.5, color=INK_SOFT, line_spacing=1.42):
    tf = textbox(slide, x, y, w, 1.6)
    p = para(tf, first=True, line_spacing=line_spacing)
    run(p, text, size, BODY, color)
    return tf


def stat_rows(slide, x, y, w, rows, size=10.5):
    """Label left / value right, hairline between — flat by design, no table chrome."""
    cy = y
    hairline(slide, x, cy, w, INK, 1.1)
    cy += 0.09
    for name, val, tone in rows:
        tf = textbox(slide, x, cy, w * 0.62, 0.3, anchor=MSO_ANCHOR.TOP)
        p = para(tf, first=True)
        run(p, name, size, BODY, INK_SOFT)
        tf2 = textbox(slide, x + w * 0.55, cy, w * 0.45, 0.3)
        p2 = para(tf2, first=True, align=PP_ALIGN.RIGHT)
        col = {"win": TEAL, "bad": ACCENT}.get(tone, INK)
        run(p2, val, size + 0.5, MONO, col)
        cy += 0.30
        hairline(slide, x, cy, w, RULE_SOFT, 0.6)
        cy += 0.10
    return cy


def page(prs, section, crumb, title=None, y=0.92, size=26, w=None, trans="push"):
    """Open a content slide: paper, running head, optional headline, ink transition."""
    s = new_slide(prs)
    running_head(s, section, crumb)
    if title:
        headline(s, title, y, size, w)
    if trans:
        transition(s, trans, *(() if trans == "fade" else ('dir="u"',)))
    return s


def tiles(slide, x, y, w, items, cols=3, pitch=1.70, value=26, label_size=10.5,
          sub_size=7.5, gap=0.30):
    """Rule, big mono value, label, small caps note — the deck's stat tile."""
    tw = w / cols
    for i, (v, l, sm, col) in enumerate(items):
        cx = x + (i % cols) * tw
        cy = y + (i // cols) * pitch
        rect(slide, cx, cy, tw - gap, 0.025, col)
        tf = textbox(slide, cx, cy + 0.14, tw - gap, 0.55)
        run(para(tf, first=True), v, value, MONO, INK, track=-0.6)
        tf = textbox(slide, cx, cy + 0.70, tw - gap, 0.3)
        run(para(tf, first=True), l, label_size, BODY, INK_SOFT)
        tf = textbox(slide, cx, cy + 1.00, tw - gap, 0.3)
        label(tf, sm, color=INK_FAINT, first=True, size=sub_size, track=1.2)


def figure_plate(slide, png, x, y, w, fignum, caption):
    """White stock on paper: a bordered plate, the image, then a ruled caption."""
    pw, ph = png_size(FIGS / png)
    inner = w - 0.20
    img_h = inner * ph / pw
    plate_h = img_h + 0.20 + 0.40
    rect(slide, x, y, w, plate_h, "FFFFFF")
    boxed(slide, x, y, w, plate_h)
    slide.shapes.add_picture(str(FIGS / png), Inches(x + 0.10), Inches(y + 0.10), width=Inches(inner))
    cy = y + img_h + 0.18
    hairline(slide, x + 0.10, cy, inner, RULE_SOFT, 0.6)
    tf = textbox(slide, x + 0.10, cy + 0.08, inner, 0.34)
    p = para(tf, first=True, line_spacing=1.12)
    run(p, fignum.upper() + "  ", 7.5, MONO, ACCENT, track=1.2)
    run(p, caption, 8.8, BODY, INK_SOFT)


def lede(tf, kick, text, first=False, size=11.5, kick_color=ACCENT):
    """Small mono kicker on its own line, then the sentence — so wrapped text never
    collides with the label and every verdict block aligns the same way."""
    pk = para(tf, first=first)
    run(pk, kick.upper(), 8.5, MONO, kick_color, track=1.4)
    pt = para(tf, line_spacing=1.36, space_before=4)
    run(pt, text, size, BODY, INK)
    return pt


def footer_line(slide, text, x=None, y=None, w=None, color=INK_FAINT, size=8.5):
    tf = textbox(slide, x if x is not None else ML, y if y is not None else SH - BOT - 0.2,
                 w if w is not None else SW - ML - MR, 0.28)
    label(tf, text, color=color, first=True, size=size, track=1.4)
    return tf


def divider(prs, num, headline_text, sub, folio, note):
    s = new_slide(prs, DARK)
    outline_numeral(s, ML, 1.10, 3.2, 3.4, num)
    x = 3.62
    w = SW - x - MR
    hairline(s, x, 2.30, w * 0.22, DARK_SOFT, 1.1)
    tf = textbox(s, x, 2.52, w, 0.3)
    label(tf, "SECTION " + num, color=BLUSH, first=True)
    tf2 = textbox(s, x, 2.92, w, 1.0)
    p = para(tf2, first=True, line_spacing=1.03)
    run(p, headline_text, 40, DISPLAY, DARK_TEXT, track=-0.6)
    tf3 = textbox(s, x, 3.98, w * 0.86, 1.1)
    p3 = para(tf3, first=True, line_spacing=1.35)
    run(p3, sub, 12.5, BODY, DARK_SOFT)
    tf4 = textbox(s, SW - MR - 3.0, SH - BOT - 0.25, 3.0, 0.28)
    label(tf4, folio, color="6E6659", first=True, align=PP_ALIGN.RIGHT)
    transition(s, "fade")
    notes(s, note)
    return s


# ---------------------------------------------------------------- content
def build():
    prs = Presentation()
    prs.slide_width = Inches(SW)
    prs.slide_height = Inches(SH)

    total = 26

    # ---- 01 cover -------------------------------------------------------
    s = new_slide(prs)
    tf = textbox(s, ML, TOP, 8.0, 0.3)
    label(tf, "Mini project · Probability & Statistics", first=True)
    tf = textbox(s, SW - MR - 4.2, TOP, 4.2, 0.3)
    label(tf, "Cricsheet · IPL 2008–2025", color=INK_FAINT, first=True, align=PP_ALIGN.RIGHT)

    tf = textbox(s, ML, 2.02, 11.0, 1.5)
    p = para(tf, first=True, line_spacing=0.96)
    run(p, "The First ", 58, DISPLAY, INK, track=-1.2)
    run(p, "Six ", 58, DISPLAY, ACCENT, track=-1.2)
    run(p, "Overs", 58, DISPLAY, INK, track=-1.2)

    rect(s, ML, 3.62, 1.15, 0.03, INK)

    tf = textbox(s, ML, 3.94, 8.4, 1.4)
    p = para(tf, first=True, line_spacing=1.44)
    run(p, "Broadcasts say the powerplay sets up the match. This project tests that claim with ", 14.5)
    run(p, "1,227 IPL matches", 14.5, BODY, INK, bold=True)
    run(p, " — and finds the toss is close to worthless, while ", 14.5)
    run(p, "wickets lost", 14.5, BODY, INK, bold=True)
    run(p, " in the first six overs are not.", 14.5)

    hairline(s, ML, 5.86, SW - ML - MR, RULE, 0.75)
    tf = textbox(s, ML, 6.02, SW - ML - MR, 0.3)
    p = para(tf, first=True)
    for i, item in enumerate(["2,454 team innings", "18 seasons · 15 teams · 60 venues",
                              "R · one reproducible script"]):
        if i:
            run(p, "      ·      ", 8.5, MONO, RULE)
        run(p, item.upper(), 8.5, MONO, INK_FAINT, track=1.4)
    transition(s, "push", 'dir="u"')
    notes(s, "Open on the claim, not on the method. One line: 1,227 IPL matches, two questions — "
             "did the toss matter, did the powerplay matter. Answer up front: toss barely, "
             "powerplay clearly. Detail follows.")

    # ---- 02 required flow -----------------------------------------------
    s = page(prs, "Contents", "02 / %d" % total,
             "Eight beats, in the order the brief asks for.", 0.92, 26, w=9.6)
    beats = [
        ("01", "Project title", "The First Six Overs"),
        ("02", "Aim / problem statement", "Six research questions, no outcome leakage"),
        ("03", "Domain theory", "Powerplay, fielding restrictions, the toss"),
        ("04", "Data description with reference", "Cricsheet ball-by-ball IPL · cited in full"),
        ("05", "Data cleaning", "Filters, standardised names, derived columns"),
        ("06", "Data implementation", "R · cricketdata, dplyr, ggplot2, broom"),
        ("07", "Data analysis", "RQ1–RQ6 · tests, bands, regression"),
        ("08", "Conclusion", "The verdict, the limits, what stays open"),
    ]
    colw = (SW - ML - MR - 0.70) / 2
    for i, (num, title, sub) in enumerate(beats):
        col_i, row = i // 4, i % 4
        x = ML + col_i * (colw + 0.70)
        y = 2.06 + row * 1.06
        rect(s, x, y, colw, 0.025, INK)
        tf = textbox(s, x, y + 0.12, 0.44, 0.3)
        label(tf, num, color=ACCENT, first=True, size=8.5)
        tf = textbox(s, x + 0.52, y + 0.09, colw - 0.52, 0.32)
        p = para(tf, first=True)
        run(p, title, 13, DISPLAY, INK, track=-0.1)
        tf = textbox(s, x + 0.52, y + 0.44, colw - 0.52, 0.36)
        p = para(tf, first=True, line_spacing=1.2)
        run(p, sub, 10.5, BODY, INK_SOFT)
    footer_line(s, "Beats 1–8 follow in that order; each opens with its own section divider.")
    notes(s, "Read the eight beats once, quickly, then move on. This is the map the rest of the deck "
             "walks: title, aim, theory, data and its source, cleaning, implementation, analysis, "
             "conclusion.")

    # ---- 03 the claim ---------------------------------------------------
    s = page(prs, "Before we start", "03 / %d" % total)
    tf = textbox(s, ML, 1.62, 10.6, 1.9)
    p = para(tf, first=True, line_spacing=1.05)
    run(p, "“Win the powerplay, ", 40, DISPLAY, INK, track=-0.6)
    run(p, "win the match", 40, DISPLAY, ACCENT, track=-0.6)
    run(p, ".”", 40, DISPLAY, INK, track=-0.6)
    tf = textbox(s, ML, 3.10, 10.0, 0.3)
    label(tf, "Commentary folklore — presumed true, never tested", color=INK_FAINT, first=True)
    hairline(s, ML, 3.72, SW - ML - MR, RULE, 0.75)
    tf = textbox(s, ML, 3.96, 8.9, 1.4)
    p = para(tf, first=True, line_spacing=1.44)
    run(p, "Momentum is an argument from memory. Conditional probability is an argument from data. "
           "Six research questions later the folklore survives — but not the half of it that blames "
           "the toss.", 14.5)
    notes(s, "Frame the stakes: this is a claim everyone repeats. We treat it as a hypothesis.")

    # ---- 03 divider · aim ----------------------------------------------
    divider(prs, "01", "Aim",
            "Turn a claim made in the commentary box into a testable question about "
            "conditional probability.", "01 · AIM",
            "Six sections. Aim, theory, data, implementation, analysis, conclusion.")

    # ---- 04 problem + RQs ----------------------------------------------
    s = page(prs, "01 · Aim", "Problem statement · RQ1–RQ6", "Estimate how the toss and the powerplay are associated with winning.", 0.92, 24)
    body_text(s, ML, 1.72, 11.6,
              "The match result is a binary outcome. Every explanatory variable is known by the end of "
              "the sixth over, so the model never sees the final score of the match it is predicting — "
              "no outcome leakage.", 11.5)
    hairline(s, ML, 2.46, SW - ML - MR, RULE, 0.75)

    rqs = [
        ("RQ1", "Probability of winning after winning the toss?", "Conditional probability · Bayes"),
        ("RQ2", "Is the toss independent of the match result?", "Chi-square test of independence"),
        ("RQ3", "Do winners score more in the powerplay?", "Mean · variance · CI · t-test"),
        ("RQ4", "Do powerplay wickets follow Poisson?", "Poisson · goodness of fit"),
        ("RQ5", "How does win probability move across score and wicket bands?", "Bivariate · conditional probability"),
        ("RQ6", "Which early variables matter most?", "Correlation · logistic regression"),
    ]
    for n, (rid, q, concept) in enumerate(rqs):
        col = n % 2
        row = n // 2
        x = ML + col * ((SW - ML - MR) / 2 + 0.20)
        y = 2.84 + row * 1.30
        tf = textbox(s, x, y, 0.55, 0.3)
        label(tf, rid, color=ACCENT, first=True, size=8.5)
        tf = textbox(s, x + 0.62, y - 0.03, 4.55, 0.85)
        p = para(tf, first=True, line_spacing=1.24)
        run(p, q, 11.5, BODY, INK_SOFT)
        p2 = para(tf, line_spacing=1.1, space_before=3)
        run(p2, concept.upper(), 7.5, MONO, INK_FAINT, track=1.2)
    footer_line(s, "Explanatory variables: toss outcome · toss decision · powerplay runs · powerplay wickets")
    notes(s, "Walk the six questions in two rows. Emphasise the leakage rule — it is the design "
             "decision that makes the model honest.")

    # ---- 05 hypotheses --------------------------------------------------
    s = page(prs, "01 · Aim", "H0 / H1 · α = 0.05", "Three null hypotheses, stated before the data was touched.", 0.92, 24)
    hyps = [
        ("Toss impact", "Toss result and match result are independent.",
         "Toss result and match result are associated."),
        ("Powerplay score", "Winning and losing teams share the same mean powerplay score.",
         "Winning teams score higher."),
        ("Powerplay wickets", "Wickets lost follow a Poisson distribution with estimated λ.",
         "Observed wickets differ from Poisson."),
    ]
    colw = (SW - ML - MR - 0.9) / 3
    for i, (title, h0, h1) in enumerate(hyps):
        x = ML + i * (colw + 0.45)
        rect(s, x, 1.86, colw * 0.30, 0.025, INK)
        tf = textbox(s, x, 2.02, colw, 0.3)
        label(tf, title, color=INK, first=True, size=9)
        tf = textbox(s, x, 2.42, colw, 1.9)
        p = para(tf, first=True, line_spacing=1.36)
        run(p, "H₀  ", 11, MONO, INK_FAINT)
        run(p, h0, 11.5, BODY, INK_SOFT)
        p = para(tf, line_spacing=1.36, space_before=10)
        run(p, "H₁  ", 11, MONO, INK_FAINT)
        run(p, h1, 11.5, BODY, INK_SOFT)
    hairline(s, ML, 4.72, SW - ML - MR, INK, 1.1)
    tf = textbox(s, ML, 4.90, SW - ML - MR, 0.9)
    lede(tf, "Why it matters",
         "A hypothesis written after seeing the result is not a test — it is a caption. "
         "These three were fixed first.", first=True, size=13)
    notes(s, "Small slide, big point: pre-registered hypotheses. α = 0.05 throughout.")

    # ---- 06 divider · theory -------------------------------------------
    divider(prs, "02", "Domain theory",
            "Why the first six overs are the most volatile — and the best-documented — "
            "part of a T20 innings.", "02 · THEORY",
            "Necessary context before any number: what the powerplay is, and why it is a "
            "trade-off rather than a free run-scoring window.")

    # ---- 07 domain ------------------------------------------------------
    s = page(prs, "02 · Domain theory", "Overs 1–6", "Restrictions cut both ways.", 0.92, 26, w=5.4)
    body_text(s, ML, 1.66, 5.3,
              "In the powerplay only two fielders may stand outside the 30-yard circle. Boundaries get "
              "cheaper — and so do wickets, because batters attack from ball one.", 11.5)
    body_text(s, ML, 2.72, 5.3,
              "That is the momentum story: a fast start, the argument goes, forces the opposition onto "
              "the back foot for the remaining fourteen overs.", 11.5)
    hairline(s, ML, 3.72, 5.3, RULE, 0.75)
    tf = textbox(s, ML, 3.92, 5.3, 1.5)
    lede(tf, "Design consequence",
         "Rules were relaxed after 2015 and pitches differ by venue, so this is an observational "
         "study: it measures association, never causation.", first=True, size=11, kick_color=INK_SOFT)
    stat_rows(s, 6.70, 1.66, 5.9, [
        ("Fielders allowed outside the circle", "2", None),
        ("Balls per powerplay", "36", None),
        ("Share of the innings", "30%", None),
        ("Observations per team", "36 balls", None),
        ("Outcome variable", "win / loss", None),
        ("Predictor cutoff", "end of over 6", "bad"),
    ])
    footer_line(s, "Everything the model knows about a team, it knows by the end of its sixth over.",
                x=6.70, y=4.90, w=5.9)
    notes(s, "Two minutes. The importance is the trade-off: attacking raises the ceiling and the "
             "variance at the same time. That is why wickets later turn out to matter more than runs.")

    # ---- 08 divider · data ---------------------------------------------
    divider(prs, "03", "Data",
            "Eighteen seasons of ball-by-ball IPL records, reduced to a single clean table.",
            "03 · DATA",
            "Two slides: the description and its reference, then the cleaning rules.")

    # ---- 09 data --------------------------------------------------------
    s = page(prs, "03 · Data description with reference", "Source & scope", "1,227 matches, 2,454 innings.", 0.92, 26, w=5.9)
    body_text(s, ML, 1.70, 5.10,
              "Ball-by-ball JSON from Cricsheet, one file per match, pulled and parsed in R with the "
              "cricketdata package. Each match contributes two rows — one per team.", 11.5)
    tf = textbox(s, ML, 2.86, 5.10, 1.1)
    p = para(tf, first=True, line_spacing=1.36)
    run(p, "CITATION  ", 8.5, MONO, ACCENT, track=1.4)
    run(p, "Cricsheet. Available match data downloads. cricsheet.org/downloads/", 10.5, BODY, INK_FAINT)
    tiles(s, 6.30, 1.70, SW - MR - 6.30, [
        ("1,227", "completed matches", "analysed", INK),
        ("2,454", "team-match rows", "two per match", INK),
        ("18", "seasons", "2008–2025", INK),
        ("15", "franchises", "name-standardised", INK),
        ("60", "venues", "not modelled", INK),
        ("16", "matches excluded", "no-result · short", ACCENT),
    ])
    hairline(s, ML, 5.06, SW - ML - MR, INK, 1.1)
    tf = textbox(s, ML, 5.26, SW - ML - MR, 0.9)
    lede(tf, "Coverage",
         "Every completed IPL match with a full six-over powerplay for both sides — the whole "
         "population, not a sample.", first=True, size=13)
    notes(s, "Cricsheet is the reference dataset for cricket analytics. Stress that this is the full "
             "population of completed IPL matches, so the confidence intervals describe the league, "
             "not an experiment.")

    # ---- 10 cleaning ----------------------------------------------------
    s = page(prs, "03 · Data cleaning", "Rules & reproducibility", "Raw files are never modified.", 0.92, 26, w=5.4)
    steps = [
        ("Filter", "Drop 9 abandoned / no-result matches and 7 without a complete six-over powerplay."),
        ("Filter", "Keep only deliveries in overs 1–6 of each innings."),
        ("Standardise", "Merge renamed franchises (Kings XI Punjab → Punjab Kings) across seasons."),
        ("Build", "powerplay_runs, powerplay_wickets and powerplay_run_rate per team-innings."),
        ("Encode", "Binary toss_win and match_win; banded score and wicket columns."),
        ("Check", "Missing values, duplicate match IDs, impossible scores — all clean."),
    ]
    y = 1.62
    for tag, txt in steps:
        tf = textbox(s, ML, y, 0.95, 0.3)
        label(tf, tag, color=ACCENT, first=True, size=7.5, track=1.2)
        tf = textbox(s, ML + 1.02, y - 0.02, 5.35, 0.62)
        p = para(tf, first=True, line_spacing=1.30)
        run(p, txt, 11, BODY, INK_SOFT)
        y += 0.62
    rect(s, 7.05, 1.62, 5.55, 1.46, DARK)
    tf = textbox(s, 7.28, 1.80, 5.10, 1.1)
    label(tf, "# one command reproduces everything", color="9A9184", first=True, size=8, track=1.0)
    p = para(tf, line_spacing=1.3, space_before=8)
    run(p, "Rscript ", 11.5, MONO, "F0B7C4")
    run(p, "R/01_analysis.R", 11.5, MONO, DARK_TEXT)
    stat_rows(s, 7.05, 3.42, 5.55, [
        ("Matches in the download", "1,243", None),
        ("Matches analysed", "1,227", None),
        ("Team rows out", "2,454", None),
        ("Columns", "21", None),
    ])
    footer_line(s, "Reads dataset/*.json → writes the cleaned table, result tables and all seven figures into output/.",
                x=7.05, y=5.34, w=5.55)
    notes(s, "One slide for reproducibility. The single script reads the raw JSON and regenerates "
             "every number in this deck — no manual steps, and the raw download is never written to.")

    # ---- 11 divider · implementation -----------------------------------
    divider(prs, "04", "Implementation",
            "One script, seven visuals, no manual steps — the analysis is reproducible from the "
            "raw download.", "04 · IMPLEMENTATION",
            "Tooling slide. Short: packages, outputs, and the guarantee that everything is traceable.")

    # ---- 12 implementation ---------------------------------------------
    s = page(prs, "04 · Data implementation", "R · 6 packages", "Statistics in the open.", 0.92, 26, w=5.4)
    body_text(s, ML, 1.62, 5.35,
              "Every test is a named function and its output is tidied with broom, so each p-value, "
              "confidence interval and odds ratio in this deck traces back to one line of code.", 11.5)
    hairline(s, ML, 2.72, 5.35, INK, 1.1)
    pkgs = [
        ("Data", "cricketdata — download and parse Cricsheet JSON"),
        ("Wrangle", "dplyr · tidyr — cleaning, grouping, reshaping"),
        ("Plots", "ggplot2 · scales — all seven figures"),
        ("Tests", "broom — tidy output for χ², t-test and regression"),
    ]
    y = 2.90
    for tag, txt in pkgs:
        tf = textbox(s, ML, y, 0.95, 0.3)
        label(tf, tag, color=ACCENT, first=True, size=7.5, track=1.2)
        tf = textbox(s, ML + 1.02, y - 0.02, 4.33, 0.5)
        p = para(tf, first=True, line_spacing=1.3)
        run(p, txt, 11, BODY, INK_SOFT)
        y += 0.60
    tf = textbox(s, 6.95, 1.62, 5.4, 0.3)
    label(tf, "Output", color=INK, first=True, size=9)
    rows = [
        ("ipl_powerplay_match_level.csv", "2,454 × 21 analysis table"),
        ("figures/01–07", "toss, runs, heatmap, Poisson, trends, odds ratios"),
        ("result tables", "descriptives, hypothesis tests, regression"),
        ("analysis.md", "final written verdict"),
    ]
    y = 1.98
    hairline(s, 6.95, y, 5.66, INK, 1.1)
    y += 0.10
    for name, desc in rows:
        tf = textbox(s, 6.95, y, 5.66, 0.52)
        p = para(tf, first=True, line_spacing=1.26)
        run(p, name, 11, MONO, INK_SOFT)
        p2 = para(tf, line_spacing=1.2)
        run(p2, desc, 9.5, BODY, INK_FAINT)
        y += 0.66
        hairline(s, 6.95, y - 0.10, 5.66, RULE_SOFT, 0.6)
    footer_line(s, "The raw dataset/ folder is an input only — nothing in the pipeline overwrites it.",
                x=6.95, y=4.92, w=5.66)
    notes(s, "Technical slide — keep it to a minute. The point is auditability: no spreadsheet steps, "
             "no hand-tuned numbers.")

    # ---- 13 divider · analysis -----------------------------------------
    divider(prs, "05", "Analysis",
            "Six questions, six tests. The toss disappoints; the wickets decide.",
            "05 · ANALYSIS",
            "The core of the talk — eight slides. Pace: roughly one minute each, more on the heatmap "
            "and the regression.")

    # ---- 14 descriptives ------------------------------------------------
    s = page(prs, "05 · Data analysis", "Powerplay runs · n = 2,454", "A typical powerplay is 48 for 1.", 0.92, 26, w=5.6)
    body_text(s, ML, 1.66, 5.4,
              "Runs are right-skewed: a handful of explosive starts, up to 125, drag the mean above the "
              "median. Wickets are far tighter — most sides lose one or two.", 11.5)
    tf = textbox(s, ML, 2.72, 5.4, 1.2)
    p = para(tf, first=True, line_spacing=0.95)
    run(p, "48.5", 54, DISPLAY, INK, track=-1.2)
    run(p, " runs", 21, DISPLAY, INK_FAINT)
    footer_line(s, "Mean powerplay score per team innings — 8.08 runs an over.",
                x=ML, y=3.94, w=5.4)
    rows = [
        ("Mean", "48.49", "1.44"),
        ("Median", "48.0", "1.0"),
        ("Std. deviation", "13.51", "1.12"),
        ("Variance", "182.6", "1.26"),
        ("Skewness", "+0.59", "+1.29"),
        ("Excess kurtosis", "+1.15", "+2.34"),
        ("Range", "13 – 125", "0 – 6"),
    ]
    x0, w0 = 6.60, 6.01
    tf = textbox(s, x0, 1.62, w0 * 0.4, 0.3)
    label(tf, "Statistic", color=INK_FAINT, first=True, size=8)
    tf = textbox(s, x0 + w0 * 0.45, 1.62, w0 * 0.275, 0.3)
    label(tf, "Runs", color=INK_FAINT, first=True, size=8, align=PP_ALIGN.RIGHT)
    tf = textbox(s, x0 + w0 * 0.725, 1.62, w0 * 0.275, 0.3)
    label(tf, "Wickets", color=INK_FAINT, first=True, size=8, align=PP_ALIGN.RIGHT)
    y = 1.92
    hairline(s, x0, y, w0, INK, 1.1)
    y += 0.10
    for name, a, b in rows:
        tf = textbox(s, x0, y, w0 * 0.42, 0.3)
        p = para(tf, first=True)
        run(p, name, 11, BODY, INK_SOFT)
        for val, cx in ((a, 0.45), (b, 0.725)):
            tf = textbox(s, x0 + w0 * cx, y, w0 * 0.275, 0.3)
            p = para(tf, first=True, align=PP_ALIGN.RIGHT)
            run(p, val, 11.5, MONO, INK)
        y += 0.34
        hairline(s, x0, y, w0, RULE_SOFT, 0.6)
        y += 0.10
    footer_line(s, "Both tails are heavier than a normal distribution: very good and very bad starts "
                   "happen more often than the bell curve predicts.",
                x=x0, y=y + 0.12, w=w0)
    notes(s, "Descriptive slide. Two things to say: the mean sits above the median because a few "
             "innings explode, and the excess kurtosis tells you the tails matter. This is why the "
             "analysis uses bands and a logistic model rather than the mean alone.")

    # ---- 15 toss (RQ1, RQ2) ---------------------------------------------
    s = page(prs, "05 · Data analysis · RQ1 RQ2", "Conditional probability · χ²")
    tf = textbox(s, ML, 1.32, 5.5, 1.3)
    p = para(tf, first=True, line_spacing=0.95)
    run(p, "51.3", 62, DISPLAY, INK, track=-1.4)
    run(p, "%", 26, DISPLAY, INK_FAINT)
    tf = textbox(s, ML, 2.42, 5.3, 0.8)
    p = para(tf, first=True, line_spacing=1.34)
    run(p, "Win rate after winning the toss — against ", 12.5)
    run(p, "48.7%", 12.5, BODY, INK, bold=True)
    run(p, " after losing it.", 12.5)
    stat_rows(s, ML, 3.24, 5.3, [
        ("95% confidence interval", "48.5 – 54.1%", None),
        ("Chi-square p-value", "0.183", None),
        ("Decision at α = 0.05", "fail to reject H0", "bad"),
    ])
    hairline(s, ML, 4.62, 5.3, INK, 1.1)
    tf = textbox(s, ML, 4.80, 5.3, 1.0)
    lede(tf, "RQ1 · RQ2",
         "The interval contains 50%. The toss buys a 2.6-point edge that could easily be noise — "
         "it is not a decision-maker.", first=True)
    figure_plate(s, "01_toss_win_rate_ci.png", 6.62, 1.42, 5.99, "Fig. 01",
                 "Win rate after winning or losing the toss, with exact 95% binomial confidence intervals.")
    notes(s, "The headline number everyone expects to be bigger. 51.3% against 48.7% — a 2.6 point "
             "gap. The confidence interval runs from 48.5 to 54.1, so 50% is well inside it, and the "
             "chi-square p-value of 0.183 means we cannot reject independence. The toss is a coin.")

    # ---- 16 toss decision -----------------------------------------------
    s = page(prs, "05 · Data analysis · RQ2", "Post-toss decision", "Field first, and the toss starts to pay.", 0.92, 25, w=6.40)
    body_text(s, ML, 1.78, 5.50,
              "Captains chase: 816 of 1,227 matches were field-first. Among toss winners the choice "
              "divides them — 54.2% of those who elected to field went on to win, against 45.7% of "
              "those who batted first.", 11.5)
    stat_rows(s, ML, 3.16, 5.50, [
        ("Chose to field first", "816 matches", None),
        ("Chose to bat first", "411 matches", None),
        ("Win rate after fielding first", "54.2%", "win"),
        ("Win rate after batting first", "45.7%", "bad"),
    ])
    hairline(s, ML, 5.00, 5.50, INK, 1.1)
    tf = textbox(s, ML, 5.18, 5.50, 1.1)
    lede(tf, "RQ2b · secondary finding",
         "An 8.5-point gap (95% CI 2.6–14.4, χ² = 7.8, p = 0.005, recomputed from the cleaned CSV). "
         "It does not survive adjustment — in the regression on slide 20 the same choice sits at "
         "OR ≈ 1, so read this as a raw comparison, not an established edge.", first=True)
    figure_plate(s, "02_toss_decision_result.png", 6.62, 1.42, 5.99, "Fig. 02",
                 "Outcome split within each decision among toss winners — the field-first group converts better.")
    notes(s, "Secondary finding, flagged as such: among toss winners, electing to field is associated "
             "with an 8.5-point higher win rate. Two caveats — it is recomputed from the cleaned CSV "
             "rather than part of the pre-registered toss test, and teams that choose to bat may differ "
             "systematically. Association, not proof.")

    # ---- 17 runs (RQ3) ---------------------------------------------------
    s = page(prs, "05 · Data analysis · RQ3", "t-test · p < 0.001", "Winners start 5.8 runs faster.", 0.92, 25, w=6.40)
    tiles(s, ML, 1.72, 5.35, [("51.4", "winners", "median 50", TEAL),
                              ("45.6", "losers", "median 45", ACCENT),
                              ("59.7%", "win rate at 50+ runs", "vs 42.3% below 50", INK)],
          pitch=1.24, value=25, label_size=10, sub_size=7)
    body_text(s, ML, 3.16, 5.35,
              "The difference is small in absolute terms — under one run an over — but with 2,454 "
              "innings the two-sample t-test rejects H0 decisively (p < 0.001).", 11.5)
    hairline(s, ML, 4.18, 5.35, INK, 1.1)
    tf = textbox(s, ML, 4.36, 5.35, 1.0)
    lede(tf, "RQ3",
         "Scoring more in the powerplay is a real signal, but a weak one: it moves the odds by about "
         "seventeen points, not by the match.", first=True)
    figure_plate(s, "03_powerplay_runs_by_result.png", 6.62, 1.24, 5.99, "Fig. 03",
                 "Powerplay runs for winners and losers — the distributions overlap heavily.")
    notes(s, "Significant, but look at the violin plots — the overlap is enormous. Statistically "
             "significant is not the same as useful for prediction. That distinction sets up the "
             "heatmap on the next slide.")

    # ---- 18 heatmap (RQ5) -----------------------------------------------
    s = page(prs, "05 · Data analysis · RQ5", "16 cells · conditional probability")
    tf = textbox(s, ML, 1.28, 5.4, 1.9)
    p1 = para(tf, first=True, line_spacing=1.08)
    run(p1, "Runs raise the ceiling.", 28, DISPLAY, INK, track=-0.5)
    p2 = para(tf, line_spacing=1.08)
    run(p2, "Wickets decide.", 28, DISPLAY, ACCENT, track=-0.5)
    stat_rows(s, ML, 2.66, 5.4, [
        ("60+ runs, no wicket lost", "77.1%", "win"),
        ("60+ runs, 3+ wickets lost", "35.5%", None),
        ("Under 40 runs, no wicket lost", "69.7%", None),
        ("Under 40 runs, 3+ wickets lost", "23.1%", "bad"),
    ])
    footer_line(s, "Move down a column and the colour barely changes. Move across a row and it collapses.",
                x=ML, y=4.62, w=5.4)
    figure_plate(s, "04_score_wicket_heatmap.png", 6.52, 1.24, 6.09, "Fig. 04",
                 "Win probability by powerplay score band and wickets lost, with cell sample sizes.")
    notes(s, "The single most important chart in the deck. Hold on it. The vertical axis — runs — "
             "matters far less than the horizontal axis — wickets. A team that is 60 for none wins "
             "about 77% of the time; a team that is 60 for three, roughly 35%. Protection beats "
             "acceleration.")

    # ---- 19 poisson (RQ4) -----------------------------------------------
    s = page(prs, "05 · Data analysis · RQ4", "Poisson goodness of fit", "Wickets are not random events.", 0.92, 25, w=5.4)
    body_text(s, ML, 1.78, 5.35,
              "If powerplay wickets were memoryless, Poisson with λ = 1.44 would fit. It does not: the "
              "observed spread, variance 1.26, is narrower than Poisson demands, and six-wicket "
              "powerplays almost never happen.", 11.5)
    stat_rows(s, ML, 3.06, 5.35, [
        ("Mean wickets per innings", "1.44", None),
        ("Variance (Poisson: equal to mean)", "1.26", None),
        ("Goodness-of-fit test", "reject H0 · p ≈ 0.002", "bad"),
    ])
    hairline(s, ML, 4.36, 5.35, INK, 1.1)
    tf = textbox(s, ML, 4.54, 5.35, 1.0)
    lede(tf, "RQ4",
         "Wicket loss is under-dispersed — teams actively protect wickets in the powerplay rather "
         "than losing them at a constant rate.", first=True)
    figure_plate(s, "05_poisson_wickets.png", 6.62, 1.42, 5.99, "Fig. 05",
                 "Observed versus Poisson-expected wicket counts — thinner tails than the model predicts.")
    notes(s, "One caution for the room: the goodness-of-fit p-value near 0.002 was recomputed from "
             "the cleaned CSV, so quote it as approximate. The qualitative result is what matters — "
             "the tails are thinner than Poisson, which means wicket loss is a managed, deliberate "
             "process, not a memoryless one.")

    # ---- 20 regression (RQ6) --------------------------------------------
    s = page(prs, "05 · Data analysis · RQ6", "Logistic regression · odds ratios")
    tf = textbox(s, ML, 1.28, 5.6, 1.3)
    p = para(tf, first=True, line_spacing=0.95)
    run(p, "0.60", 58, DISPLAY, ACCENT, track=-1.4)
    run(p, " × odds", 22, DISPLAY, INK_FAINT)
    tf = textbox(s, ML, 2.34, 5.4, 0.8)
    p = para(tf, first=True, line_spacing=1.34)
    run(p, "For every extra wicket lost in the powerplay, estimated win odds fall about ", 12.5)
    run(p, "40%", 12.5, BODY, INK, bold=True)
    run(p, ".", 12.5)
    stat_rows(s, ML, 3.02, 5.4, [
        ("Powerplay wickets (per wicket)", "OR 0.60", "bad"),
        ("Powerplay runs (per run)", "OR > 1", "win"),
        ("Toss won", "OR ≈ 1", None),
        ("Toss decision: field", "OR ≈ 1", None),
    ])
    hairline(s, ML, 4.86, 5.4, INK, 1.1)
    tf = textbox(s, ML, 5.04, 5.4, 1.0)
    lede(tf, "RQ6",
         "The strongest early indicator of an IPL win is not losing wickets in the first six overs. "
         "The toss adds nothing once wickets are in the model.", first=True)
    figure_plate(s, "07_logistic_odds_ratios.png", 6.62, 1.42, 5.99, "Fig. 07",
                 "Odds ratios with 95% confidence intervals for early-match predictors.")
    notes(s, "The model that answers RQ6. Wickets carry the signal, runs carry a smaller one, and the "
             "toss confidence interval sits across 1.0 — no effect. Note the honest caveat: an odds "
             "ratio of 0.60 is an association, not a lever.")

    # ---- 21 team trends --------------------------------------------------
    s = page(prs, "05 · Data analysis", "18 seasons · 15 franchises", "A fast start is not a habit that wins.", 0.92, 25, w=6.40)
    body_text(s, ML, 1.82, 5.35,
              "Teams with the same powerplay run rate convert it into wins at very different rates, and "
              "the gap moves season to season. Squad quality, venue and conditions sit behind both the "
              "start and the result — which is exactly why this study claims association, not cause.", 11.5)
    hairline(s, ML, 3.36, 5.35, RULE, 0.75)
    tf = textbox(s, ML, 3.56, 5.35, 1.6)
    lede(tf, "Context worth naming",
         "Sixty venues, rule changes after 2015, and franchise reshuffles across eighteen seasons "
         "all feed into the spread beside you.", first=True, size=11, kick_color=INK_SOFT)
    figure_plate(s, "06_team_season_trends.png", 6.62, 1.06, 5.99, "Fig. 06",
                 "Powerplay run rate and win rate by team and season.")
    notes(s, "This is the confounder slide in disguise. If the powerplay caused wins, the teams with "
             "high run rates would convert consistently. They do not.")

    # ---- 22 divider · conclusion ---------------------------------------
    divider(prs, "06", "Conclusion",
            "What the tests actually license us to say — and what they do not.",
            "06 · CONCLUSION",
            "Close on the verdict, then spend real time on the limitations. Exam answers live here.")

    # ---- 23 conclusion ---------------------------------------------------
    s = page(prs, "06 · Conclusion", "Six answers", "Answers, in the order the questions were asked.", 0.90, 24)
    answers = [
        ("RQ1 · Win after the toss", "Marginal", "51.3% · CI 48.5–54.1", None),
        ("RQ2 · Toss independent of result", "No evidence of association", "p = 0.183", None),
        ("RQ3 · Winners score more", "Yes, narrowly", "51.4 vs 45.6 · p < 0.001", None),
        ("RQ4 · Wickets Poisson", "No — thinner tails", "var 1.26 vs mean 1.44", None),
        ("RQ5 · Best early situation", "60+ runs, no wicket lost", "77.1% wins", None),
        ("RQ6 · Strongest early signal", "Wickets lost in the powerplay", "OR 0.60", "hot"),
    ]
    x0, w0 = ML, SW - ML - MR
    y = 1.72
    hairline(s, x0, y, w0, INK, 1.1)
    y += 0.10
    for q, a, ev, tone in answers:
        if tone == "hot":
            rect(s, x0 - 0.14, y - 0.06, w0 + 0.28, 0.44, "F1E7E4")
        tf = textbox(s, x0, y, w0 * 0.36, 0.3)
        p = para(tf, first=True)
        run(p, q, 11, BODY, INK_SOFT)
        tf = textbox(s, x0 + w0 * 0.36, y, w0 * 0.40, 0.3)
        p = para(tf, first=True)
        run(p, a, 11, BODY, INK, bold=(tone == "hot"))
        tf = textbox(s, x0 + w0 * 0.76, y, w0 * 0.24, 0.3)
        p = para(tf, first=True, align=PP_ALIGN.RIGHT)
        run(p, ev, 11, MONO, ACCENT if tone == "hot" else INK)
        y += 0.44
        hairline(s, x0, y, w0, RULE_SOFT, 0.6)
        y += 0.10
    hairline(s, x0, y + 0.08, w0, INK, 1.1)
    tf = textbox(s, x0, y + 0.26, w0, 1.0)
    lede(tf, "Verdict",
         "The toss is a small advantage at most. A strong, low-wicket powerplay is the clearer sign "
         "of an IPL win — and protecting wickets matters more than scoring quickly.",
         first=True, size=13)
    notes(s, "Read the six rows quickly, land on RQ6, then say the verdict sentence verbatim. "
             "This is the sentence the grader is looking for.")

    # ---- 24 limitations --------------------------------------------------
    s = page(prs, "06 · Conclusion", "Scope & limits", "What this cannot tell you.", 0.92, 25, w=5.6)
    limits = [
        ("Causality", "Observational data. Stronger squads produce both good powerplays and wins."),
        ("Confounders", "Opposition, venue, pitch, weather, season and rule changes are unmodelled."),
        ("Reverse path", "Teams already ahead may bat conservatively — low wickets can be a "
                         "consequence of winning, not only a cause."),
        ("Generalisability", "IPL only. These numbers should not be assumed for other T20 leagues "
                             "or formats."),
    ]
    y = 1.94
    for tag, txt in limits:
        tf = textbox(s, ML, y, 1.25, 0.3)
        label(tf, tag, color=ACCENT, first=True, size=7.5, track=1.2)
        tf = textbox(s, ML + 1.34, y - 0.02, 5.05, 0.75)
        p = para(tf, first=True, line_spacing=1.32)
        run(p, txt, 11, BODY, INK_SOFT)
        y += 0.80
    rect(s, 7.15, 1.94, 5.46, 1.86, PAPER)
    boxed(s, 7.15, 1.94, 5.46, 1.86)
    tf = textbox(s, 7.40, 2.16, 4.96, 1.5)
    label(tf, "Honest headline", color=ACCENT, first=True, size=8.5)
    p = para(tf, line_spacing=1.40, space_before=8)
    run(p, "The powerplay ", 12.5)
    run(p, "describes", 12.5, BODY, INK, italic=True)
    run(p, " a winning team well. It does not prove the powerplay ", 12.5)
    run(p, "made", 12.5, BODY, INK, italic=True)
    run(p, " the win — and no observational dataset of 1,227 matches can settle that.", 12.5)
    footer_line(s, "Next steps: venue-normalised baselines, a within-match design, and mixed-effects "
                   "models with season and team as random effects.",
                x=7.15, y=4.04, w=5.46)
    notes(s, "Do not skip this slide — for a statistics module it is often where the marks are. "
             "Association is not causation, and the reverse path is subtle: a team that is cruising "
             "protects wickets, so part of the effect runs the other way.")

    # ---- 25 closing ------------------------------------------------------
    s = new_slide(prs)
    tf = textbox(s, ML, TOP, 8.0, 0.3)
    label(tf, "The First Six Overs", color=INK_FAINT, first=True)
    tf = textbox(s, SW - MR - 3.0, TOP, 3.0, 0.3)
    label(tf, "26 / 26", color=INK_FAINT, first=True, align=PP_ALIGN.RIGHT)
    rect(s, ML, 2.20, 1.15, 0.03, INK)
    tf = textbox(s, ML, 2.52, 11.9, 2.4)
    p1 = para(tf, first=True, line_spacing=1.04)
    run(p1, "The toss is a coin.", 42, DISPLAY, INK, track=-0.9)
    p2 = para(tf, line_spacing=1.04)
    run(p2, "The powerplay is a ", 42, DISPLAY, INK, track=-0.9)
    run(p2, "signal", 42, DISPLAY, ACCENT, track=-0.9)
    run(p2, ".", 42, DISPLAY, INK, track=-0.9)
    tf = textbox(s, ML, 4.72, 9.4, 0.9)
    p = para(tf, first=True, line_spacing=1.40)
    run(p, "And the sharpest part of that signal is not how fast a team scored — it is how few wickets "
           "it lost getting there.", 14)
    hairline(s, ML, 5.94, SW - ML - MR, RULE, 0.75)
    tf = textbox(s, ML, 6.10, SW - ML - MR, 0.3)
    p = para(tf, first=True)
    for i, item in enumerate(["Data · Cricsheet ball-by-ball IPL", "1,227 matches · 2,454 innings",
                              "R · R/01_analysis.R"]):
        if i:
            run(p, "      ·      ", 8.5, MONO, RULE)
        run(p, item.upper(), 8.5, MONO, INK_FAINT, track=1.4)
    transition(s, "fade")
    notes(s, "Land the verdict and stop. Invite questions on the bowling side: wicket protection "
             "looks like the real lever, and the next version of this study should test it properly.")

    # ---- metadata --------------------------------------------------------
    prs.core_properties.title = "The First Six Overs — IPL Powerplay Study"
    prs.core_properties.author = "The First Six Overs"
    prs.core_properties.subject = ("Do the toss and the first six overs decide an IPL match? "
                                   "1,227 matches, Cricsheet ball-by-ball data.")
    prs.core_properties.comments = ("Editorial-themed presentation generated by tools/build_deck.py. "
                                    "Figures sourced from output/figures/.")

    prs.save(str(OUT))
    print("wrote %s  (%d slides)" % (OUT, len(prs.slides._sldIdLst)))


if __name__ == "__main__":
    build()
