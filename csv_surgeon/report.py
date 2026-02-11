"""HTML report generator for csv-surgeon analysis results."""

import os
import tempfile
from datetime import datetime, timezone


def _base_style():
    return """
    :root {
        --bg: #0d1117; --card: #161b22; --border: #30363d;
        --text: #e6edf3; --muted: #8b949e;
        --green: #3fb950; --red: #f85149; --blue: #58a6ff;
        --purple: #bc8cff; --orange: #d29922;
    }
    * { margin:0; padding:0; box-sizing:border-box; }
    body {
        font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;
        background:var(--bg); color:var(--text); line-height:1.6;
        padding:2rem; max-width:1100px; margin:0 auto;
    }
    .header { text-align:center; margin-bottom:2rem; padding-bottom:1.5rem; border-bottom:1px solid var(--border); }
    .header h1 { font-size:1.8rem; margin-bottom:0.3rem; }
    .header .subtitle { color:var(--muted); font-size:0.95rem; }
    .cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:1rem; margin-bottom:2rem; }
    .card { background:var(--card); border:1px solid var(--border); border-radius:8px; padding:1.2rem; }
    .card .label { color:var(--muted); font-size:0.8rem; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.3rem; }
    .card .value { font-size:1.5rem; font-weight:600; }
    .card .value.pass { color:var(--green); }
    .card .value.fail { color:var(--red); }
    .card .value.warn { color:var(--orange); }
    .section { background:var(--card); border:1px solid var(--border); border-radius:8px; padding:1.5rem; margin-bottom:1.5rem; }
    .section h2 { font-size:1.1rem; margin-bottom:1rem; padding-bottom:0.5rem; border-bottom:1px solid var(--border); }
    table { width:100%; border-collapse:collapse; font-size:0.85rem; }
    th { text-align:left; color:var(--muted); font-weight:500; padding:0.5rem 0.8rem; border-bottom:1px solid var(--border); font-size:0.75rem; text-transform:uppercase; }
    td { padding:0.5rem 0.8rem; border-bottom:1px solid var(--border); }
    tr:last-child td { border-bottom:none; }
    .mono { font-family:'SF Mono',Monaco,Consolas,monospace; font-size:0.82rem; }
    .badge { display:inline-block; padding:0.15rem 0.5rem; border-radius:4px; font-size:0.72rem; font-weight:500; }
    .badge-ok { background:rgba(63,185,80,0.15); color:var(--green); }
    .badge-warn { background:rgba(210,153,34,0.15); color:var(--orange); }
    .badge-err { background:rgba(248,81,73,0.15); color:var(--red); }
    .bar-bg { background:var(--bg); border-radius:4px; height:10px; width:100%; overflow:hidden; }
    .bar { height:10px; border-radius:4px; transition:width 0.3s; }
    .footer { text-align:center; color:var(--muted); font-size:0.8rem; margin-top:2rem; padding-top:1rem; border-top:1px solid var(--border); }
    .footer a { color:var(--blue); text-decoration:none; }
    """


