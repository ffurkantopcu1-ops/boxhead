# -*- coding: utf-8 -*-
"""Git geçmişinden data/patch_notes.json üretir.

Kullanım (repo kökünden):
    python tools/generate_patch_notes.py            # etiketlenmemişler "Yayınlanmamış" olur
    python tools/generate_patch_notes.py 1.7.0      # etiketlenmemişler v1.7.0 başlığına yazılır

Her sürüm etiketi (v*) arasındaki commit mesajlarını conventional-commit
önekine göre kategorize eder ve en yeni sürüm en üstte olacak şekilde
data/patch_notes.json dosyasına yazar. Henüz etiketlenmemiş commitler
"Yayınlanmamış" başlığı altında listelenir.

Release akışı: sürüm etiketi atmadan ÖNCE bu script çalıştırılıp çıktı
commit'lenmelidir ki paket içindeki patch notes güncel olsun.
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, 'data', 'patch_notes.json')

# Önek -> Türkçe kategori başlığı (görüntüleme sırası korunur)
CATEGORY_MAP = [
    (('feat',), '✨ Yeni Özellikler'),
    (('fix', 'hotfix'), '🐞 Hata Düzeltmeleri'),
    (('balance',), '⚖️ Denge Değişiklikleri'),
    (('perf', 'refactor'), '⚙️ İyileştirmeler'),
    (('docs', 'ci', 'chore', 'test', 'build', 'style'), '📦 Diğer'),
]
DEFAULT_CATEGORY = '📦 Diğer'

# Bu commitler notlara girmez
SKIP_PATTERNS = [
    re.compile(r'^release v?\d', re.IGNORECASE),
    re.compile(r'^merge ', re.IGNORECASE),
    re.compile(r'regenerate patch notes', re.IGNORECASE),
]


def git(*args):
    result = subprocess.run(
        ['git', '-C', ROOT] + list(args),
        capture_output=True, text=True, encoding='utf-8', check=True,
    )
    return result.stdout.strip()


def parse_semver(tag):
    nums = []
    for part in tag.lstrip('v').split('.')[:3]:
        try:
            nums.append(int(part))
        except ValueError:
            nums.append(0)
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums)


def categorize(subject):
    match = re.match(r'^(\w+)(\([^)]*\))?[!]?:\s*(.+)$', subject)
    if match:
        prefix, _, rest = match.group(1).lower(), match.group(2), match.group(3)
        for prefixes, title in CATEGORY_MAP:
            if prefix in prefixes:
                return title, rest.strip()
    return DEFAULT_CATEGORY, subject.strip()


def collect_notes(rev_range):
    """rev_range içindeki commitleri {kategori: [mesaj, ...]} olarak döndür."""
    out = git('log', rev_range, '--no-merges', '--pretty=%s')
    categories = {}
    for subject in out.splitlines():
        subject = subject.strip()
        if not subject or any(p.search(subject) for p in SKIP_PATTERNS):
            continue
        title, text = categorize(subject)
        # Aynı mesajı iki kez listeleme
        if text not in categories.setdefault(title, []):
            categories[title].append(text)
    # Görüntüleme sırasına göre sırala
    order = [title for _, title in CATEGORY_MAP]
    return {t: categories[t] for t in order if t in categories}


def tag_date(ref):
    return git('log', '-1', '--format=%ad', '--date=format:%Y-%m-%d', ref)


def main():
    # Opsiyonel argüman: etiketlenmemiş commitlerin yazılacağı sürüm adı
    pending_version = sys.argv[1].lstrip('v') if len(sys.argv) > 1 else None
    tags = [t for t in git('tag', '--list', 'v*').splitlines() if t]
    tags.sort(key=parse_semver)

    versions = []
    prev = None
    for tag in tags:
        rev_range = f'{prev}..{tag}' if prev else tag
        notes = collect_notes(rev_range)
        if notes:
            versions.append({
                'version': tag.lstrip('v'),
                'date': tag_date(tag),
                'categories': notes,
            })
        prev = tag

    # Etiketlenmemiş commitler (varsa)
    if tags:
        unreleased = collect_notes(f'{tags[-1]}..HEAD')
        if unreleased:
            versions.append({
                'version': pending_version or 'Yayınlanmamış',
                'date': tag_date('HEAD'),
                'categories': unreleased,
            })

    versions.reverse()  # En yeni en üstte

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump({'versions': versions}, f, ensure_ascii=False, indent=2)
        f.write('\n')

    print(f'{OUTPUT} yazildi ({len(versions)} surum).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
