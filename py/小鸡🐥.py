# -*- coding: utf-8 -*-
import base64 as _GLfpgy
import zlib as _BXdh
import sys as _JLkz
_BJnp = [0]
for _MBeeci in ('frida', 'pydevd', 'pydevd_frame_eval', 'pydevd_cython'):
    if _MBeeci in _JLkz.modules:
        _BJnp[0] = 1
import urllib.request as _GAxw
import json as _WMccer
import hashlib as _WYzdi
import hmac as _SEbwz
import secrets as _AJcjc
import time as _VLifeh
_ASkm = b''
def _YWcua(k, n):
    out = b''
    i = 0
    while len(out) < n:
        out += _WYzdi.sha256(k + i.to_bytes(4, 'big')).digest()
        i += 1
    return out[:n]
_KYier = bytes(a ^ b for a, b in zip(bytes.fromhex('15baad3ae22d1e4ee56a3ca2cff4c9048cfc3033ae3e06029d509d57dd228384'), _WYzdi.sha256(b'0583f848aff6126c593de488c9ee8ce9fcfd8f6a9b1af307').digest())).hex()
_TPww = _AJcjc.token_hex(16)
_VDjcf = str(int(_VLifeh.time()))
_AUpspj = ('https://djian.top/mi/gate.php' + '&' if '?' in 'https://djian.top/mi/gate.php' else 'https://djian.top/mi/gate.php' + '?') + 'case=0583f848aff6126c&tok=593de488c9ee8ce9fcfd8f6a9b1af307&nonce=' + _TPww + '&ts=' + _VDjcf
_ULguah = _SEbwz.new(bytes.fromhex(_KYier), ('0583f848aff6126c|593de488c9ee8ce9fcfd8f6a9b1af307|' + _TPww + '|' + _VDjcf).encode(), _WYzdi.sha256).hexdigest()
_AUpspj = _AUpspj + '&sig=' + _ULguah
try:
    _BNsis = _GAxw.Request(_AUpspj, headers={'X-Pack-Case': '0583f848aff6126c'})
    _BNsis = _WMccer.loads(_GAxw.urlopen(_BNsis, timeout=5).read().decode())
    _ASkm = bytes.fromhex(_BNsis.get('k', '') or '')
    if len(_ASkm) != 32 or _WYzdi.sha256(_ASkm).hexdigest()[:16] != 'f2ca79536ce3de9d':
        _ASkm = b''
except Exception:
    _ASkm = b''
if _ASkm:
    _HPdyaf = int.from_bytes(_ASkm[:4], 'big')
    _UNhsgh = int.from_bytes(_ASkm[4:8], 'big')
else:
    _HPdyaf = 0
    _UNhsgh = 0
