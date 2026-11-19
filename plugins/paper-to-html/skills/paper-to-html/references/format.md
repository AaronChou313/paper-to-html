# 数据与命令

路径以本技能目录为基准。用 Python 3.10+。渲染器只用标准库。可选的 PDF 抽取脚本需要 PyMuPDF。下面是最小可运行示例，包含该纸面格式常用的段落选项。

```json
{
  "paper": {
    "title_zh": "室内移动机器人定位",
    "title_en": "Indoor Mobile Robot Localization",
    "source_lang": "en"
  },
  "blocks": [
    {"type": "section", "id": "abstract", "title_en": "Abstract", "title_zh": "摘要"},
    {
      "type": "paragraph", "id": "abstract-p1", "pages": [1, 1],
      "en": "Wheel odometry provides relative motion estimates.",
      "zh": "轮式里程计提供相对运动估计。",
      "notes": ["**轮式里程计**提供局部相对位移。"],
      "highlight_en": ["Wheel odometry"],
      "highlight_zh": ["轮式里程计"]
    }
  ]
}
```

- `paper` 可另设 `short_title`、`authors`、`publication`、`keywords_en` 与 `keywords_zh`（字符串数组）。`links` 是 `{"label":"论文 DOI","url":"https://doi.org/..."}` 形式的对象数组，只填已确认的链接。
- `blocks` 按真实阅读顺序排列。所有 `id` 唯一，以英文字母开头，其余可含字母、数字、下划线和连字符。
- `section` 使用 `title_en` 和 `title_zh`。可设 `level: 3` 作子节，默认 2。设置 `route_label` 可将重要章节放到标题下的阅读主线。
- `paragraph` 使用 `en` 原文、`zh` 完整译文及 `notes` 字符串数组。笔记内 `**短语**` 显示为粗体。可设 `pages: [物理起始页, 物理结束页]`，页码从 1 起。两类高亮字段都是与原文大小写一致的短语数组。`links_en` 或 `links_zh` 可为 `{"Fig. 2":"figure-2"}`，键需出现在对应段落，值是现有块 ID。
- `figure` 和 `equation` 复用段落字段，`title` 为显示标题，`image` 为图片路径。复杂公式用 `image`，简单公式也可用 `formula` 字符串。图、公式的 `en` 和 `zh` 保留出处中的图注或原文说明。源文无图注时用可辨识的原始标签。
- `table` 同样复用段落字段。填写 `rows_zh`，提供 `image` 或 `rows_en`。行使用字符串数组，包含表头，单位与表注不可遗失。表注及来源放在 `en` 与 `zh` 中。图片相对于 JSON 位于同一临时目录的任意子路径，支持 PNG、JPEG 和 WebP，渲染时会内嵌。
- `references` 使用 `title`（如「展开参考文献」）和 `entries`。每条参考文献含 `text` 及可选 `url`。可以在前面用一个 `section` 生成导航入口。
- 输入一律为纯文本。渲染器会转义正文里的尖括号和引用符号。正文换行用 JSON 的 `\n`。词组的高亮和引用跳转用块字段。

示例命令中的 <skill> 为包含 SKILL.md 的目录，临时路径仅作示例。

```sh
python3 "<skill>/scripts/pdf_source.py" inspect "papers/论文.pdf" > "/tmp/paper-blocks.json"
python3 "<skill>/scripts/pdf_source.py" crop "papers/论文.pdf" 2 "/tmp/fig-1.png" --clip 40 155 530 410
python3 "<skill>/scripts/render.py" "/tmp/paper-reading.json" "shelf/论文·双语精读.html" --source-pdf "papers/论文.pdf"
```

读取 `inspect` 的坐标时，原点在左上，单位是 PDF 点，`box` 顺序是左、上、右、下。用 `--pages FIRST LAST` 分批读取。`crop` 省略 `--clip` 可渲染整页检查。渲染器的 `--source-pdf` 生成相对路径链接，移动输出时保留两者目录关系便可继续使用物理页跳转。HTML 正文、图表、CSS 和交互均内嵌。
