"""Automatisk retting av R1-07-jordskjelv-usgs.

Hver sjekk i SJEKKER er én deltest, og poengene fordeles likt på dem.
De samme sjekkene ligger i "Test løsningen din"-cellen nederst i notebooken.
"""
import pytest

from notebook_loader import last_notebook

def naer(a, b, rel=1e-3):
    """Sant hvis tallet a er innenfor rel (relativt) av b."""
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if b == 0:
        return abs(a) < 1e-9
    return abs(a - b) <= rel * abs(b)


def S(tekst):
    """Gjør tekst om til et sympy-uttrykk, f.eks. S("x**2 - 1")."""
    import sympy
    return sympy.sympify(tekst, locals={n: sympy.Symbol(n) for n in ("N", "O", "Q", "S")})


def lik(a, b):
    """Sant hvis a og b er matematisk like.

    Lister og mengder sammenlignes uten hensyn til rekkefølge, tupler (koordinater) i rekkefølge.
    """
    import sympy
    if a is None:
        return False
    if isinstance(b, tuple):
        if not isinstance(a, (tuple, list, sympy.Tuple)) or len(a) != len(b):
            return False
        return all(lik(x, y) for x, y in zip(a, b))
    if isinstance(b, (list, set)):
        if isinstance(a, sympy.FiniteSet):
            a = list(a)
        if not isinstance(a, (list, tuple, set)) or len(a) != len(b):
            return False
        rest = list(a)
        for y in b:
            for i, x in enumerate(rest):
                if lik(x, y):
                    del rest[i]
                    break
            else:
                return False
        return True
    if isinstance(b, dict):
        if not isinstance(a, dict) or len(a) != len(b):
            return False
        a = {str(k): v for k, v in a.items()}
        return all(str(k) in a and lik(a[str(k)], v) for k, v in b.items())
    try:
        a, b = sympy.sympify(a), sympy.sympify(b)
    except (sympy.SympifyError, TypeError):
        return False
    vanlige = lambda u: u.subs({s: sympy.Symbol(s.name) for s in u.free_symbols})
    a, b = vanlige(a), vanlige(b)
    if isinstance(a, sympy.Set) or isinstance(b, sympy.Set):
        return a == b
    if getattr(b, "is_Relational", False):
        return a == b
    try:
        return sympy.simplify(a - b) == 0
    except TypeError:
        return a == b

oppgave = last_notebook("oppgave")

SJEKKER = [
    ('1', 'magnituder skal gi listen med magnituder uten None', "list(magnituder({'type': 'FeatureCollection', 'features': [{'properties': {'mag': 5.6, 'place': '91 km SW of Tamarindo, Costa Rica', 'time': 1790805326296}, 'geometry': {'coordinates': [-86.3, 9.7, 10.0]}}, {'properties': {'mag': None, 'place': 'ukjent', 'time': 1790805326000}, 'geometry': {'coordinates': [0, 0, 0]}}, {'properties': {'mag': 4.7, 'place': 'Kermadec Islands', 'time': 1790801000000}, 'geometry': {'coordinates': [-177.9, -29.1, 35.0]}}]})) == [5.6, 4.7]"),
    ('2_amplitude', 'amplitudeforhold(7, 5) skal gi 100', 'naer(amplitudeforhold(7, 5), 100) and naer(amplitudeforhold(5, 6), 0.1)'),
    ('2_energi', 'energiforhold(7, 5) skal gi 1000', 'naer(energiforhold(7, 5), 1000) and naer(energiforhold(6, 5), 10**1.5)'),
    ('3', 'antall_minst([4.5, 5.0, 5.2, 6.1, 4.9], 5) skal gi 3', 'antall_minst([4.5, 5.0, 5.2, 6.1, 4.9], 5) == 3 and antall_minst([4.5, 5.0], 7) == 0'),
    ('4_eksakt', 'b_verdi([4, 5, 6], [1000, 100, 10]) skal gi 1', 'naer(b_verdi([4, 5, 6], [1000, 100, 10]), 1)'),
    ('4_annen', 'b_verdi([5, 6, 7], [800, 50, 3.125]) skal gi ca. 1.204', 'naer(b_verdi([5, 6, 7], [800, 50, 3.125]), 1.20412, rel=1e-4)'),
]


@pytest.mark.parametrize(
    "beskrivelse,uttrykk", [s[1:] for s in SJEKKER], ids=[s[0] for s in SJEKKER]
)
def test_sjekk(beskrivelse, uttrykk):
    navnerom = {**vars(oppgave), "naer": naer, "lik": lik, "S": S}
    assert eval(uttrykk, navnerom), beskrivelse
