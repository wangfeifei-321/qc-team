#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PPTX 交付门：机械检查画布尺寸、页数、原生文字、图片数量、对象是否越界。

用法:
    python3 scripts/check_pptx.py presentation/QC-Team.pptx

退出码 0 表示全部通过；非 0 表示有项未通过，不应交付。
"""
import re
import sys
import zipfile

EMU_PER_INCH = 914400
TOLERANCE_EMU = 9144           # 0.01 英寸，容忍浮点取整
EXPECTED_PAGES = 10
MAX_MEDIA = 4                  # 2 张证据截图 + 缩略图等附属资源

OFF_EXT = re.compile(
    r'<a:off x="(-?\d+)" y="(-?\d+)"/><a:ext cx="(\d+)" cy="(\d+)"/>'
)


def check(path):
    with zipfile.ZipFile(path) as pkg:
        presentation = pkg.read("ppt/presentation.xml").decode("utf-8")
        size = re.search(r'<p:sldSz cx="(\d+)" cy="(\d+)"', presentation)
        if not size:
            print("✗ 读不到画布尺寸")
            return 1
        canvas_w, canvas_h = int(size.group(1)), int(size.group(2))

        slides = sorted(
            n for n in pkg.namelist()
            if re.match(r"ppt/slides/slide\d+\.xml$", n)
        )
        media = [n for n in pkg.namelist() if n.startswith("ppt/media/")]

        print("画布 %.3f x %.3f 英寸" % (canvas_w / EMU_PER_INCH, canvas_h / EMU_PER_INCH))
        print("页数 %d ｜ 媒体文件 %d" % (len(slides), len(media)))
        print("-" * 46)

        failures = []
        total_out = 0
        # 本机绝对路径不得出现在任何 XML（PPTX 会把图片来源写进 descr）
        leak_pat = re.compile(r"/Users/|/home/|[A-Za-z]:\\\\Users\\\\")
        for name in pkg.namelist():
            if not name.endswith(".xml"):
                continue
            hit = leak_pat.search(pkg.read(name).decode("utf-8", "ignore"))
            if hit:
                failures.append("%s 里残留本机绝对路径：%s" % (name, hit.group(0)))
        for index in range(1, len(slides) + 1):
            xml = pkg.read("ppt/slides/slide%d.xml" % index).decode("utf-8")
            boxes = OFF_EXT.findall(xml)
            out = [
                b for b in boxes
                if int(b[0]) < -TOLERANCE_EMU
                or int(b[1]) < -TOLERANCE_EMU
                or int(b[0]) + int(b[2]) > canvas_w + TOLERANCE_EMU
                or int(b[1]) + int(b[3]) > canvas_h + TOLERANCE_EMU
            ]
            texts = len(re.findall(r"<a:t>", xml))
            total_out += len(out)
            print("第%2d页  对象%3d  原生文字%3d  越界%d" % (index, len(boxes), texts, len(out)))
            if texts == 0:
                failures.append("第%d页没有原生文字，整页可能是位图" % index)
            if out:
                failures.append("第%d页有 %d 个对象越界" % (index, len(out)))

    print("-" * 46)
    if len(slides) != EXPECTED_PAGES:
        failures.append("页数是 %d，期望 %d" % (len(slides), EXPECTED_PAGES))
    if len(media) > MAX_MEDIA:
        failures.append("媒体文件 %d 个，超过上限 %d，可能又变成整页贴图" % (len(media), MAX_MEDIA))

    if failures:
        for f in failures:
            print("✗", f)
        return 1
    print("✓ 全部通过：%d 页、越界 %d、每页均有原生文字" % (len(slides), total_out))
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 scripts/check_pptx.py <文件.pptx>")
        sys.exit(1)
    sys.exit(check(sys.argv[1]))
