#!/usr/bin/env python3
"""Build the static skill sharing page and QR code."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont
from qrcode.image.pil import PilImage
from qrcode.image.svg import SvgPathImage


ROOT = Path(__file__).resolve().parent
SKILL_PATH = ROOT / "SKILL.md"
REFERENCE_PATH = ROOT / "references" / "chinese-company-lookup-tactics.md"


def split_frontmatter(markdown: str) -> tuple[dict[str, str], str]:
    if not markdown.startswith("---\n"):
        return {}, markdown

    end = markdown.find("\n---\n", 4)
    if end == -1:
        return {}, markdown

    raw = markdown[4:end]
    body = markdown[end + len("\n---\n") :]
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        if not line or line.startswith(" ") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    return meta, body


def inline_markdown(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)

    def link(match: re.Match[str]) -> str:
        label = match.group(1)
        url = html.escape(match.group(2), quote=True)
        return f'<a href="{url}">{label}</a>'

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, escaped)


def is_table_separator(line: str) -> bool:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def render_table(rows: list[str]) -> str:
    header = split_table_row(rows[0])
    body_rows = rows[2:] if len(rows) > 1 and is_table_separator(rows[1]) else rows[1:]
    out = ["<div class=\"table-wrap\"><table>", "<thead><tr>"]
    out.extend(f"<th>{inline_markdown(cell)}</th>" for cell in header)
    out.append("</tr></thead>")
    if body_rows:
        out.append("<tbody>")
        for row in body_rows:
            out.append("<tr>")
            out.extend(f"<td>{inline_markdown(cell)}</td>" for cell in split_table_row(row))
            out.append("</tr>")
        out.append("</tbody>")
    out.append("</table></div>")
    return "\n".join(out)


def starts_block(line: str) -> bool:
    stripped = line.strip()
    return (
        not stripped
        or stripped.startswith("```")
        or stripped.startswith("#")
        or stripped.startswith("|")
        or stripped.startswith("> ")
        or bool(re.match(r"^\s*[-*]\s+", line))
        or bool(re.match(r"^\s*\d+\.\s+", line))
    )


def render_markdown(markdown: str) -> str:
    lines = markdown.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue

        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            code: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            lang_attr = f' data-lang="{html.escape(lang, quote=True)}"' if lang else ""
            out.append(
                f"<pre class=\"code\"{lang_attr}><code>{html.escape(chr(10).join(code))}</code></pre>"
            )
            continue

        heading = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading:
            level = min(len(heading.group(1)) + 1, 5)
            out.append(f"<h{level}>{inline_markdown(heading.group(2))}</h{level}>")
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and is_table_separator(lines[i + 1]):
            rows = [line]
            i += 1
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            out.append(render_table(rows))
            continue

        if stripped.startswith("> "):
            quoted: list[str] = []
            while i < len(lines) and lines[i].strip().startswith("> "):
                quoted.append(lines[i].strip()[2:])
                i += 1
            out.append(f"<blockquote>{inline_markdown(' '.join(quoted))}</blockquote>")
            continue

        if re.match(r"^\s*[-*]\s+", line):
            out.append("<ul>")
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                item = re.sub(r"^\s*[-*]\s+", "", lines[i])
                out.append(f"<li>{inline_markdown(item)}</li>")
                i += 1
            out.append("</ul>")
            continue

        if re.match(r"^\s*\d+\.\s+", line):
            out.append("<ol>")
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                item = re.sub(r"^\s*\d+\.\s+", "", lines[i])
                out.append(f"<li>{inline_markdown(item)}</li>")
                i += 1
            out.append("</ol>")
            continue

        para: list[str] = [stripped]
        i += 1
        while i < len(lines) and not starts_block(lines[i]):
            para.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline_markdown(' '.join(para))}</p>")

    return "\n".join(out)


def write_qr(url: str) -> None:
    svg_image = qrcode.make(url, image_factory=SvgPathImage, box_size=10, border=2)
    svg_image.save(ROOT / "qr.svg")

    png_image = qrcode.make(url, image_factory=PilImage, box_size=12, border=2)
    png_image.save(ROOT / "qr.png")
    (ROOT / "share-url.txt").write_text(url + "\n", encoding="utf-8")


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text:
        trial = current + char
        if draw.textlength(trial, font=font) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines


def draw_centered(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    font: ImageFont.ImageFont,
    fill: str,
    max_width: int,
    line_gap: int = 8,
) -> int:
    lines = wrap_text(draw, text, font, max_width)
    for line in lines:
        width = draw.textlength(line, font=font)
        draw.text(((1200 - width) / 2, y), line, font=font, fill=fill)
        bbox = draw.textbbox((0, 0), line, font=font)
        y += bbox[3] - bbox[1] + line_gap
    return y


def write_share_card(url: str) -> None:
    card = Image.new("RGB", (1200, 1600), "#f7f9fb")
    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle((72, 72, 1128, 1528), radius=28, fill="#ffffff", outline="#d6dde5", width=3)
    draw.rounded_rectangle((72, 72, 1128, 242), radius=28, fill="#eef6f4")
    draw.rectangle((72, 190, 1128, 242), fill="#eef6f4")

    eyebrow_font = load_font(34)
    title_font = load_font(74)
    body_font = load_font(38)
    small_font = load_font(28)
    url_font = load_font(26)

    y = 120
    y = draw_centered(draw, "Hermes Skill Share", y, eyebrow_font, "#0f766e", 900, 10)
    y += 52
    y = draw_centered(draw, "ToB 客户拜访 AI 背调", y, title_font, "#17202a", 960, 18)
    y += 28
    y = draw_centered(
        draw,
        "把公开信息转化为销售判断、开场话术和拜访验证问题。",
        y,
        body_font,
        "#344054",
        900,
        12,
    )

    qr = Image.open(ROOT / "qr.png").convert("RGB").resize((520, 520), Image.Resampling.NEAREST)
    qr_x = (1200 - qr.width) // 2
    qr_y = 650
    draw.rounded_rectangle((qr_x - 34, qr_y - 34, qr_x + qr.width + 34, qr_y + qr.height + 34), radius=24, fill="#ffffff", outline="#d6dde5", width=3)
    card.paste(qr, (qr_x, qr_y))

    y = qr_y + qr.height + 70
    y = draw_centered(draw, "扫码查看完整 Skill 内容", y, body_font, "#17202a", 900, 12)
    y += 8
    y = draw_centered(draw, url, y, url_font, "#667085", 980, 8)

    draw.rounded_rectangle((185, 1390, 1015, 1456), radius=12, fill="#eef3f7", outline="#d6dde5", width=2)
    draw_centered(draw, "包含 SKILL.md 原文、Prompt Pack 与中文企业查询策略", 1405, small_font, "#344054", 760, 6)
    card.save(ROOT / "share-card.png", quality=95)


def build_html(url: str) -> str:
    skill_raw = SKILL_PATH.read_text(encoding="utf-8")
    reference_raw = REFERENCE_PATH.read_text(encoding="utf-8")
    meta, skill_body = split_frontmatter(skill_raw)
    title = "ToB 客户拜访 AI 背调"
    description = "把公开信息转化为可验证的销售判断、开场话术和拜访问题。"
    version = meta.get("version", "1.0.0")
    license_name = meta.get("license", "MIT")
    author = meta.get("author", "Hermes Agent + Yves")

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{html.escape(description, quote=True)}">
  <title>{html.escape(title)} | Hermes Skill</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #17202a;
      --muted: #667085;
      --line: #d6dde5;
      --paper: #f7f9fb;
      --surface: #ffffff;
      --accent: #0f766e;
      --accent-ink: #063c38;
      --code: #101828;
      --code-bg: #eef3f7;
      --warn: #8a4b0f;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      line-height: 1.65;
    }}
    a {{ color: var(--accent); text-decoration-thickness: 1px; text-underline-offset: 3px; }}
    header {{
      background: linear-gradient(180deg, #ffffff 0%, #eef6f4 100%);
      border-bottom: 1px solid var(--line);
    }}
    .hero, main, footer {{
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
    }}
    .hero {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 240px;
      gap: 32px;
      align-items: end;
      padding: 44px 0 28px;
    }}
    .eyebrow {{
      margin: 0 0 10px;
      color: var(--accent-ink);
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 0;
      font-size: clamp(34px, 5vw, 58px);
      line-height: 1.08;
      letter-spacing: 0;
    }}
    .summary {{
      max-width: 760px;
      margin: 18px 0 0;
      color: #344054;
      font-size: 19px;
    }}
    .actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 22px;
    }}
    .button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 40px;
      padding: 8px 14px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--surface);
      color: var(--ink);
      font-weight: 700;
      text-decoration: none;
    }}
    .button.primary {{
      border-color: var(--accent);
      background: var(--accent);
      color: #ffffff;
    }}
    .qr-panel {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      padding: 14px;
    }}
    .qr-panel img {{
      display: block;
      width: 100%;
      height: auto;
    }}
    .qr-panel p {{
      margin: 10px 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.4;
      overflow-wrap: anywhere;
    }}
    main {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 260px;
      gap: 28px;
      padding: 28px 0 48px;
    }}
    article, aside {{
      min-width: 0;
    }}
    aside {{
      align-self: start;
      position: sticky;
      top: 20px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      padding: 16px;
    }}
    aside h2 {{
      margin: 0 0 10px;
      font-size: 17px;
    }}
    aside dl, aside dd, aside dt {{ margin: 0; }}
    aside dt {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      margin-top: 12px;
      text-transform: uppercase;
    }}
    aside dd {{
      color: var(--ink);
      overflow-wrap: anywhere;
    }}
    .notice {{
      border-left: 4px solid var(--accent);
      background: #eef6f4;
      padding: 12px 14px;
      margin-bottom: 18px;
      color: var(--accent-ink);
    }}
    section.content {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      padding: clamp(18px, 3vw, 34px);
      margin-bottom: 22px;
    }}
    h2, h3, h4, h5 {{
      line-height: 1.25;
      letter-spacing: 0;
    }}
    h2 {{
      margin: 0 0 18px;
      font-size: 28px;
    }}
    h3 {{
      margin: 30px 0 12px;
      padding-top: 10px;
      border-top: 1px solid var(--line);
      font-size: 22px;
    }}
    h4 {{
      margin: 24px 0 10px;
      font-size: 18px;
    }}
    p, ul, ol, blockquote, .table-wrap, pre {{
      margin: 12px 0;
    }}
    ul, ol {{ padding-left: 1.35rem; }}
    li + li {{ margin-top: 4px; }}
    code {{
      border-radius: 4px;
      background: var(--code-bg);
      padding: 0.1rem 0.28rem;
      color: var(--code);
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 0.92em;
    }}
    pre.code {{
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #101828;
      color: #f9fafb;
      padding: 16px;
      line-height: 1.5;
    }}
    pre.code code {{
      background: transparent;
      color: inherit;
      padding: 0;
      white-space: pre;
    }}
    blockquote {{
      border-left: 4px solid #b9c9d6;
      margin-left: 0;
      padding: 8px 14px;
      color: #344054;
      background: #f3f6f9;
    }}
    .table-wrap {{
      overflow-x: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    table {{
      width: 100%;
      min-width: 640px;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 10px 12px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #eef3f7;
      color: #263344;
    }}
    tr:last-child td {{ border-bottom: 0; }}
    footer {{
      border-top: 1px solid var(--line);
      padding: 18px 0 34px;
      color: var(--muted);
      font-size: 13px;
    }}
    @media (max-width: 860px) {{
      .hero, main {{
        grid-template-columns: 1fr;
      }}
      .qr-panel {{
        width: min(220px, 100%);
      }}
      aside {{
        position: static;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="hero">
      <div>
        <p class="eyebrow">Hermes Skill Share</p>
        <h1>{html.escape(title)}</h1>
        <p class="summary">{html.escape(description)}</p>
        <div class="actions">
          <a class="button primary" href="#skill">阅读 Skill 内容</a>
          <a class="button" href="SKILL.md" download>下载 SKILL.md</a>
          <a class="button" href="references/chinese-company-lookup-tactics.md" download>下载参考资料</a>
        </div>
      </div>
      <div class="qr-panel">
        <img src="qr.svg" alt="分享二维码">
        <p>扫码打开：{html.escape(url)}</p>
      </div>
    </div>
  </header>
  <main>
    <article>
      <div class="notice">分享说明：这个页面保留了原始 skill 内容和参考资料，适合发给同事、客户成功团队或销售团队扫码查看。</div>
      <section class="content" id="skill">
        {render_markdown(skill_body)}
      </section>
      <section class="content" id="reference">
        <h2>参考资料：中文企业查询策略</h2>
        {render_markdown(reference_raw)}
      </section>
    </article>
    <aside aria-label="Skill metadata">
      <h2>Skill 信息</h2>
      <dl>
        <dt>Name</dt>
        <dd>{html.escape(meta.get("name", "tob-customer-background-check"))}</dd>
        <dt>Version</dt>
        <dd>{html.escape(version)}</dd>
        <dt>Author</dt>
        <dd>{html.escape(author)}</dd>
        <dt>License</dt>
        <dd>{html.escape(license_name)}</dd>
        <dt>Source</dt>
        <dd><a href="SKILL.md">SKILL.md</a></dd>
        <dt>Reference</dt>
        <dd><a href="references/chinese-company-lookup-tactics.md">chinese-company-lookup-tactics.md</a></dd>
      </dl>
    </aside>
  </main>
  <footer>
    <p>Generated for sharing. If this directory is moved to a public host, regenerate <code>qr.svg</code> with the final URL.</p>
  </footer>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Build skill sharing page.")
    parser.add_argument("--url", required=True, help="URL that the QR code should open.")
    args = parser.parse_args()

    write_qr(args.url)
    write_share_card(args.url)
    (ROOT / "index.html").write_text(build_html(args.url), encoding="utf-8")


if __name__ == "__main__":
    main()
