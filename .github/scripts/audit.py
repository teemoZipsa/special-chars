"""
티모집사 도구 품질 검사 스크립트
GitHub Actions에서 자동 실행됩니다.
"""
import os, glob, re, sys

base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
errors = []
warnings = []

tools = sorted(glob.glob(os.path.join(base, "*/index.html")))
print(f"🔍 {len(tools)}개 도구 검사 중...\n")

for f in tools:
    tool = os.path.basename(os.path.dirname(f))
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    lines = content.split('\n')

    # 1. Footer 존재 확인
    if 'class="footer"' not in content:
        errors.append(f"[{tool}] ❌ footer가 없습니다")
        continue

    # 2. Footer CSS 존재 확인
    if '.footer{' not in content and '.footer {' not in content:
        errors.append(f"[{tool}] ❌ footer CSS가 없습니다")

    # 3. Footer가 <details> 안에 있는지 확인
    footer_idx = next(i for i, l in enumerate(lines) if 'class="footer"' in l)
    in_details = False
    for i in range(footer_idx, -1, -1):
        if '<details' in lines[i]:
            in_details = True
            break
        if '</details>' in lines[i]:
            break
    if in_details:
        errors.append(f"[{tool}] ❌ footer가 <details> 안에 갇혀있습니다")

    # 4. body align-items 확인 (하단 여백 방지)
    body_match = re.search(r'body\s*\{([^}]+)\}', content)
    if body_match:
        b = body_match.group(1)
        if 'min-height:100vh' in b and 'display:flex' in b and 'align-items' not in b:
            warnings.append(f"[{tool}] ⚠️ body에 align-items 없음 (하단 여백 발생 가능)")

    # 5. 상단 헤더 존재 확인
    if 'class="header"' not in content and 'class="app-header"' not in content and 'class="calc-header"' not in content:
        warnings.append(f"[{tool}] ⚠️ 상단 헤더가 없습니다")

    # 6. theme.css 연결 확인
    if 'theme.css' not in content:
        warnings.append(f"[{tool}] ⚠️ theme.css가 연결되지 않았습니다")

    # 7. meta description 확인
    if '<meta name="description"' not in content:
        warnings.append(f"[{tool}] ⚠️ meta description이 없습니다")

    # 8. 더 많은 도구 링크 확인
    if '더 많은 도구' not in content:
        errors.append(f"[{tool}] ❌ '더 많은 도구' 링크가 없습니다")

# 9. Sitemap 검사
sitemap_path = os.path.join(base, 'sitemap.xml')
if os.path.exists(sitemap_path):
    with open(sitemap_path, 'r', encoding='utf-8') as fh:
        sitemap = fh.read()
    for f in tools:
        tool = os.path.basename(os.path.dirname(f))
        if f'/special-chars/{tool}/' not in sitemap:
            warnings.append(f"[{tool}] ⚠️ sitemap.xml에 등록되지 않았습니다")
else:
    errors.append("[sitemap] ❌ sitemap.xml 파일이 없습니다")

# 결과 출력
print("=" * 50)
if errors:
    print(f"\n❌ 오류 {len(errors)}건:")
    for e in errors:
        print(f"  {e}")

if warnings:
    print(f"\n⚠️ 경고 {len(warnings)}건:")
    for w in warnings:
        print(f"  {w}")

if not errors and not warnings:
    print("\n✅ 모든 도구가 정상입니다!")

print(f"\n📊 검사 완료: {len(tools)}개 도구, {len(errors)}개 오류, {len(warnings)}개 경고")

if errors:
    sys.exit(1)
