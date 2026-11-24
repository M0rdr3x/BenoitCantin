#!/usr/bin/env python3
"""Contrats de version du script MFA SINJIRA (aucun accès aux comptes)."""
import unittest

from validate_session_security_v24_4_68 import validate_security_script_version


def page(version: str) -> str:
    return (
        '<!doctype html><html><body>'
        f'<script src="../assets/js/v24-security.js?v={version}" type="module"></script>'
        '</body></html>'
    )


class SessionSecurityVersionTest(unittest.TestCase):
    def test_minimum_historique_accepte(self):
        validate_security_script_version(page('24.4.69'))

    def test_versions_plus_recentes_acceptees(self):
        validate_security_script_version(page('24.4.70'))
        validate_security_script_version(page('24.5.0'))

    def test_version_ancienne_refusee(self):
        with self.assertRaises(AssertionError):
            validate_security_script_version(page('24.4.68'))

    def test_absence_de_version_refusee(self):
        with self.assertRaises(AssertionError):
            validate_security_script_version(page(''))

    def test_script_duplique_refuse(self):
        with self.assertRaises(AssertionError):
            validate_security_script_version(page('24.4.70') + page('24.4.71'))

    def test_simple_texte_ne_remplace_pas_la_balise(self):
        with self.assertRaises(AssertionError):
            validate_security_script_version('v24-security.js?v=24.4.70')


if __name__ == '__main__':
    unittest.main()