def generate_html(file_path, file_size, total_lines, encoding_name, encoding_conf,
                   delimiter, delimiter_conf, expected_cols, column_mismatches,
                   quote_issues, preview_lines=None):
    """Generate HTML report for CSV analysis."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    total_issues = len(column_mismatches) + len(quote_issues)
    health = "HEALTHY" if total_issues == 0 else f"{total_issues} ISSUES"
    health_class = "pass" if total_issues == 0 else "warn" if total_issues < 5 else "fail"

    enc_class = "badge-ok" if encoding_conf >= 0.9 else "badge-warn" if encoding_conf >= 0.7 else "badge-err"
    del_class = "badge-ok" if delimiter_conf >= 0.9 else "badge-warn" if delimiter_conf >= 0.7 else "badge-err"

    delim_display = {',': 'Comma (,)', ';': 'Semicolon (;)', '\t': 'Tab', '|': 'Pipe (|)'}.get(delimiter, delimiter)

    # Issue rows
    issue_rows = ""
    for iss in column_mismatches[:20]:
        issue_rows += f'<tr><td>Line {iss.line_number}</td><td><span class="badge badge-warn">Column Mismatch</span></td><td class="mono">{iss.details}</td></tr>'
    for iss in quote_issues[:10]:
        issue_rows += f'<tr><td>Line {iss.line_number}</td><td><span class="badge badge-err">Unclosed Quote</span></td><td class="mono">{iss.details}</td></tr>'

    # Preview
    preview_html = ""
    if preview_lines:
        for i, line in enumerate(preview_lines[:5]):
            cells = "".join(f"<td class='mono'>{c[:50]}</td>" for c in line.split(delimiter)[:8])
            preview_html += f"<tr><td class='mono' style='color:var(--muted)'>{i+1}</td>{cells}</tr>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>csv-surgeon Analysis Report</title>
<style>{_base_style()}</style>
</head>
<body>

<div class="header">
    <h1>csv-surgeon Analysis Report</h1>
    <div class="subtitle">CSV Diagnostics &mdash; {now}</div>
</div>

<div class="cards">
    <div class="card">
        <div class="label">File Health</div>
        <div class="value {health_class}">{health}</div>
    </div>
    <div class="card">
        <div class="label">File</div>
        <div class="value" style="font-size:0.95rem;">{os.path.basename(file_path)}</div>
    </div>
    <div class="card">
        <div class="label">Size / Lines</div>
        <div class="value" style="font-size:1.1rem;">{file_size//1024}KB / {total_lines:,}</div>
    </div>
    <div class="card">
        <div class="label">Columns</div>
        <div class="value">{expected_cols}</div>
    </div>
</div>

<div class="section">
    <h2>Detection Results</h2>
    <table>
        <tr><td style="width:30%">Encoding</td><td><span class="badge {enc_class}">{encoding_name}</span> &nbsp; confidence: {encoding_conf:.0%}</td></tr>
        <tr><td>Delimiter</td><td><span class="badge {del_class}">{delim_display}</span> &nbsp; confidence: {delimiter_conf:.0%}</td></tr>
        <tr><td>Column Mismatches</td><td>{"<span class='badge badge-ok'>0</span>" if not column_mismatches else f"<span class='badge badge-warn'>{len(column_mismatches)}</span>"}</td></tr>
        <tr><td>Quote Issues</td><td>{"<span class='badge badge-ok'>0</span>" if not quote_issues else f"<span class='badge badge-err'>{len(quote_issues)}</span>"}</td></tr>
    </table>
</div>

{"<div class='section'><h2>Issues Found</h2><table><thead><tr><th>Location</th><th>Type</th><th>Details</th></tr></thead><tbody>" + issue_rows + "</tbody></table></div>" if issue_rows else ""}

{"<div class='section'><h2>Data Preview</h2><table><tbody>" + preview_html + "</tbody></table></div>" if preview_html else ""}

<div class="section">
    <h2>Recommendation</h2>
    <p>{"<span style='color:var(--green)'>File looks healthy. No repair needed.</span>" if total_issues == 0 else "<span style='color:var(--orange)'>Run <code>csv-surgeon repair " + os.path.basename(file_path) + "</code> to fix detected issues.</span>"}</p>
</div>

<div class="footer">
    <p>Generated by <a href="https://pypi.org/project/csv-surgeon/">csv-surgeon</a> &mdash; Intelligent CSV repair and sanitization</p>
</div>

</body>
</html>"""
    return html


def export_html(file_path, file_size, total_lines, encoding_name, encoding_conf,
                delimiter, delimiter_conf, expected_cols, column_mismatches,
                quote_issues, preview_lines=None, output_path=None):
    """Generate and save HTML report, return file path."""
    html = generate_html(file_path, file_size, total_lines, encoding_name, encoding_conf,
                         delimiter, delimiter_conf, expected_cols, column_mismatches,
                         quote_issues, preview_lines)
    if not output_path:
        output_path = os.path.join(tempfile.gettempdir(), "csv-surgeon-report.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path