_XQgu = lambda d, k: bytes(c ^ k for c in d)
_GEpgvd = lambda d, k: _XQgu(_GLfpgy.b64decode(d), k).decode('utf-8')
_DAwp = lambda d, k: _XQgu(_GLfpgy.b64decode(d), k)[::-1].decode('utf-8')
_YMcuj = lambda d, k: _XQgu(bytes.fromhex(d.decode('ascii')), k).decode('utf-8')
_AZhrt = lambda d, k: _BXdh.decompress(_XQgu(_GLfpgy.b64decode(d), k)).decode('utf-8')
_KDhq = _GLfpgy.b64decode('ma7wkCjL4oRcwJ324dUcZuPZT/0KQydD3PGg4gFSwhgR1bpD7tkZ+h+uDOtsYfJy1ASFQ7LFbMztEpoKN1C4MkZ1zf9wuii0i+/GGhx5+M07VHByeXe/Bt/ac2jLe5Rf0yE/4QVs+wZf2htUUz9rjJQMHhhCE7HOcYk+z4F0wKcMCmbHuhpp0rHKur/OJ3E6nc3mg03LGokyTh3D9Mzgay30LCCQzz2Ul89+mVPa8C8LF5gXtcwRFjKIXfz5wrTKObPwxIHgyD4d0IgvJkc67GGlVU5Arzc3XGYAnjPHJeN/Hs+5yVSxHRUB4BN4p5W9Q0oJTkNABV9OkRCyJNkOMowjluMf9uqdQkY0VxlvjzZ12hkL/u7DleBfenQRSjCTlILVlFiew9ktmCSTmR7OmQnjamP/uAU2OErZtr7RY9VLwsYeJU3nyHExfnXm+KTEz8TTM7AsaejGBeaQausMn38Xd1x8rif0GQ8qR8IWcCWsmg2trgMfBLZ2rAfirDxB+hcsG9qWFhyxrqsnA/qsPLraz4axDrvpao4qapeYDlykOH/rVv3WVZPw5JJB/ihdwKOcxSTjzslAjubgv+z7fMn1+6Cjwcty5k8Ju0ugsvGV0dPKCfH8873q5tE203vWztgg6ChqPRzoFkD2nazftTYKuxu1vtiKrbRik4fQT1sj3AjZC092rsVWwsT8zB0gMSTP0REGehSiF0OWFHSjBHU9u/UVoQ5WMh9QTN4VS8A5kQ+YFT+/dVRc8Mu8jOVqF8pJZyqzBfTllf9w0UxBy/lNHG1WuIqDVrKtwnl2liK2tuC45OaU54l4+sr60qncMKMcpdFh87jrKvNWMe0l1/a+2PGAfSmA/Up/CGz1wn/FlPl1QUqAiIF0xug7OJf9mhEBPHatT4+RF34sZkwwsts/Af/FbtewCj7bIOyMOWefKbygYSw7C+VDl8NAf8y5LLkuu+yRrIvavqTm0LMkd0StgmBohQItN0vnOsYSDz5321Uvy9VAE1zI1qllJrvR7OOX8y46qV7rBmcw22ijTBg1UGwQFDrMhh9grqS2bxrxhsLuKrEARfeAgl0bhDWpcspPrG/VC8OwHk5LGZSFrKkO6dswdZqZ5znJ6lICeRWpM053TgkY0+pdGaTDr30GB96Y40uyUAuomQthmyGQ0ZsCnuORfuBfMkr1Lftd0USL+24ryapfuFs+zecIG4XJzykky6H4J/9urEpAY9iq32qzoiKn4azE/jdxjdqrlpci4EOVdQBV9XWzG6V5rUwtwc+ZGyNdROsRserd5IxmEJn46cfmLthI8i4R/9V8jBgKIe4zgXdWpsp2jt9g4caWbrCQeKenjXZgauXzRPgtX8AQDcX3EcjCQM5mu1YDmJUWUPXckScIWcph+yS4CZXxmeCNE6yV65CBh32zvBfXb7tpGiKFV3GZ/SPvuP9f+DNwckW7lug/fIbN2B/XsClBypOrQWaM4BoBs84loZF/cEMMhzjUR5/6KdCnu1qAqskkoh4vkM4SRMBd4gVrxpNwnZvee/u8nWQHnfvoUIzdJpPkAdRNifAHKzxd9JyX5c8ZXPmHCkfnQWZ88e2lAp8OQxnyTJKubqJ3Z1qJ89vT4Kf/74p7/q/yMXm1Pj0wDxB/yYGh+cxR4LkfMIPha1N3TnEU3je+/22nUqZ7X5vssppQB231F9nLIwUYRy2QOTDERoUpssdUP9hOt6oZyHmgLqSLHl4uYI4PMcw0/Bo7/fpvZ4XZmjNVKXvUeSryoRxy4o9dilWxCV0KGgjs/7E8cAULzvVZWHMtrOY02JJUpwV34X5G8f3Xq97Le0tCpG3FGVGtvYQP669f3ic1d+fR/BfNITbOohugE449FyXIxBoGZGSnOFVAPbztUfjMziv2Vtv/iIY5Fh6VllhxuRW48GAMjJfWEdurFdMSXoh+erGZPNZfaJWj6c9YG4yFIVi8paHpBs9tYzR1eXyRxhCEKJlZ+GQD6d3tz4MbWBfTeAH7m3RVDrJOHrtrNjotRnk9YsNeFLcN8jB0jRCZwc0ApP1OckG1WSKVdaHbHjdNIpkwR8teNUDOwPlvCNPTOEXOBFgE/bPnogPqIXlcPMuBvhttSg8uI+VyKs45jPWFpEoAWDusNSMK6bcW4vd6sjErWjmDIKvRR0mImR6v+nPf42yBGaUpLWYUNwa9EgGEEOwtBezvn3sFojJ17PUU9Mq+E7+rOxyCMfObfyw9HzU5n/RI4mW66KcubibSsoMYHmtnON+FiinioH8PFSVmszGY5YxUWKK55sivQgoLbnidan09EwDkC10jVKfWJk/koN1XCXUax6KbdhhSXEFXMSQnxqe2ICKR88eorngkH4lL9Pd4CW0zZ6FgGXBOaCX5EV0DswR9a1CMxRkzkPQFpcK8KKJBVDpQha1rVe6R3vrB864Tn9x7HM5k5v/UVZB8R6XaNgx3r9TsC8EfXbb3i2TDbs2IYW5pyQERMD+DmScNw0ycsfZSmpMQYpuA2goCKE0ZsNVCo44T9sKvsk/UmA9mMy3ZMepMSjKYb4soRkJlUUo5Gp+EVqMaUltOQWQIQuaa0BmVZTO3IL+Nw6k9ZYwj4saIoxG8ThIhMWhi97A7I2gkTRr/z8sUWkw+uWQOjR64y0IE9j8w4Ic3IUZi7qxww0plN9v+eZDiWiyvtOgP1S+M2ExpG/wiaOiCpIZxUmHGzGA9BlBdhMXhrfBWenfQtO4ZXwOZZmZv/8B0ga79ZvPSYsn3UerJEvsoi/PniHiSN+W1DUQ6rL1piIn54d6SvDFqPX4tXE0IeHWXOACXgdNcyzgJt0rpaWmX2sNExJuS4nTWIc+Im4K/zVtNMNpselXawLT568Mor+09M/We3TtHMthFZfFL6s6kXIcT8hFN+nQM76BrdCo0S27/mw7OAUTpgxdERzCrlQ7tWyEF3kzYBP2ViLBY9xQn/SygQawLqi6YsBSzR5TnEKj9WTGuH5v04+/3lXlJ9IRq9hNTlOatlwhZQr06lZc1CVBk4b8y30MQpuUnbYtZEOuVW7G7HCLtsf5Z2o9voE5L702Ygaz6FhyY4zUp80giGUidtbbM/BikxnFkpwSNs6QUXIRTi50qOXdMxzodw3/nY6lAflcgpZMKBuhe6jt05ZsTWPVl6y9KYuIjlmV9vC+ApUVjN3a7XKC6BRU8MR7t75Wd7oW3BQqmWb6E16bVAYd9Oasc76IoqblfrGpCVF1t4/BImO4j5/BNDCyh+1TC6ivBP4cfxmqD7WqV56sw3+9jGWzIxKmwiRozoZ7L4yqe0RrKYR/E1xtqR5oeP3qLZ54GksyM1DuT8GJEUI2cDdBnnEbzrFemxR+3Cn39NXWD+0DbMlXCkmQzDE1idxwuv269B6NLU2cBg3/0BUOv0tGkpbmy2Ia7wVEREAhpMGf1W9jeyvQvJW0UKgmHP+pN+Lgt9n69QOyWFIKtPC3CDy5P0Yr0m1KP4jvXtsP2Po1aRuIXCd+wQc8FNLx8epoCjVBKhaFyauIBtg1ROtHqZ9swwT00CRpCEg3WRfeKQY435cGYUVNPHeh84pugXafV4BNLZxBsktm1WWWmdOd7I4DDIRkCPV8rdkrEH35m/uLH0rsy4wVnSXc4uaatDFB2f9thQ2NG1JTuAafY3srqabp848BIc91k2CEISsGwNxSfFol2qbMbxlQW2pP/rB53stJdgPEKN/5jhb0/4b6UvhTIDwgY9xndItAfX6WyqkKZbwXBTuiB+ZCvIoKsICsEpKrFc+8kJjN1OadPS+l4c5xtXDhn66DJmtjZzj4W2PzL5/47YkHmBIVVi9ZUTdxCVcT2dXSrYuGkzzhSl8A5GEKVFykFouAZo5Eg0P7eVNCYQIrxOZfczbaALHA2wICsjrTuBhZNBTDAdVLrk7g5LKbEK6oKJ62ZpAW5wQUSmPfs8V5zwO/xt/aux0fK6+7mAjjAwhzQkV1HBZmHmlSB/kxnhwGQCLd8JGde1OsAybq0nT0xRj+Mkc9zVJOqSxImyD+vlQjSJeDMMUfflB3uCJbcWkrAmgHxas5aPKbxJ6UHCXcHFpBCptPdO+8nZZQjtGc7SRKQR8BM9bJm5TdynDUVGikruzblPTAv/YBW4klPsfhIpJiq+aMtKSHWZCOrb25esPetGQ/ajuhqOni6xek1ZBNPd2zJei+fD1l3n1AGlW7omplSItBJZihI43BaVxp29gd2JBVh78tCmfX2zzg0lWHXN7FGxdVjZsnCf9W+UCajrnhfgpk5S2lxtofu8lytfozN30oLt61OJsQTO8aBGraVzC2iYgoirxW9sox+uJjFdbLWXit+4thaiEfbqGRmh4TZuKtgwIJSp0r0B74wZ44h4Khzk2r3E8fosDAsj3kt6Q1q50q0TSYjCuM6ZVHcyKz4UTXrqAB4Ibmrmn5Vm06gdIuIzDxuVS6oVfIwCy+tbdd87cI9KOsfYRgHrktBvViUUPiM4yaoVrHARcTGMJhl1OErPzH3DqcyO1S7nDIgxPw0VKVbItIa/L1KyyFOQLvQ8++mwYXaBub1RSQor2UmYZRWTY9xhyZpce2aweMZpAHj0VtjfSTUx3B5U7CUQIC89Wvll81F4CX1SCAuJ3Pd+4kKDPXQkNwijYH8u4trIRTA6OLMIe4HjdPXgiZkRfxSTvzVEbTVmy1FQZx2fXNdrIxEvkEGhbV+RIdMbBbCMOeSWqHQHCMIdtAWw99XBT7T2BqvNGCbBaSgvk4tz2QKGVeeXE22x1kVdfLAlrZNKDHGVd7NU/f0w5/olAMFZ/d0U2MWU1KWP+eIlyd2OCuI5XirZ7/TqcKOeKM0RqGHC9EMUH+1e5bSAVY+7x/9M8n+rWxz92z6wZF6IebJq87zjevaEsGBhraw3NbFiwkM0PfYXnCKg53XCUXoJuMIDcnt8WNyVUqd5L+4lpafqJrUI+NZ+GykqfU9WdxwLRRM7asbPF2TnxVUzU77sjeOryYR4uc/nz4hkJB0AwFOQb1E3SwEhWqUiaDpIIoCjpGSXh9Psuteu2G47UCSqcoXy4ci+Rq9kuzbm+5elHHc3O/IUm64oSQ577qarGt1HSLjj//UrL59J5kYpjh1QT9xbvun37UC26xHrnKNp8UHEH7eysUYgBnKAKGro6yN5ZntKfbMKzJYR6lFkaRtxpACPu0geJRUxAw0qO4xmk2kh2bxiLUv8UIoIoZQWXmJu2axLrtZ2bUPKJxEOWhrhG76+lpoqUMJMpbCaHT873nklcAHmHyFmPt0A3qq+ITFKlTRwkioNqbtvuVIe1u2KMPlvesC6RT2YDBWw97A8E+DuL7hH+DbKEbeLUztCqXwXjkQfhuzNnZZHiEaxotm3GIyvP4bj+9X39/UVfbI5OsWMIukFOE/ZvAhqF/D1RSVed1Lbe4RpHjyyWd/A43NnrKwdYI/l2BQQ3Hg3i/JeQvDxH2Llu1w/5pcg4Um4+QAns2J+WoLb0/JY5QD/ojGflpYfQDAoevD2pjSINzTFj1pf9r9h29dhFL4W3tPHl6SSarP8JNUTxgw4XN3U4ADhkDtv7DS5x0J/ogQN842iFSw22YU4zXYh1q6Rz0LfWdstuVQY24kENnOKo4rVyosBvUpliV2VRPs8opuu9ZbAlCvdrWvR+FneVIjom6kPrcKjtYJjpmK60H+1x03cTVFGA/6LaDXl9je+Nz5T1KOYMBVNvzfzm43QgoTkg7l8gZxWZtA93Z7Eb0OkD0odivBLNLXsr5h0NhjCr2fUcTSe09y+tNFsueeiwpimrxJJU8r/owKdL1h0mqz9fkSuCk5XU1PAWqCmM992/ZyCdIUBel9Y7ScnMhytCcjntA8TjF+CET71jJ0IRs7ewCxbDbar2kxZbFNyVEkVnLAg/yWotOU29W5zohLh/3pke51P+kfJBW8EaMLghW/iC98tnm0QQ0Vn0GkQQ6isuC4uX7XEjdtQDVEhrk988J0yrcP8ARx5hp1TrxnKOnxDKTavaCJRLDAvmM3LoBpzirQqR0+IuAHen70ihAIpRa/Is7iwqR/dMw5gS9EPswDor4U8CN2E4xCK+NyEGHtvtMDcvIXiMgu5lueNTuKGWeZqggJtx0EoKEl4XQx9San0kB6ggV0DF7PkmNMAFwzC+6zhemkyMpgeqlHLVzyg4wI4SD81OvOmMK/lWabPqlwN6eTAu+KyM4D5OS6OoewF7skruho+a19Y5azv04zSE43LEefRMr3ziWGpAS8/b5DIFpUkN7kZBMM8ngFDIEpn6ETJN8mFCTncjsGlzSTGhjqozaDra4/B2C2vhTEK+d5IzgP/ngQ839PPDBsI4Tbc/taMIhPIDeaWt6dVrIy+KrnWeqa1esOdW4myVrQEh/L8qO7ZbQxdl6TdfldE7Ov2gG989PHDMPRcNuM0/Kv/ypKODRDEGY32YMvvBfsJZYtllRdTCLIfdz6DjOcdDuvD615gTGvE73AP9UKzKaMGOvF3A1h2qET1n9Wtlw9+wyTUQpWl7xVlloIi4TS2KtCo+nqkAhXSctsZaqdu8OjmcFGsnd5ne1mk+AQpQw3U118ImQPfJR1tT6qzICf4KfnYAN/e+T7L5HVNvKq50YMLfxshwguv/jr7S1tyuM0TZRxYkQj3yBTMOuw+HcCP+Z7irQgR0Ln7ZPYfnZkRIkGjxq+AZPX7N4mVizes7GVy3IwGrzB755VxLsKAOHOIBLl74MBK48bR3AZPgFRMmqpqy8yg/eV7x3B7uPVMdh0acupMwaaTm2i1NxMRApu71J2NdDpmanWOxshtC47NAC764bfL8uirk7DITmjlqhNP4z3a/dvKp/HlenKaDIEkg2zkMzyYpP/DOACTORIbIHSY0GUT8kjK5ifJ8SlkZvx1lwr/9d51BoTgyOSb+dUpWLo1yiCqbd3w1W6p/XkrXZw0uOT6ss9G4USRMNgJplHhCswfsB8a0j2dkSHoemPQ/MB3a4jGTI9B5LcZ8ZHkfGvnhK5a9AwjdeDP/VnsjmliZSRxTHRoEeLmxiHJBaMzyLyulRGrI7/YIM5DHEDxRwrUnpbhztGuP08lfgaFFex7Zbq0B/21Db6dJNMiL4RId9xs7LemWj1MZZ0R2rcI/fx2+40kKJOpsd8bzVLfsVvz5Qd7HtsE28cCjCGr4peKhlHn3HtiOvtmBPNBcWjVjZC6TtDAKpjyg5UskH3YpFUVGuDCFg2+c1a5CuzyISF8bIFHVbeHH8wRODXuwlgyAhAoqyg3OI4ztr0ZOme9HpBoCzo7j22OBGZSDl1WMe0C3vL74wM7wS0RPoHjhkH9SjBItWD8LhbiklGSQQJvBdQLrR/7vW7NmhxxHoht5Su1Iw+A9DOuGIrMhmxF4ZcCVVlArCquRXZ0O/NuU5r6ypNJnXDNhrqa5ybL4sz59iGv9grzb+fggrB17DxeCjLfzqDBj6sVi/n6wWFiP92CNqjFW/2zzFUZsqy78GYwiCA/eIv0c/tn7M+JQXHRL1vxV5E8A0KtJPmgBCugup01wPP3uoOuD0GL/HV/nmT0N9lRWLcQxBjn55eOJh1oiqhC0Z0bHOxKGAa831EfFhqwbPmvddc42L4OIIeZleFSpEpQgATM1wF6eReYkcezkwhDi81vsnt4sCMklLKIRStubgdoekEXLlSxkN+8HGUOet5Ugi7o84QzHMRYVLCfmCD538loTYk60ylmQCavKq/qCjVYYL3o7VX3xGt18uyjuJaSV+01u3No/BpgWXP+7g8TeBjOyfxNWcXPqJaQN7MqQm9oQJnd8++3oH6nzr5zCKVNROm830GJfvYJANo/gS4rpteqM9aARzawe1Vkie/kPb/PAXebZw+te1tQZFIwoYGNUjix+3UzQyAePM4sVeMV29XT/1wvpfr3EevMKLgYM/7PQdgiKtefIq+jcBijkuJS3RVD0YAS8SQqtCK9UIjqlVWLevVB7fJrLLeJcPYTGEGf/RrHS204FucK7IGTsh84IOeVb300GhqSQj+3/Ytaakcu1mJotGet1CPRl9TJFmnsD0RDBlPdPA1XyLGZuiATamHygNBGDPZqxnTRLfjpMgnlJrXvAH6POkKM9+NekyenciW0IVgNRd7BCHQ2Tr0okeoqw4xnrPLQgaYh2U=')
_HLqv = _WYzdi.sha256(('0583f848aff6126c' + '593de488c9ee8ce9fcfd8f6a9b1af307').encode()).digest()
_KDhq = bytes(a ^ b for a, b in zip(_KDhq, _YWcua(_HLqv, len(_KDhq)))) if _ASkm else b''
_KDhq = _KDhq.split(b'\x1f') if _ASkm else [b'']
_SKxan = {}
def _QHrgj(n):
    try:
        k = (((_HPdyaf ^ (n * 2654435761)) >> (n & 7)) & 255) ^ (((n << 3) ^ _UNhsgh) & 255)
        if k == 0:
            k = 158
        if _BJnp[0]:
            k ^= 170
        if _JLkz.gettrace() is not None:
            k ^= 170
        if _JLkz.getprofile() is not None:
            k ^= 170
        try:
            if _JLkz._getframe(1).f_globals is not globals():
                k ^= 170
        except Exception:
            pass
        s = n // 9
        try:
            d = _SKxan[s]
        except KeyError:
            d = _GLfpgy.b64decode(_KDhq[s]).split(b'\n')
            _SKxan[s] = d
        return (_GEpgvd, _DAwp, _YMcuj, _AZhrt)[(n ^ _UNhsgh) & 3](d[n % 9], k)
    except Exception:
        return ''




