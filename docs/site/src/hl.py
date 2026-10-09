"""Coloration syntaxique des blocs de code du site, faite à la génération : aucun script, le texte reste intact.

Langages couverts : JSON (y compris des échanges JSON-RPC fléchés), shell, en-tête YAML suivi de Markdown, Markdown,
échange HTTP. Tout le reste est affiché en texte brut. Un test vérifie que retirer les balises redonne le texte d'origine.
"""
from __future__ import annotations

import html
import re


def _esc(s: str) -> str:
    return html.escape(s, quote=False)


def _span(cls: str, s: str) -> str:
    return f'<span class="sx-{cls}">{_esc(s)}</span>' if s else ""


def _tokenize(text: str, pattern: re.Pattern, classify) -> str:
    out, pos = [], 0
    for m in pattern.finditer(text):
        out.append(_esc(text[pos:m.start()]))
        out.append(classify(m))
        pos = m.end()
    out.append(_esc(text[pos:]))
    return "".join(out)


_JSON = re.compile(r'(?P<arrow>->|<-)|(?P<str>"(?:\\.|[^"\\\n])*")(?P<colon>\s*:)?|(?P<num>-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)|\b(?P<kw>true|false|null)\b|(?P<p>[{}\[\],])')


def _json_cls(m: re.Match) -> str:
    if m.group("arrow"):
        return _span("a", m.group("arrow"))
    if m.group("str"):
        if m.group("colon"):
            return _span("k", m.group("str")) + _span("p", m.group("colon"))
        return _span("s", m.group("str"))
    if m.group("num"):
        return _span("n", m.group("num"))
    if m.group("kw"):
        return _span("b", m.group("kw"))
    return _span("p", m.group("p"))


def json(text: str) -> str:
    return _tokenize(text, _JSON, _json_cls)


_SH = re.compile(
    r'(?P<shebang>^#!.*$)|(?P<comment>(?:(?<=\s)|^)#(?!!).*$)|(?P<str>"(?:\\.|[^"\\])*"|\'[^\']*\')'
    r'|(?P<var>\$\{?[A-Za-z_][A-Za-z0-9_]*\}?|\$\()|(?P<flag>(?<=\s)--?[A-Za-z][\w-]*)'
    r'|\b(?P<kw>if|then|else|fi|for|in|do|done|exit|echo|while)\b', re.M)


def _sh_cls(m: re.Match) -> str:
    for name, cls in (("shebang", "c"), ("comment", "c"), ("str", "s"), ("var", "v"), ("flag", "f"), ("kw", "b")):
        if m.group(name):
            return _span(cls, m.group(name))
    return _esc(m.group(0))


def shell(text: str) -> str:
    return _tokenize(text, _SH, _sh_cls)


_INLINE = re.compile(r"(?P<code>`[^`\n]+`)|(?P<str>\"[^\"\n]*\")")


def _md_line(line: str) -> str:
    if re.match(r"#{1,6}\s", line):
        return _span("h", line)
    m = re.match(r"^(\s*)([-*])(\s.*)$", line)
    out, rest = "", line
    if m:
        out, rest = _esc(m.group(1)) + _span("p", m.group(2)), m.group(3)
    return out + _tokenize(rest, _INLINE, lambda x: _span("s", x.group(0)))


def markdown(text: str) -> str:
    return "\n".join(_md_line(l) for l in text.split("\n"))


_YAML_KV = re.compile(r"^(\s*)([A-Za-z_][\w-]*)(:)(.*)$")
_YAML_VAL = re.compile(r'(?P<str>"[^"]*")|\b(?P<kw>true|false|null)\b')


def _yaml_value(v: str) -> str:
    return _tokenize(v, _YAML_VAL, lambda m: _span("s", m.group("str")) if m.group("str") else _span("b", m.group("kw")))


def frontmatter(text: str) -> str:
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return markdown(text)
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return markdown(text)
    out = [_span("p", lines[0])]
    for l in lines[1:end]:
        m = _YAML_KV.match(l)
        if m:
            out.append(_esc(m.group(1)) + _span("k", m.group(2)) + _span("p", m.group(3)) + _yaml_value(m.group(4)))
        else:
            out.append(_yaml_value(l))
    out.append(_span("p", lines[end]))
    out.extend(markdown(l) for l in lines[end + 1:])
    return "\n".join(out)


_HTTP_REQ = re.compile(r"^(GET|POST|PUT|PATCH|DELETE)(\s+)(\S+)(\s+HTTP/[\d.]+)?$")
_HTTP_HDR = re.compile(r"^([A-Z][\w-]*)(:)(.*)$")
_HTTP_STATUS = re.compile(r"^(\d{3})(\s.*)?$")


def http(text: str) -> str:
    out = []
    for l in text.split("\n"):
        m = _HTTP_REQ.match(l)
        if m:
            out.append(_span("b", m.group(1)) + _esc(m.group(2)) + _span("s", m.group(3)) + _span("p", m.group(4) or ""))
            continue
        m = _HTTP_STATUS.match(l)
        if m:
            out.append(_span("n", m.group(1)) + _esc(m.group(2) or ""))
            continue
        m = _HTTP_HDR.match(l)
        if m:
            out.append(_span("k", m.group(1)) + _span("p", m.group(2)) + _esc(m.group(3)))
            continue
        out.append(json(l))
    return "\n".join(out)


def detect(text: str) -> str:
    t = text.lstrip()
    first = t.split("\n", 1)[0]
    if t.startswith("---"):
        return "frontmatter"
    if t.startswith("#!"):
        return "shell"
    if re.match(r"^(GET|POST|PUT|PATCH|DELETE)\s", t):
        return "http"
    if t.startswith(("{", "[")) or re.match(r"^(->|<-)\s", t):
        return "json"
    if re.match(r"#{1,6}\s", first):
        return "markdown"
    return "plain"


def highlight(text: str, lang: str | None = None) -> str:
    lang = lang or detect(text)
    fn = {"json": json, "shell": shell, "frontmatter": frontmatter, "markdown": markdown, "http": http}.get(lang)
    return fn(text) if fn else _esc(text)
