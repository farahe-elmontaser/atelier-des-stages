"""Test des vraies sources SANS Internet : on simule les reponses des API
avec le meme format JSON que les vraies.

Lancement :  python -m tests.test_offres_reelles
"""
from unittest.mock import patch

REPONSES = {
    "boards-api.greenhouse.io": {"jobs": [
        {"title": "Software Engineering Intern, Summer 2027", "absolute_url": "https://boards.greenhouse.io/stripe/jobs/1",
         "location": {"name": "Paris"}, "updated_at": "2026-10-01T10:00:00Z",
         "content": "&lt;p&gt;Build &lt;b&gt;APIs&lt;/b&gt; in Python.&lt;/p&gt;"},
        {"title": "Senior Backend Engineer", "absolute_url": "https://boards.greenhouse.io/stripe/jobs/2",
         "location": {"name": "Dublin"}, "content": ""},
        {"title": "Internal Tools Engineer", "absolute_url": "https://x", "location": {"name": "X"}, "content": ""},
    ]},
    "api.lever.co": [
        {"text": "Data Science Internship", "hostedUrl": "https://jobs.lever.co/spotify/abc",
         "categories": {"location": "Stockholm", "commitment": "Internship"}, "descriptionPlain": "Analyse data.",
         "createdAt": 1790000000000},
        {"text": "Product Manager", "hostedUrl": "https://jobs.lever.co/spotify/def",
         "categories": {"location": "London", "commitment": "Full-time"}},
    ],
    "www.themuse.com": {"page_count": 1, "results": [
        {"name": "Marketing Intern", "company": {"name": "Acme"}, "locations": [{"name": "New York, NY"}],
         "refs": {"landing_page": "https://www.themuse.com/jobs/acme/marketing-intern"},
         "contents": "<p>Help the <i>marketing</i> team.</p>", "publication_date": "2026-10-05T00:00:00Z"}]},
    "www.arbeitnow.com": {"data": [
        {"title": "Werkstudent Data Analytics (m/w/d)", "company_name": "Beta GmbH", "location": "Berlin",
         "remote": False, "url": "https://www.arbeitnow.com/jobs/beta/werkstudent", "job_types": ["Part-Time"],
         "description": "<p>SQL und Python</p>", "created_at": 1790000000},
        {"title": "Head of Sales", "company_name": "Gamma", "location": "Munich", "url": "https://x", "job_types": ["Full-Time"]},
    ]},
    "remotive.com": {"jobs": [
        {"title": "Frontend Developer Intern", "company_name": "Delta", "candidate_required_location": "Europe",
         "url": "https://remotive.com/remote-jobs/software-dev/frontend-intern-1", "description": "<p>React</p>",
         "job_type": "internship", "publication_date": "2026-10-06T00:00:00"}]},
}


class Reponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


def faux_get(url, **kwargs):
    for domaine, data in REPONSES.items():
        if domaine in url:
            return Reponse(data)
    raise AssertionError("URL inattendue : " + url)


def test():
    from app.sources import offres_reelles as src
    with patch.object(src.requests, "get", side_effect=faux_get), patch.object(src.time, "sleep"), \
         patch.object(src, "GREENHOUSE_ENTREPRISES", ["stripe"]), patch.object(src, "LEVER_ENTREPRISES", ["spotify"]), \
         patch.object(src, "MUSE_PAGES", 1), patch.object(src, "ARBEITNOW_PAGES", 1):
        gh, lv, mu, ar, rm = (src.source_greenhouse(), src.source_lever(), src.source_themuse(),
                              src.source_arbeitnow(), src.source_remotive())

    assert [o.titre for o in gh] == ["Software Engineering Intern, Summer 2027"], gh   # pas le Senior, pas "Internal"
    assert gh[0].description == "Build APIs in Python." and gh[0].entreprise == "Stripe"
    assert [o.titre for o in lv] == ["Data Science Internship"] and lv[0].lien == "https://jobs.lever.co/spotify/abc"
    assert mu[0].description == "Help the marketing team." and mu[0].ville == "New York, NY"
    assert [o.titre for o in ar] == ["Werkstudent Data Analytics (m/w/d)"] and ar[0].description == "SQL und Python"
    assert rm[0].ville == "Europe (télétravail)"
    for o in gh + lv + mu + ar + rm:
        assert o.lien.startswith("https://"), o
        print("OK :", o.source, "|", o.titre, "|", o.lien)
    print("Tous les tests passent.")


if __name__ == "__main__":
    test()
