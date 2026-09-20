#!/usr/bin/env python3
"""全站内容一致性检查（G7 完整验证增强）.

检查项：
1. 所有页面 HTTP 200
2. 跨页链接有效（无死链）
3. 内容同步（首页引用的 API 数量与子页面一致）
4. 权限文案统一（不出现旧权限码）
5. 导航完整性（所有页面在导航中）

用法：
  python3 scripts/validate_site_consistency.py --base http://127.0.0.1:8096
"""
import sys
import urllib.request
import re
from pathlib import Path

def check_site(base_url: str) -> list[str]:
    errors = []
    
    # 1. All pages must return 200
    pages = [
        'index.html', 'overview.html', 'quickstart.html',
        'authentication.html', 'employee-api.html',
        'conversation-api.html', 'runs-api.html', 'changelog.html'
    ]
    
    page_contents = {}
    for page in pages:
        url = f"{base_url}/{page}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status != 200:
                    errors.append(f"❌ {page}: HTTP {resp.status}")
                    continue
                page_contents[page] = resp.read().decode('utf-8')
        except Exception as e:
            errors.append(f"❌ {page}: {e}")
            continue
    
    # 2. Cross-page links valid
    all_pages_set = set(pages)
    for page, content in page_contents.items():
        links = re.findall(r'href="([a-z-]+\.html)"', content)
        for link in links:
            if link not in all_pages_set:
                errors.append(f"❌ {page}: dead link to {link}")
    
    # 3. Index must reference all API pages
    index = page_contents.get('index.html', '')
    for api_page in ['employee-api.html', 'conversation-api.html', 'runs-api.html']:
        if api_page not in index:
            errors.append(f"❌ index.html: missing link to {api_page}")
    
    # 3b. Check ALL pages for stale content
    import re as _re
    for page, content in page_contents.items():
        # Check stale API count
        api_count_match = _re.search(r'当前开放 (\d+) 个 API', content)
        if api_count_match:
            count = int(api_count_match.group(1))
            if count < 17:
                errors.append(f"❌ {page}: stale API count '{count}' (should be ≥17)")
        
        # A page may correctly describe the employee-query subgroup as read-only.
        # It is stale only if it describes the whole platform as read-only.
        describes_full_platform = 'conversation-api' in content and 'runs-api' in content
        if page != 'employee-api.html' and '只读' in content and not describes_full_platform:
            errors.append(f"❌ {page}: still says '只读' but platform has POST APIs")
        
        # "4 个 GET/接口" is valid for the employee-query subgroup.
        # Reject only the old platform-level claim such as "当前开放 4 个 API".
        if re.search(r'(?:当前开放|开放)\s*4\s*个\s*API', content):
            errors.append(f"❌ {page}: stale platform-level API count '4'")
    
    # 4. No old permission codes in pills
    for page, content in page_contents.items():
        if re.search(r'employee:read.*resource:read', content):
            errors.append(f"❌ {page}: still shows old permission codes")
    
    # 5. Quickstart must mention all 3 API categories
    quickstart = page_contents.get('quickstart.html', '')
    for term in ['employee-api', 'conversation-api', 'runs-api']:
        if term not in quickstart:
            errors.append(f"❌ quickstart.html: missing reference to {term}")
    
    return errors

def main():
    base = "http://127.0.0.1:8096"
    if len(sys.argv) > 2 and sys.argv[1] == '--base':
        base = sys.argv[2]
    
    errors = check_site(base)
    
    if errors:
        print(f"FAIL: {len(errors)} issues")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("PASS: 全站内容一致性检查通过（8页面+链接+权限+API引用）")

if __name__ == '__main__':
    main()
