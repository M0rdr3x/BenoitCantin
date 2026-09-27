#!/usr/bin/env python3
from __future__ import annotations

import unittest

import validate_production_review_decision_trace as guard


class ProductionReviewDecisionTraceTests(unittest.TestCase):
    def test_static_empty_trace_is_allowed_for_historical_batch(self):
        errors = []
        batch = [guard.LEGACY_REVIEWED_ROWS[0]]
        guard.validate_static(errors, batch, [], '20260906035442')
        self.assertEqual(errors, [])

    def test_new_reviewed_row_with_same_diff_trace_is_accepted(self):
        errors = []
        base_batch = [('20260907145100', 'legacy_reviewed', 'a' * 40)]
        current_batch = base_batch + [('20260913030500', 'new_reviewed', 'b' * 40)]
        base_trace = []
        current_trace = [('20260913030500', 'new_reviewed', 'b' * 40, 438, 'APPROVED')]
        guard.validate_transition(errors, base_batch, current_batch, base_trace, current_trace, '20260906035442')
        self.assertEqual(errors, [])

    def test_new_reviewed_row_without_new_trace_is_rejected(self):
        errors = []
        base_batch = [('20260907145100', 'legacy_reviewed', 'a' * 40)]
        current_batch = base_batch + [('20260913030500', 'new_reviewed', 'b' * 40)]
        guard.validate_transition(errors, base_batch, current_batch, [], [], '20260906035442')
        self.assertTrue(any('sans trace de décision' in error for error in errors), errors)

    def test_precreated_trace_without_batch_addition_is_rejected(self):
        errors = []
        base_batch = [('20260907145100', 'legacy_reviewed', 'a' * 40)]
        trace = [('20260913030500', 'future_precreated', 'b' * 40, 438, 'APPROVED')]
        guard.validate_transition(errors, base_batch, list(base_batch), [], trace, '20260906035442')
        self.assertTrue(any('pré-créée' in error for error in errors), errors)

    def test_trace_history_is_append_only(self):
        errors = []
        batch = [('20260907145100', 'legacy_reviewed', 'a' * 40)]
        base_trace = [('20260907145100', 'legacy_reviewed', 'a' * 40, 100, 'APPROVED')]
        current_trace = [('20260907145100', 'legacy_reviewed', 'a' * 40, 101, 'APPROVED')]
        guard.validate_transition(errors, batch, batch, base_trace, current_trace, '20260906035442')
        self.assertTrue(any('non append-only' in error for error in errors), errors)

    def test_changed_blob_requires_new_exact_trace(self):
        errors = []
        base_batch = [('20260913030500', 'reviewed', 'a' * 40)]
        current_batch = [('20260913030500', 'reviewed', 'b' * 40)]
        base_trace = [('20260913030500', 'reviewed', 'a' * 40, 438, 'APPROVED')]
        current_trace = list(base_trace)
        guard.validate_transition(errors, base_batch, current_batch, base_trace, current_trace, '20260906035442')
        self.assertTrue(any('sans trace de décision' in error for error in errors), errors)

    def test_changed_blob_with_new_exact_trace_is_accepted(self):
        errors = []
        base_batch = [('20260913030500', 'reviewed', 'a' * 40)]
        current_batch = [('20260913030500', 'reviewed', 'b' * 40)]
        base_trace = [('20260913030500', 'reviewed', 'a' * 40, 438, 'APPROVED')]
        current_trace = base_trace + [('20260913030500', 'reviewed', 'b' * 40, 438, 'APPROVED')]
        guard.validate_transition(errors, base_batch, current_batch, base_trace, current_trace, '20260906035442')
        self.assertEqual(errors, [])

    def test_duplicate_trace_for_same_blob_is_rejected(self):
        errors = []
        batch = [('20260913030500', 'reviewed', 'a' * 40)]
        trace = [
            ('20260913030500', 'reviewed', 'a' * 40, 438, 'APPROVED'),
            ('20260913030500', 'reviewed', 'a' * 40, 439, 'APPROVED'),
        ]
        guard.validate_static(errors, batch, trace, '20260906035442')
        self.assertTrue(any('plusieurs fois' in error for error in errors), errors)

    def test_static_new_reviewed_row_without_trace_is_rejected(self):
        errors = []
        batch = [guard.LEGACY_REVIEWED_ROWS[0], ('20260913030500', 'new_reviewed', 'b' * 40)]
        guard.validate_static(errors, batch, [], '20260906035442')
        self.assertTrue(any('hors baseline historique sans trace' in error for error in errors), errors)

    def test_static_new_reviewed_row_with_trace_is_accepted(self):
        errors = []
        row = ('20260913030500', 'new_reviewed', 'b' * 40)
        batch = [guard.LEGACY_REVIEWED_ROWS[0], row]
        trace = [(row[0], row[1], row[2], 438, 'APPROVED')]
        guard.validate_static(errors, batch, trace, '20260906035442')
        self.assertEqual(errors, [])

    def test_future_trace_without_active_batch_row_is_rejected(self):
        errors = []
        batch = [guard.LEGACY_REVIEWED_ROWS[0]]
        trace = [('20260913030500', 'future_precreated', 'b' * 40, 438, 'APPROVED')]
        guard.validate_static(errors, batch, trace, '20260906035442')
        self.assertTrue(any('sans ligne active' in error for error in errors), errors)

    def test_historical_trace_may_remain_after_ledger_advances(self):
        errors = []
        batch = [guard.LEGACY_REVIEWED_ROWS[0]]
        trace = [('20260905000000', 'already_applied', 'b' * 40, 400, 'APPROVED')]
        guard.validate_static(errors, batch, trace, '20260906035442')
        self.assertEqual(errors, [])

    def test_trace_parser_requires_issue_and_approved(self):
        with self.assertRaises(ValueError):
            guard.parse_trace_text(
                '20260913030500 new_reviewed ' + ('b' * 40) + ' issue#438 PENDING\n',
                'test',
            )


if __name__ == '__main__':
    unittest.main(verbosity=2)
