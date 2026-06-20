# latexmk config: XeLaTeX + BibTeX pipeline
$pdf_mode = 5;
$bibtex_use = 2;
$xelatex = 'xelatex -interaction=nonstopmode -shell-escape %O %S';
$clean_ext = 'bbl rel %R.is %R.if %R.44 xdv';
