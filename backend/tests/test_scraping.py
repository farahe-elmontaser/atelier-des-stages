"""Test du scraper SANS Internet : on remplace requests.get par de fausses pages HTML
qui ont la meme structure que le site Fake Jobs.

Lancement :  python -m tests.test_scraping
"""
from unittest.mock import patch

PAGE_LISTE = """
<html><body><div id="ResultsContainer">
  <div class="card"><div class="card-content">
    <div class="media"><div class="media-content">
      <h2 class="title is-5">Senior Python Developer</h2>
      <h3 class="subtitle is-6 company">Payne, Roberts and Davis</h3>
    </div></div>
    <div class="content">
      <p class="location">Stewartbury, AA</p>
      <p class="is-small has-text-grey"><time datetime="2021-04-08">2021-04-08</time></p>
    </div>
    <footer class="card-footer">
      <a href="https://www.realpython.com" class="card-footer-item">Learn</a>
      <a href="https://realpython.github.io/fake-jobs/jobs/senior-python-developer-0.html" class="card-footer-item">Apply</a>
    </footer>
  </div></div>
  <div class="card"><div class="card-content">
    <h2 class="title is-5">Data Scientist Intern</h2>
    <h3 class="subtitle is-6 company">Vasquez-Davidson</h3>
    <p class="location">Christopherville, AA</p>
    <time datetime="2021-04-08">2021-04-08</time>
    <a href="https://www.realpython.com">Learn</a>
    <a href="jobs/data-scientist-intern-1.html">Apply</a>
  </div></div>
</div></body></html>
"""

PAGE_DETAIL = """
<html><body><div class="box">
  <h1 class="title is-2">Senior Python Developer</h1>
  <div class="content">
    <p>Build and maintain Python data pipelines with pandas and SQL.</p>
    <p id="location"><strong>Location:</strong> Stewartbury, AA</p>
  </div>
</div></body></html>
"""


class FausseReponse:
    def __init__(self, texte, code=200):
        self.text, self.status_code = texte, code

    def raise_for_status(self):
        pass


def faux_get(url, **kwargs):
    if url.endswith("robots.txt"):
        return FausseReponse("", 404)            # pas de robots.txt -> tout autorise
    if "/jobs/" in url:
        return FausseReponse(PAGE_DETAIL)
    return FausseReponse(PAGE_LISTE)


def test():
    from app.sources import scraping
    with patch.object(scraping.requests, "get", side_effect=faux_get), \
         patch.object(scraping, "SCRAPING_PAUSE", 0):
        offres = scraping.scraper_fake_jobs()

    assert len(offres) == 2, offres
    o = offres[0]
    assert o.titre == "Senior Python Developer"
    assert o.entreprise == "Payne, Roberts and Davis"
    assert o.ville == "Stewartbury, AA"
    assert o.lien.endswith("senior-python-developer-0.html")
    assert "pandas" in o.description                       # lu sur la page detail
    assert offres[1].lien == "https://realpython.github.io/fake-jobs/jobs/data-scientist-intern-1.html"  # lien relatif complete
    for o in offres:
        print("OK :", o, "|", o.description[:50])

    # robots.txt qui interdit tout -> le scraper doit refuser
    scraping._robots_cache.clear()
    interdit = lambda url, **k: FausseReponse("User-agent: *\nDisallow: /", 200)
    with patch.object(scraping.requests, "get", side_effect=interdit):
        try:
            scraping.telecharger("https://realpython.github.io/fake-jobs/")
            raise AssertionError("aurait du etre refuse")
        except PermissionError as e:
            print("OK : robots.txt respecte ->", e)
    scraping._robots_cache.clear()
    print("Tous les tests passent.")


if __name__ == "__main__":
    test()
