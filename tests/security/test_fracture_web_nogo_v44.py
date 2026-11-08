"""Tests adversariaux du garde V44 : une activation Web doit faire échouer CI."""
import unittest

from scripts.validate_fracture_web_nogo_v44 import (
    PLAY, LANDING, validate_public_fracture,
)


class FractureWebNogoV44(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.play = PLAY.read_text(encoding="utf-8")
        cls.landing = LANDING.read_text(encoding="utf-8")

    def assert_blocked(self, changed_play=None, changed_landing=None):
        errors = validate_public_fracture(
            self.play if changed_play is None else changed_play,
            self.landing if changed_landing is None else changed_landing,
        )
        self.assertTrue(errors, "La modification dangereuse devrait être refusée.")

    def test_page_officielle_reste_en_nogo(self):
        self.assertEqual(validate_public_fracture(self.play, self.landing), [])

    def test_suppression_du_titre_est_bloquee(self):
        self.assert_blocked(self.play.replace("Mode Web en mise à niveau", "Jouer en ligne", 1))

    def test_suppression_de_l_avertissement_est_bloquee(self):
        self.assert_blocked(self.play.replace("temporairement suspendues", "ouvertes", 1))

    def test_suppression_des_regles_solo_duo_est_bloquee(self):
        self.assert_blocked(self.play.replace("contrôle humain", "contrôle ordinateur", 1))

    def test_formulaire_de_rejoindre_partie_est_bloque(self):
        self.assert_blocked(self.play.replace("</main>", "<form action='/start'><input name='code'></form></main>", 1))

    def test_script_legacy_est_bloque(self):
        self.assert_blocked(self.play.replace("</body>", "<script src='/assets/js/sinjira-fracture-online.js'></script></body>", 1))

    def test_script_en_ligne_est_bloque(self):
        self.assert_blocked(self.play.replace("</main>", "<script>fetch('/game/start')</script></main>", 1))

    def test_handler_js_inline_est_bloque(self):
        self.assert_blocked(self.play.replace("<main", '<main onload="activateGame()"', 1))

    def test_javascript_url_est_bloquee(self):
        self.assert_blocked(self.play.replace('href="regles.html"', 'href="javascript:alert(1)"', 1))

    def test_action_de_lobby_est_bloquee(self):
        self.assert_blocked(self.play.replace("<main", '<main data-fracture-start="1"', 1))

    def test_injection_rpc_est_bloquee(self):
        self.assert_blocked(self.play.replace("</main>", '<p>fracture_engine_start</p></main>', 1))

    def test_redirection_automatique_est_bloquee(self):
        self.assert_blocked(self.play.replace("</head>", '<meta http-equiv="refresh" content="0;url=game.html"></head>', 1))

    def test_alternatives_physiques_doivent_rester_disponibles(self):
        self.assert_blocked(self.play.replace('href="feuille-de-score.html"', 'href="ailleurs.html"'))

    def test_lien_d_etat_jouer_requis_dans_presentation(self):
        self.assert_blocked(changed_landing=self.landing.replace('href="jouer.html"', 'href="lobby.html"'))

    def test_chargement_ancien_moteur_via_presentation_est_bloque(self):
        self.assert_blocked(changed_landing=self.landing.replace("</body>", "<script src='/assets/js/sinjira-fracture-online.js'></script></body>", 1))

    def test_mise_a_jour_de_versions_de_scripts_innocente(self):
        edited = self.play.replace("site.js?v=24.4.23", "site.js?v=24.4.24", 1)
        self.assertEqual(validate_public_fracture(edited, self.landing), [])


if __name__ == "__main__":
    unittest.main()
