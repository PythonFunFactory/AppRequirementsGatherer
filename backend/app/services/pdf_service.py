from pathlib import Path
from fpdf import FPDF
from ..config import settings

PAGE_W = 210  # A4 mm
MARGIN = 20
CONTENT_W = PAGE_W - MARGIN * 2

# Font candidates: (directory, regular, bold, italic)
_FONT_CANDIDATES = [
    (
        Path("C:/Windows/Fonts"),
        "arial.ttf", "arialbd.ttf", "ariali.ttf",
    ),
    (
        Path("/usr/share/fonts/truetype/liberation"),
        "LiberationSans-Regular.ttf", "LiberationSans-Bold.ttf", "LiberationSans-Italic.ttf",
    ),
]

FONTS_DIR = None
_FONT_REGULAR = _FONT_BOLD = _FONT_ITALIC = None

for _dir, _reg, _bold, _ital in _FONT_CANDIDATES:
    if _dir.exists() and (_dir / _reg).exists():
        FONTS_DIR = _dir
        _FONT_REGULAR, _FONT_BOLD, _FONT_ITALIC = _reg, _bold, _ital
        break

USE_SYSTEM_FONTS = FONTS_DIR is not None


def _safe(val) -> str:
    if val is None:
        return ""
    text = str(val)
    # Fallback replacements for non-Unicode font environments
    replacements = {
        "—": "-",  # em dash
        "–": "-",  # en dash
        "‘": "'",  # left single quote
        "’": "'",  # right single quote
        "“": '"',  # left double quote
        "”": '"',  # right double quote
        "…": "...",  # ellipsis
        "•": "-",  # bullet
        " ": " ",  # non-breaking space
    }
    if not USE_SYSTEM_FONTS:
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        return text.encode("latin-1", errors="replace").decode("latin-1")
    return text


class RequirementsPDF(FPDF):
    def __init__(self, title: str):
        super().__init__()
        self.doc_title = title
        self.set_margins(MARGIN, MARGIN, MARGIN)
        self.set_auto_page_break(auto=True, margin=MARGIN)
        self._load_fonts()

    def _load_fonts(self):
        if USE_SYSTEM_FONTS:
            self.add_font("Sans", "", str(FONTS_DIR / _FONT_REGULAR))
            self.add_font("Sans", "B", str(FONTS_DIR / _FONT_BOLD))
            self.add_font("Sans", "I", str(FONTS_DIR / _FONT_ITALIC))
            self._font_family = "Sans"
        else:
            self._font_family = "Helvetica"

    def _sf(self, style="", size=10):
        self.set_font(self._font_family, style, size)

    def header(self):
        if self.page_no() == 1:
            return
        self._sf("I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 6, f"Requirements — {_safe(self.doc_title)}", align="L")
        self.set_text_color(0, 0, 0)
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self._sf("I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 6, f"Page {self.page_no()}", align="C")
        self.set_text_color(0, 0, 0)

    def section_title(self, text: str):
        self._sf("B", 9)
        self.set_text_color(80, 80, 80)
        self.set_fill_color(245, 245, 245)
        self.cell(0, 7, _safe(text).upper(), fill=True, ln=True)
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def body_text(self, text: str, indent: int = 0):
        self._sf("", 10)
        self.set_x(MARGIN + indent)
        self.multi_cell(CONTENT_W - indent, 5, _safe(text))
        self.ln(1)

    def label_value(self, label: str, value: str):
        self._sf("B", 10)
        self.set_x(MARGIN)
        self.cell(35, 5, _safe(label) + ":")
        self._sf("", 10)
        self.multi_cell(CONTENT_W - 35, 5, _safe(value))
        self.ln(0.5)

    def req_row(self, req_id: str, title: str, description: str):
        self._sf("B", 9)
        self.set_x(MARGIN)
        self.set_fill_color(250, 250, 250)
        self.cell(22, 5, _safe(req_id), fill=True)
        self._sf("B", 10)
        self.cell(0, 5, _safe(title), ln=True)
        self._sf("", 10)
        self.set_x(MARGIN + 22)
        self.multi_cell(CONTENT_W - 22, 5, _safe(description))
        self.ln(1)

    def story_block(self, story_id: str, as_a: str, i_want: str, so_that: str):
        self._sf("I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 4, _safe(story_id), ln=True)
        self.set_text_color(0, 0, 0)
        self._sf("", 10)
        text = f"As a {_safe(as_a)}, I want {_safe(i_want)}, so that {_safe(so_that)}."
        self.multi_cell(CONTENT_W, 5, text)
        self.ln(2)

    def bullet(self, text: str):
        self._sf("", 10)
        self.set_x(MARGIN)
        self.cell(5, 5, "-")
        self.set_x(MARGIN + 5)
        self.multi_cell(CONTENT_W - 5, 5, _safe(text))
        self.ln(0.5)


async def render_pdf(session_id: int, requirements: dict, title: str) -> str:
    pdf = RequirementsPDF(title=title)
    pdf.add_page()

    # ── Cover / Title ──────────────────────────────────────────────
    pdf._sf("B", 20)
    pdf.set_y(40)
    pdf.multi_cell(0, 10, _safe(requirements.get("project_name") or title), align="C")
    pdf.ln(4)
    pdf._sf("I", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "Software Requirements Document", align="C", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(MARGIN, pdf.get_y(), PAGE_W - MARGIN, pdf.get_y())
    pdf.ln(8)

    # ── Overview ───────────────────────────────────────────────────
    if requirements.get("overview"):
        pdf.section_title("Overview")
        pdf.body_text(requirements["overview"])
        pdf.ln(4)

    # ── Stakeholders ───────────────────────────────────────────────
    stakeholders = requirements.get("stakeholders") or []
    if stakeholders:
        pdf.section_title("Stakeholders")
        for s in stakeholders:
            pdf.label_value(s.get("name", ""), s.get("description", ""))
        pdf.ln(4)

    # ── Functional Requirements ────────────────────────────────────
    frs = requirements.get("functional_requirements") or []
    if frs:
        pdf.section_title("Functional Requirements")
        for r in frs:
            pdf.req_row(r.get("id", ""), r.get("title", ""), r.get("description", ""))
        pdf.ln(2)

    # ── User Stories ───────────────────────────────────────────────
    stories = requirements.get("user_stories") or []
    if stories:
        pdf.section_title("User Stories")
        for s in stories:
            pdf.story_block(s.get("id", ""), s.get("as_a", ""), s.get("i_want", ""), s.get("so_that", ""))
        pdf.ln(2)

    # ── Non-Functional Requirements ────────────────────────────────
    nfrs = requirements.get("non_functional_requirements") or []
    if nfrs:
        pdf.section_title("Non-Functional Requirements")
        for r in nfrs:
            pdf.label_value(r.get("category", ""), r.get("description", ""))
        pdf.ln(4)

    # ── Constraints ────────────────────────────────────────────────
    constraints = requirements.get("constraints") or []
    if constraints:
        pdf.section_title("Constraints & Assumptions")
        for c in constraints:
            pdf.bullet(c)
        pdf.ln(4)

    # ── Open Questions ─────────────────────────────────────────────
    open_qs = requirements.get("open_questions") or []
    if open_qs:
        pdf.section_title("Open Questions")
        for q in open_qs:
            pdf.bullet(q)

    output_dir = Path(settings.pdf_storage_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / f"session_{session_id}.pdf")
    pdf.output(output_path)
    return output_path
