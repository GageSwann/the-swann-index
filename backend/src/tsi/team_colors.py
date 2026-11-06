# ruff: noqa: E501  (a data table of source URLs)
"""Corrections to CFBD's team colors (Phase 13.2, decision #138).

CFBD's 2026 `/teams` colors are kept as loaded; this table corrects the teams whose
CFBD colors are missing, black-only, duplicated or out of date. It is applied when
teams are read (`db/queries/team_info.team_refs`), so a fix is live on the next API
deploy and survives any re-ingest. Each row names its source: a school's own brand
guide where one gives hex values (`official=True`), else the best team-color reference
found (usually one checked against the athletics site's logo). Which color the site
shows in each theme is decided by the web (`web/lib/format/color.ts`).

Dependency-free so every layer can import it.
"""

from dataclasses import dataclass
from datetime import date

CHECKED = date(2026, 11, 6)


@dataclass(frozen=True)
class ColorFix:
    team_id: int
    school: str  # for reading the table; matching is by id
    color: str
    alt_color: str | None
    source: str
    official: bool  # True: the school's own brand guide gives these hex values
    checked: date = CHECKED


FIXES: tuple[ColorFix, ...] = (
    # FBS: out of date in CFBD
    ColorFix(12, "Arizona", "#AB0520", "#0C234B",
             "https://marcom.arizona.edu/brand-guidelines/colors", True),
    ColorFix(154, "Wake Forest", "#9E7E38", "#000000",
             "https://brand.wfu.edu/our-brand-identity/color-patterns-papers/", True),
    # FCS: wrong, duplicated or incomplete in CFBD
    ColorFix(2016, "Alcorn State", "#512D6D", "#CC8A00",
             "https://www.alcorn.edu/wp-content/uploads/2023/07/ASU_Graphic_Standards_Manual_122020.pdf", True),
    ColorFix(2083, "Bucknell", "#003865", "#E87722",
             "https://usteamcolors.com/bucknell-university-colors/", False),
    ColorFix(2097, "Campbell", "#EA7125", "#1E252B",
             "https://brand.campbell.edu/visual-identity/color-palette/", True),
    ColorFix(2110, "Central Arkansas", "#582C83", "#7C878E",
             "https://uca.edu/toolkit/official-colors/", True),
    ColorFix(2130, "Chicago State", "#006666", "#FFFFFF",
             "https://usteamcolors.com/chicago-state-university-colors/", False),
    ColorFix(2837, "East Texas A&M", "#1D2953", "#E8A311",
             "https://usteamcolors.com/texas-am-university-commerce-colors/", False),
    ColorFix(2197, "Eastern Illinois", "#003399", "#B2B2B2",
             "https://usteamcolors.com/eastern-illinois-university-colors/", False),
    ColorFix(2210, "Elon", "#73000A", "#B59A57",
             "https://www.elon.edu/u/university-communications/brand/guide/visual-identity/color-type/", True),
    ColorFix(2916, "Incarnate Word", "#CB333B", "#000000",
             "https://www.uiw.edu/styleguide/graphic-standards/logo-colors.html (PMS 1797; hex from usteamcolors.com)", False),
    ColorFix(2320, "Lamar", "#B00C14", "#FFFFFF",
             "https://www.lamar.edu/web-communication/resources/web-style-guidelines.html", True),
    ColorFix(2815, "Lindenwood", "#000000", "#B5A36A",
             "https://lindenwood.edu/marketing-and-communications/brand-resources", True),
    ColorFix(2341, "Long Island University", "#69B3E7", "#FFC72C",
             "https://www.brandcolorcode.com/liu-sharks", False),
    ColorFix(2385, "Mercyhurst", "#1A554B", "#182752",
             "https://usteamcolors.com/mercyhurst-university-colors/", False),
    ColorFix(2771, "Merrimack", "#0B335E", "#FFDD00",
             "https://www.merrimack.edu/wp-content/uploads/visual-identity-guidelinespdf.pdf (gold; blue from usteamcolors.com)", True),
    ColorFix(93, "Murray State", "#002144", "#ECAC00",
             "https://www.murraystate.edu/about/administration/advancement/branding-mkt-comm/toolkit/index.aspx", True),
    ColorFix(2453, "North Alabama", "#592B8A", "#FFB92A",
             "https://una.edu/emdc/brand/docs/una-branding-guide-2024.pdf", True),
    ColorFix(2448, "North Carolina A&T", "#004684", "#FDB927",
             "https://relations.ncat.edu/branding/color-palette.html", True),
    ColorFix(2464, "Northern Arizona", "#002454", "#FFD200",
             "https://nau.edu/visual-identity-guide/color (blue; gold from usteamcolors.com)", True),
    ColorFix(2900, "St. Thomas (MN)", "#520C77", "#97999B",
             "https://www.brandcolorcode.com/university-of-st-thomas-minnesota", False),
    ColorFix(284, "Stonehill", "#4F2684", "#FFFFFF",
             "https://www.stonehill.edu/offices-and-services/marketing-office/brand-standards/colors-typography (PMS 268; hex from brandcolorcode.com)", False),
    ColorFix(2627, "Tarleton State", "#4F2D7F", "#FFFFFF",
             "https://tarleton.edu/brand/university-colors", True),
    ColorFix(292, "UT Rio Grande Valley", "#F05023", "#0C2340",
             "https://teamcolorcodes.com/utrgv-vaqueros-colors/", False),
    ColorFix(3101, "Utah Tech", "#BA1C21", "#003058",
             "https://brand.utahtech.edu/ourlook/color/", True),
    ColorFix(110242, "West Florida", "#00205B", "#00A346",
             "https://uwf.edu/brand/color/", True),
)  # fmt: skip

_BY_TEAM = {fix.team_id: fix for fix in FIXES}


def corrected_colors(
    team_id: int, color: str | None, alt_color: str | None
) -> tuple[str | None, str | None]:
    """A team's (color, alt color): the correction if there is one, else CFBD's."""
    fix = _BY_TEAM.get(team_id)
    return (fix.color, fix.alt_color) if fix else (color, alt_color)
