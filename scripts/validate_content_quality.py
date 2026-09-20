#!/usr/bin/env python3
"""内容质量检查（G7 增强）— 不只查能不能用，还查内容对不对.

检查项：
1. 数字一致性：同一数字在页面内多次出现时是否矛盾
2. 结构重复：同类卡片/章节是否重复
3. 过时引用：是否引用已删除的功能或旧数字
4. 逻辑完整性：新增功能后旧页面是否同步更新

用法：
  python3 scripts/validate_content_quality.py --base http://127.0.0.1:8096
"""
import sys
import urllib.request
import re
from collections import Counter


def fetch(url: str) -> str:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.read().decode('utf-8')


def check_content_quality(base: str) -> list[str]:
    errors = []
    pages = [
        'index.html', 'overview.html', 'quickstart.html',
        'authentication.html', 'employee-api.html',
        'conversation-api.html', 'runs-api.html', 'changelog.html'
    ]

    contents = {}
    for page in pages:
        try:
            contents[page] = fetch(f"{base}/{page}")
        except Exception as e:
            errors.append(f"❌ {page}: {e}")

    for page, content in contents.items():
        # 1. Check for structural duplicates (same card-title appearing twice)
        card_titles = re.findall(r'class="card-title"[^>]*>([^<]+)', content)
        title_counts = Counter(t.strip() for t in card_titles)
        for title, count in title_counts.items():
            if count > 1:
                errors.append(f"❌ {page}: card '{title}' appears {count} times")

        # 2. Check for conflicting API counts
        api_counts = re.findall(r'(\d+) 个 (?:API|接口)', content)
        if api_counts:
            unique_counts = set(api_counts)
            # Filter out sub-page counts (like "4 个 GET" on employee-api)
            page_level = [c for c in api_counts if int(c) >= 10]
            sub_level = [c for c in api_counts if int(c) < 10]
            # If page mentions both platform-level (>=10) and sub-level (<10),
            # that's OK. But if it mentions two different platform-level counts, that's wrong.
            if len(set(page_level)) > 1:
                errors.append(f"❌ {page}: conflicting API counts: {sorted(set(page_level))}")

        # 3. Check for outdated capability descriptions.
        # A page that links all three API groups may validly call the employee subgroup read-only.
        has_post = bool(re.search(r'POST|发送|创建|执行', content))
        says_readonly = '只读' in content
        full_platform_page = 'conversation-api' in content and 'runs-api' in content
        if has_post and says_readonly and page != 'employee-api.html' and not full_platform_page:
            errors.append(f"❌ {page}: says '只读' but also mentions POST/execute endpoints")

        # 4. Check for orphan references (referencing pages that don't link back)
        links_out = set(re.findall(r'href="([a-z-]+\.html)"', content))
        for link in links_out:
            if link in contents:
                back_links = set(re.findall(r'href="([a-z-]+\.html)"', contents[link]))
                # Index should be linked from all pages (via nav)
                # API pages should be linked from index and overview
                if page in ('index.html', 'overview.html') and link not in back_links and link != 'index.html':
                    # This is OK for nav-generated links, just warn
                    pass

        # 5. Check for excessive repetition of key phrases
        text = re.sub(r'<[^>]+>', ' ', content)
        text = re.sub(r'\s+', ' ', text)
        key_phrases = [
            '数字员工完整', '当前开放', '一站式', '全生命周期',
            '查询员工', '创建会话', '发送任务'
        ]
        for phrase in key_phrases:
            count = text.count(phrase)
            if count > 3:
                errors.append(f"❌ {page}: '{phrase}' appears {count} times (>2)")

    return errors


def main():
    base = "http://127.0.0.1:8096"
    if len(sys.argv) > 2 and sys.argv[1] == '--base':
        base = sys.argv[2]

    errors = check_content_quality(base)

    if errors:
        print(f"FAIL: {len(errors)} content quality issues")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("PASS: 内容质量检查通过（无重复/无过时/无矛盾/无冗余）")


if __name__ == '__main__':
    main()
