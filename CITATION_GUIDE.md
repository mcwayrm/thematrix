# Citation Guide

This website uses a centralized bibliography system. All references are stored in `references.bib` and can be cited in any `.qmd` file.

## How to Add References

Add new entries to `references.bib` in BibTeX format. Common entry types:

### Article
```bibtex
@article{authorYear,
  title={Article Title},
  author={Last, First and Last, First},
  journal={Journal Name},
  volume={10},
  number={2},
  pages={123--145},
  year={2024}
}
```

### Book
```bibtex
@book{authorYear,
  title={Book Title},
  author={Last, First},
  year={2023},
  publisher={Publisher Name}
}
```

## How to Cite in .qmd Files

Use the `@` symbol followed by the citation key:

- **In-text citation**: `@authorYear` renders as: Author (Year)
- **Parenthetical**: `[@authorYear]` renders as: (Author, Year)
- **Multiple citations**: `[@author2024; @other2023]`
- **With page numbers**: `[@authorYear, pp. 42-43]`
- **Suppress author**: `[-@authorYear]` renders as: (Year)

## Example

```markdown
According to @example2024, this is important. 
Other research supports this claim [@examplebook2023; @exampleconf2025].
```

## Citation Style

The website uses APA style by default (configured in `_quarto.yml`). You can change this by:

1. Download a different `.csl` file from the [Zotero Style Repository](https://www.zotero.org/styles)
2. Save it in your project directory
3. Update the `csl:` field in `_quarto.yml`

Common styles: `apa.csl`, `chicago.csl`, `ieee.csl`, `nature.csl`

## References Page

All cited references automatically appear on the [References](references.qmd) page.