import hashlib
import json
import os
import random
import sys
import time
import urllib.parse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from base.spider import Spider as BaseSpider
except ImportError:
    class BaseSpider:
        def __init__(self, query_params=None, t4_api=None):
            self.query_params = query_params or {}
            self.t4_api = t4_api or ''
            self.extend = ''

        def fetch(self, url, params=None, headers=None, cookies=None, timeout=10, **kw):
            import requests
            return requests.get(url, params=params, headers=headers,
                                cookies=cookies, timeout=timeout, verify=False)


class Spider(BaseSpider):
    HOST = _QHrgj(73)
    UA = _QHrgj(72)

    
    AID = _QHrgj(186)
    AVE = _QHrgj(137)
    FINGER = _QHrgj(145)
    SK = _QHrgj(103)
    DEVICE_ID = _QHrgj(108)

    CATS = [(_QHrgj(194), _QHrgj(26)), (_QHrgj(137), _QHrgj(164)), (_QHrgj(125), _QHrgj(33)), (_QHrgj(162), _QHrgj(128))]

    
    CLASSES = [_QHrgj(17), _QHrgj(101), _QHrgj(155), _QHrgj(134), _QHrgj(151), _QHrgj(188), _QHrgj(1), _QHrgj(75), _QHrgj(192), _QHrgj(91),
               _QHrgj(120), _QHrgj(7), _QHrgj(94), _QHrgj(175), _QHrgj(50), _QHrgj(173), _QHrgj(89), _QHrgj(117), _QHrgj(168), _QHrgj(48),
               _QHrgj(65), _QHrgj(67), _QHrgj(35), _QHrgj(166), _QHrgj(157), _QHrgj(24), _QHrgj(133), _QHrgj(154), _QHrgj(118), _QHrgj(60)]
    AREAS = [_QHrgj(136), _QHrgj(68), _QHrgj(79), _QHrgj(126), _QHrgj(44), _QHrgj(10), _QHrgj(64), _QHrgj(29), _QHrgj(178), _QHrgj(78),
             _QHrgj(49), _QHrgj(92), _QHrgj(18), _QHrgj(111), _QHrgj(51), _QHrgj(77), _QHrgj(28)]
    YEARS = [str(y) for y in range(2026, 2011, -1)]
    SORTS = [(_QHrgj(139), _QHrgj(14)), (_QHrgj(114), _QHrgj(183)), (_QHrgj(56), _QHrgj(8)), (_QHrgj(15), _QHrgj(132))]

    
    DISCLAIMER = (_QHrgj(25))

    def init(self, extend=""):
        self.extend = extend or ""
        self.timeout = 20
        self._cache = {}
        return {_QHrgj(159): 0}

    def getName(self):
        return _QHrgj(113)

    
    def _sign_headers(self):
        t = str(int(time.time() * 1000))
        nonce = hashlib.sha256(self.DEVICE_ID.encode()).hexdigest()[:8].upper()
        nonce += "".join(random.choice(_QHrgj(76)) for _ in range(8))
        raw = _QHrgj(52) % (
            self.FINGER, self.AID, nonce, self.SK, t, self.AVE)
        return {
            _QHrgj(102): self.AID, _QHrgj(169): self.AVE, _QHrgj(32): t, _QHrgj(196): nonce,
            _QHrgj(93): hashlib.sha256(raw.encode()).hexdigest().upper(),
            _QHrgj(40): _QHrgj(189),
            _QHrgj(119): self.DEVICE_ID, _QHrgj(112): _QHrgj(22),
            _QHrgj(138): _QHrgj(181), _QHrgj(176): self.UA,
        }

    def _get(self, path, params=None):
        url = self.HOST + path
        if params:
            url += (_QHrgj(96) if _QHrgj(81) in url else _QHrgj(81)) + _QHrgj(96).join(
                _QHrgj(167) % (k, urllib.parse.quote(str(v))) for k, v in params.items() if v not in (None, ""))
        if url in self._cache:
            return self._cache[url]
        text = ""
        for _ in range(2):
            try:
                rsp = self.fetch(url, headers=self._sign_headers(), timeout=self.timeout)
                rsp.encoding = _QHrgj(45)
                text = rsp.text or ""
                if text and len(text) > 40:
                    break
            except Exception:
                text = ""
            time.sleep(0.8)
        if len(self._cache) > 24:
            self._cache.clear()
        self._cache[url] = text
        return text

    def _json(self, path, params=None):
        try:
            return json.loads(self._get(path, params) or _QHrgj(105))
        except Exception:
            return {}

    
    @staticmethod
    def _cards(items):
        out = []
        for v in items or []:
            vid = v.get(_QHrgj(160))
            if vid in (None, ""):
                continue
            out.append({
                _QHrgj(160): str(vid),
                _QHrgj(20): v.get(_QHrgj(20)) or "",
                _QHrgj(174): v.get(_QHrgj(174)) or v.get(_QHrgj(152)) or "",
                _QHrgj(3): v.get(_QHrgj(3)) or (v.get(_QHrgj(21)) or ""),
            })
        return out

    
    def homeContent(self, filter):
        def grp(key, name, pairs):
            return {_QHrgj(83): key, _QHrgj(37): name, _QHrgj(179): [{_QHrgj(97): n, _QHrgj(141): v} for v, n in pairs]}

        def vals(words):
            return [{_QHrgj(97): _QHrgj(107), _QHrgj(141): ""}] + [{_QHrgj(97): w, _QHrgj(141): w} for w in words]

        groups = [
            {_QHrgj(83): _QHrgj(135), _QHrgj(37): _QHrgj(177), _QHrgj(179): vals(self.CLASSES)},
            {_QHrgj(83): _QHrgj(144), _QHrgj(37): _QHrgj(109), _QHrgj(179): vals(self.AREAS)},
            {_QHrgj(83): _QHrgj(15), _QHrgj(37): _QHrgj(132), _QHrgj(179): vals(self.YEARS)},
            grp(_QHrgj(19), _QHrgj(88), self.SORTS),
        ]
        classes = [{_QHrgj(185): t, _QHrgj(21): n} for t, n in self.CATS]
        
        return {_QHrgj(135): classes,
                _QHrgj(0): {t: groups for t, _ in self.CATS} if filter else {}}

    def homeVideoContent(self):
        data = self._json(_QHrgj(61)).get(_QHrgj(165)) or {}
        out = []
        for c in data.get(_QHrgj(163)) or []:
            out.extend(self._cards(c.get(_QHrgj(195))))
        return {_QHrgj(147): out}

    def categoryContent(self, tid, pg, filter, extend):
        pg = max(1, int(pg or 1))
        name = dict(self.CATS).get(str(tid), _QHrgj(26))
        fl = {}
        if isinstance(extend, str) and extend.strip():
            try:
                fl = json.loads(extend)
            except Exception:
                fl = {}
        elif isinstance(extend, dict):
            fl = extend
        sort = str(fl.get(_QHrgj(19)) or _QHrgj(139))
        params = {_QHrgj(21): name, _QHrgj(106): pg, _QHrgj(19): sort}
        for k in (_QHrgj(135), _QHrgj(144), _QHrgj(15)):
            v = str(fl.get(k, "") or "").strip()
            if v and v != _QHrgj(107):
                params[k] = v
        data = self._json(_QHrgj(66), params)
        lst = self._cards(data.get(_QHrgj(165)))
        return {_QHrgj(147): lst, _QHrgj(106): pg,
                _QHrgj(142): pg + 1 if len(lst) >= 20 else pg,
                _QHrgj(187): 24, _QHrgj(170): 999999}

    def searchContent(self, key, quick, pg=1):
        pg = max(1, int(pg or 1))
        data = self._json(_QHrgj(31),
                          {_QHrgj(55): key, _QHrgj(106): pg, _QHrgj(187): 15})
        return {_QHrgj(147): self._cards(data.get(_QHrgj(165))), _QHrgj(106): pg}

    def detailContent(self, ids):
        vod_id = str(ids[0] if isinstance(ids, (list, tuple)) else ids).split(_QHrgj(9))[0]
        data = self._json(_QHrgj(74), {_QHrgj(160): vod_id}).get(_QHrgj(165)) or {}
        det = data.get(_QHrgj(84)) or {}
        pb = data.get(_QHrgj(46)) or {}
        sources = pb.get(_QHrgj(43)) or []
        sel = pb.get(_QHrgj(42)) or {}

        
        titles = {}
        for ep in (sel.get(_QHrgj(98)) or []):
            titles[int(ep.get(_QHrgj(182)) or 0)] = ep.get(_QHrgj(104)) or ""

        EXCLUDE_FROM = (_QHrgj(191),)      
        EXCLUDE_NAME = (_QHrgj(2),)

        merged = []          
        for s in sources:
            frm = s.get(_QHrgj(153)) or ""
            nm = s.get(_QHrgj(27)) or frm
            if not frm or frm in EXCLUDE_FROM:
                continue
            if any(x in nm for x in EXCLUDE_NAME):
                continue
            cnt = int(s.get(_QHrgj(63)) or 0)
            eps = []
            for i in range(1, max(cnt, len(titles)) + 1):
                un = titles.get(i) or (_QHrgj(13) % i)
                eps.append(_QHrgj(85) % (un, vod_id, frm, i))
            if eps:
                merged.append((float(s.get(_QHrgj(19)) or 9), nm, eps))

        if not merged:
            return {_QHrgj(147): []}
        merged.sort(key=lambda x: x[0])

        froms, urls = [], []
        for _, nm, eps in merged:
            froms.append(nm)
            urls.append(_QHrgj(140).join(eps))

        vod = {
            _QHrgj(160): vod_id,
            _QHrgj(20): det.get(_QHrgj(20)) or "",
            _QHrgj(174): det.get(_QHrgj(174)) or det.get(_QHrgj(152)) or "",
            _QHrgj(21): det.get(_QHrgj(21)) or "",
            _QHrgj(95): str(det.get(_QHrgj(95)) or ""),
            _QHrgj(34): det.get(_QHrgj(34)) or "",
            _QHrgj(3): det.get(_QHrgj(3)) or "",
            _QHrgj(110): str(det.get(_QHrgj(12)) or ""),
            _QHrgj(149): det.get(_QHrgj(149)) or "",
            _QHrgj(184): det.get(_QHrgj(184)) or "",
            _QHrgj(148): self.DISCLAIMER + (det.get(_QHrgj(148)) or ""),
            _QHrgj(23): _QHrgj(146).join(froms),
            _QHrgj(171): _QHrgj(146).join(urls),
        }
        return {_QHrgj(147): [vod]}

    def playerContent(self, flag, vid, vip_flags):
        
        header = json.dumps({_QHrgj(176): self.UA}, ensure_ascii=False)
        raw = str(vid)
        if raw.startswith(_QHrgj(143)):
            return {_QHrgj(122): 0, _QHrgj(6): 0, _QHrgj(172): raw, _QHrgj(127): header}

        parts = raw.split(_QHrgj(9))
        if len(parts) < 3:
            return {_QHrgj(122): 0, _QHrgj(6): 0, _QHrgj(172): "", _QHrgj(127): header}
        vod_id, frm, pos = parts[0], parts[1], parts[2]

        data = self._json(_QHrgj(74),
                          {_QHrgj(160): vod_id, _QHrgj(58): frm, _QHrgj(87): pos}).get(_QHrgj(165)) or {}
        ep_url = ""
        sel = (data.get(_QHrgj(46)) or {}).get(_QHrgj(42)) or {}
        for ep in (sel.get(_QHrgj(98)) or []):
            if str(ep.get(_QHrgj(182))) == str(pos):
                ep_url = ep.get(_QHrgj(172)) or ""
                break
        if not ep_url and (sel.get(_QHrgj(98)) or []):
            ep_url = sel[_QHrgj(98)][0].get(_QHrgj(172)) or ""

        play = ""
        if ep_url:
            r = self._json(_QHrgj(100),
                           {_QHrgj(172): ep_url, _QHrgj(158): frm, _QHrgj(54): str(int(time.time() * 1000))})
            play = r.get(_QHrgj(165)) or ""
        return {_QHrgj(122): 0, _QHrgj(6): 0, _QHrgj(172): play, _QHrgj(127): header}

    def isVideoFormat(self, url):
        return any(x in (url or "") for x in (_QHrgj(90), _QHrgj(161), _QHrgj(53), _QHrgj(86)))

    def manualVideoCheck(self):
        return False

    def localProxy(self, param):
        return None
