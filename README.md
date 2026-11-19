# 论文 → HTML

把英文论文整理为一个可离线阅读的双语精读 HTML。桌面布局左侧上方是英文原文、下方是中文译文，右侧是同一段的阅读笔记。页面沿用暖白背景、浅青笔记区和淡金高亮，支持章节跳转、移动端堆叠和「只看笔记」。

插件提供论文提取、翻译、术语统一、图表还原和校对的工作流程。AI 整理论文内容，随附渲染器统一页面结构和样式。图表、样式、交互都内嵌在一个 HTML 中，原版 PDF 页码可链接回本地文件。

## 安装

有 Codex CLI 时，可以添加此仓库作为插件源：

```sh
codex plugin marketplace add AaronChou313/paper-to-html
```

然后在 ChatGPT 桌面应用的插件目录中选择「论文 → HTML」并安装。[OpenAI 官方安装文档](https://developers.openai.com/plugins/build/plugins#add-a-marketplace-from-the-cli)

也可从 [GitHub Release](https://github.com/AaronChou313/paper-to-html/releases/latest) 下载插件 ZIP，在支持上传私有插件包的 Plugin Creator 中导入。

## 使用示例

在新对话中选中插件并提供 PDF，或在有工作区文件访问权限的 Codex 中指定 PDF 路径：

> 把 `papers/example.pdf` 整理成双语精读 HTML。每段英文原文在上、中文译文在下，旁边写简要阅读笔记。保留公式、图表和页码，输出到 `shelf/`。

渲染器使用 Python 3.10+ 标准库。可选的 PDF 文字块提取和图表裁切工具需要 PyMuPDF。数据格式与脚本命令见[渲染说明](plugins/paper-to-html/skills/paper-to-html/references/format.md)，论文整理步骤见[插件技能](plugins/paper-to-html/skills/paper-to-html/SKILL.md)。
