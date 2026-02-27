# My Quarto Website

This is a Quarto website hosted on GitHub Pages.

## Local Development

To preview your site locally:

```bash
quarto preview
```

This will start a local preview server at `http://localhost:3000/`.

## Building

To build the site:

```bash
quarto render
```

This generates the static files in the `_site/` directory.

## Deployment

The site is automatically deployed to GitHub Pages when you push to the `main` branch via the GitHub Actions workflow defined in `.github/workflows/deploy.yml`.

## Editing Content

- Edit `.qmd` files to add or modify content
- Update `_quarto.yml` to change site configuration
- Add custom styling in `styles.css`

## Resources

- [Quarto Documentation](https://quarto.org)
- [Quarto Websites Guide](https://quarto.org/docs/websites)
