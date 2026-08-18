# Stappenplan voor Devotionals App

Name: Study Bible / Bayble 

Explanation of app: 
The app provides commentary, essays and Bible study notes for the Bible, where the reader can read the text and refer to these commentary, essay and notes. 

Explanation of script:
The script analyzes every markdown file which has either a tag `#biblestudy/devotionals/[biblebook]` at the top or bottom five lines, if not, the file is skipped. If the file does have this, then the `[biblebook]`-part in the tag indicates metadata of this file, namely in which book of the Bible this devotional is written. This is also clear from the title, which is in the form `[title] [chapter] ([abbreviation of Bible translation])`. `[abbreviation of Bible translation]` also needs to end up in the metadata.
Each markdown file is placed in a folder named `[biblebook]`. Images are renamed `[biblebook]-img-[01].[extension]`, where `[01]` of course is the index. If it is better for the app, then all images can be converted to PNG. Raw images can be converted PNG as well (but this hardly to never occurs), and images larger than 5 MB need approval from the user with a request to be downscaled to 500 DPI. All images are placed an `/images`-folder under `[biblebook]/`.

The script converts the markdown text to LaTeX, but not with the standard command `pandoc "Leviticus 4 (LSB).md" -o "Leviticus 4 (LSB).tex"` because that will cause result into strange LaTeX-code. 

## Instructions for conversions
The markdown files are written according to Bear-markdown.

### Chapters and Sections
Section Headings level 1, 2 and 3, indicated in markdown by the `#`, `##`, and `###` signs, respectively, are simply to be converted to the LaTeX `\section{}` and `\subsection{}` and `\subsubsection{}` commands. Section Headings level 4 and 5 are to be converted to `\textbf{[level 4 section title]} \newline \noindent` and `\textbf{[level 5 section title].} `. Notice that the period needs to be inside the `\textbf{}` part and that there needs to be a space after the period, without a linebreak. All sections should not be numbered, so in LaTeX this would be `\section*{}`. Every section and chapter should furthermore have the `\label[label_name]`-label so it can be referred to. 

Footnotes in markdown are referenced by `[^1]`, where `1` is the index of the footnote, and where the footnote itself is noted as `[^1]:` at the bottom of the page. This should easily be converted to LaTeX as `\footnote{}`. 
Boldface and italic should be marked as `\textbf{}` and `\textit{}`, respectively, and highlights in markdown which are marked as `==[text to be highlighted]==` need some custom LaTeX-command, because this does not exist as standard mark-up. Quotes, too—which are noted by greater-than symbols `>`—might need custom LaTeX symbols, which I have not found out yet. 

Hyperlinks in MarkDown are noted by double opening and closing brackets `[[...]]` and refer to the markdownfile with exactly this name. When code looks like this `[[(ESV) 1 Timothy|test]]`, it means that the text in the file should show "test", but that the link should refer to `(ESV) 1 Timothy.md`. This is converted to the `\ref`-command in LaTeX. Another format for hyperlinks is `[title](address)`. This format could contain external URLs, in which case the `hyperref`-package is invoked. In the case where internal Bear-links are used, e.g. [Isaiah 29:8](bear://x-callback-url/open-note?id=FA328286-7D5E-4F04-9AE1-E1E25DC9B1F2-13631-0000E508D93D61DC) this note should be searched for on the computer and the name of that file or file-section should then be looked up within the repository, and it should instead refer to the file found in the repository. 

### Images and Mermaid diagrams

The `graphicx`-package is used in LaTeX. By default captions and labels are added, and the other default settings are as shown in the code snippet below.

```tex
\usepackage{graphicx} % Modern graphics package
\graphicspath{ {./images/} } % Optional: Tells LaTeX to look in an "images" folder

\begin{document}

\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.8\textwidth]{my-image-file}
    \caption{This is my figure caption.}
    \label{fig:my_image}
\end{figure}

\end{document}
```

Mermaid-code for diagrams need to be converted to high-resolution PNG-files (300 DPI) before they are included in the LaTeX-file.

### Tags

