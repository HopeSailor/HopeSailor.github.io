# Xiaochen Wang — Academic Homepage

Source code for [my academic homepage](https://hopesailor.github.io/), which presents my research interests, publications, academic background, and selected projects.

**Maintained by:** [Xiaochen Wang](https://github.com/HopeSailor)  
**Built with:** Jekyll and GitHub Pages  
**Upstream template:** [RayeRen/AcadHomepage](https://github.com/RayeRen/acad-homepage.github.io)

> This website is customized from the AcadHomepage template. The underlying template is **not** my original creation. The repository retains the upstream license and attribution.

## Site content

- [Academic homepage](https://hopesailor.github.io/) — profile, research news, and publications
- [`_pages/about.md`](_pages/about.md) — homepage content
- [`_config.yml`](_config.yml) — site metadata, author information, and Jekyll settings
- [`images/`](images/) — website images
- [`assets/`](assets/) — theme assets

## Run locally

1. Install a Ruby/Jekyll development environment compatible with the repository's `Gemfile` and `Gemfile.lock`.
2. From the repository root, install dependencies and start Jekyll:

   ```bash
   bundle install
   bundle exec jekyll serve
   ```

3. Open `http://localhost:4000`. You can edit `_pages/about.md` and `_config.yml` to update the site. Restart Jekyll after changing `_config.yml`.

Deployment is handled through GitHub Pages; the public URL is [hopesailor.github.io](https://hopesailor.github.io/).

## Credits and license

This site is based on [AcadHomepage by RayeRen](https://github.com/RayeRen/acad-homepage.github.io), which itself builds on the open-source Jekyll academic-homepage ecosystem. Please refer to the repository [LICENSE](LICENSE) and the upstream project for the applicable notices and credits. Site-specific biography, publications, and images belong to their respective owners.
