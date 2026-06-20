# 中文论文草稿 (Draft)

本目录用于存放中文论文各章节的 Markdown 草稿，供团队讨论和迭代。

## 目录结构

```
draft/zh/
├── README.md              ← 本文件
├── 00_abstract.md         ← 摘要草稿
├── 01_introduction.md     ← 引言草稿
├── 02_related_work.md     ← 相关工作草稿
├── 03_model.md            ← 问题建模草稿
├── 04_algorithm.md        ← 算法设计草稿
├── 05_experiments.md       ← 实验结果草稿
├── 06_conclusion.md       ← 结论草稿
└── notes/                 ← 零散讨论笔记
```

## 工作流程

1. **撰写草稿**: 在 Markdown 中自由撰写，不需要关心 LaTeX 格式
2. **讨论修改**: 通过 Markdown 快速迭代内容
3. **转换为 LaTeX**: 内容定稿后，搬运到 `paper/src/zh_conf/sections/*.tex` 或 `paper/src/zh_supp/sections/*.tex`
4. **编译论文**: 运行 `bash paper/build.sh zh_conf` 或 `bash paper/build.sh zh_supp` 生成 PDF

## 注意事项

- Markdown 草稿是**讨论用**的，最终提交以 `paper/src/<target>/main.tex` 为准
- 公式可以用 LaTeX 数学语法写（`$...$` 和 `$$...$$`），方便后续迁移
- 参考文献用 `[@key]` 或 `\cite{key}` 标注，后续统一整理到 `references.bib`
