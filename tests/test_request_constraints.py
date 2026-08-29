from __future__ import annotations

import json
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from mqt.bench.targets import get_device

from qiskit_dataset.catalog import load_catalog
from qiskit_dataset.generation import build_target_record

from prototype.quantum_assistant.adapters.hardware import (
    HardwareCatalogIntegrityError,
    HardwareMaskBuilder,
    MqtHardwareCatalog,
)
from prototype.quantum_assistant.adapters.llm import CallableLlmGateway
from prototype.quantum_assistant.adapters.request import (
    FEATURE_NAMES,
    QasmRequestParser,
    RequestSemanticValidator,
)
from prototype.quantum_assistant.controller import PrototypeController
from prototype.quantum_assistant.errors import RequestValidationError
from prototype.quantum_assistant.factory import build_default_service
from prototype.quantum_assistant.models import (
    CircuitInput,
    DeviceExclusionReason,
    UiSubmission,
    UserRequest,
)
from prototype.quantum_assistant.schema_validation import (
    ensure_supported_schema,
    load_schema,
    validate_instance,
)
from prototype.quantum_assistant.services import NoEligibleDeviceError


DEVICE_IDS = (
    "ibm_falcon_27",
    "ibm_falcon_127",
    "ibm_heron_133",
    "ibm_heron_156",
    "quantinuum_h2_56",
)
REQUEST_ID = "11111111-1111-4111-8111-111111111111"
TWO_QUBIT_QASM = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
cx q[0],q[1];
"""


def request_payload(
    catalog_snapshot_id: str,
    constraints: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "request_id": REQUEST_ID,
        "catalog_snapshot_id": catalog_snapshot_id,
        "circuit": {
            "format": "openqasm2",
            "name": "bell",
            "source": TWO_QUBIT_QASM,
        },
        "figure_of_merit_id": "expected_fidelity",
        "hardware_constraints": constraints or {},
    }


class PhaseTwoRequestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog_adapter = MqtHardwareCatalog(DEVICE_IDS)
        cls.catalog = cls.catalog_adapter.snapshot()
        cls.parser = QasmRequestParser()
        cls.semantic_validator = RequestSemanticValidator()
        cls.mask_builder = HardwareMaskBuilder()

    def issue_codes(self, error: RequestValidationError) -> set[str]:
        return {issue.code for issue in error.report.issues}

    def normalize(
        self,
        constraints: dict[str, object] | None = None,
        *,
        snapshot_id: str | None = None,
    ):
        parsed = self.parser.parse(
            request_payload(
                snapshot_id or self.catalog.catalog_snapshot_id,
                constraints,
            )
        )
        return self.semantic_validator.normalize(parsed, self.catalog)

    def test_catalog_is_normalized_stable_and_ui_ready(self) -> None:
        self.assertIs(self.catalog_adapter.snapshot(), self.catalog)
        self.assertEqual(self.catalog.provider_ids, ("ibm", "quantinuum"))
        self.assertEqual(
            tuple(device.device_id for device in self.catalog.devices),
            tuple(sorted(DEVICE_IDS)),
        )
        self.assertEqual(len(self.catalog.qiskit_configuration_ids), 12)
        self.assertEqual(
            self.catalog.supported_figure_of_merit_ids,
            ("expected_fidelity",),
        )
        self.assertTrue(all(device.target_available for device in self.catalog.devices))
        self.assertTrue(all(device.target_hash for device in self.catalog.devices))

        profiles = self.catalog.device_by_id
        self.assertEqual(profiles["ibm_falcon_27"].provider_id, "ibm")
        self.assertEqual(
            profiles["ibm_falcon_27"].native_gate_ids,
            ("cx", "id", "rz", "sx", "x"),
        )
        self.assertEqual(
            profiles["ibm_heron_133"].native_gate_ids,
            ("cz", "id", "rz", "sx", "x"),
        )
        quantinuum = profiles["quantinuum_h2_56"]
        self.assertEqual(quantinuum.provider_id, "quantinuum")
        self.assertEqual(quantinuum.native_gate_ids, ("rx", "ry", "rz", "rzz"))
        self.assertEqual(quantinuum.coupling_type, "explicit_complete")
        self.assertEqual(len(quantinuum.coupling_edges), 56 * 55)

        schema = load_schema("hardware_catalog.schema.json")
        self.assertEqual(validate_instance(schema, self.catalog.to_dict()), ())

    def test_catalog_fingerprint_is_dataset_linkable_and_cross_instance_stable(
        self,
    ) -> None:
        rebuilt = MqtHardwareCatalog(tuple(reversed(DEVICE_IDS))).snapshot()
        self.assertEqual(rebuilt.to_dict(), self.catalog.to_dict())
        self.assertEqual(
            self.catalog.provenance["fingerprint_algorithm"],
            "assistant-hardware-catalog/2",
        )

        for profile in self.catalog.devices:
            with self.subTest(device_id=profile.device_id):
                historical = build_target_record(profile.device_id)
                self.assertEqual(
                    profile.target_hash,
                    historical["target_sha256"],
                )
                self.assertEqual(
                    profile.metadata["target_fingerprint_algorithm"],
                    "qiskit-dataset-target/1",
                )
                self.assertRegex(
                    profile.metadata["instruction_properties_hash"],
                    r"^[0-9a-f]{64}$",
                )

    def test_catalog_is_deeply_immutable_but_serializes_to_mutable_json(
        self,
    ) -> None:
        with self.assertRaises(TypeError):
            self.catalog.provenance["unexpected"] = True
        with self.assertRaises(TypeError):
            self.catalog.provenance["package_versions"]["qiskit"] = "mutated"
        with self.assertRaises(TypeError):
            self.catalog.devices[0].metadata["target_source"] = "mutated"

        serialized = self.catalog.to_dict()
        serialized["provenance"]["package_versions"]["qiskit"] = "mutated"
        self.assertNotEqual(
            self.catalog.provenance["package_versions"]["qiskit"],
            "mutated",
        )

    def test_catalog_validates_injected_configuration_catalog(self) -> None:
        baseline = load_catalog()
        with self.assertRaisesRegex(ValueError, "expected_fidelity"):
            MqtHardwareCatalog(
                ("ibm_falcon_27",),
                configuration_catalog=replace(
                    baseline,
                    objective={"name": "unsupported_metric"},
                ),
            )
        with self.assertRaisesRegex(ValueError, "config_id duplicati"):
            MqtHardwareCatalog(
                ("ibm_falcon_27",),
                configuration_catalog=replace(
                    baseline,
                    configurations=(
                        baseline.configurations[0],
                        baseline.configurations[0],
                    ),
                ),
            )

    def test_target_loading_failure_is_stable_and_masked_without_error_text(
        self,
    ) -> None:
        adapter = MqtHardwareCatalog(("ibm_falcon_27",))
        with patch(
            "prototype.quantum_assistant.adapters.hardware.get_device",
            side_effect=RuntimeError("/private/path/that/must/not/leak"),
        ):
            snapshot = adapter.snapshot()

        profile = snapshot.devices[0]
        self.assertFalse(profile.target_available)
        self.assertEqual(
            profile.metadata["unavailability_code"],
            "TARGET_LOAD_FAILED",
        )
        self.assertEqual(profile.metadata["load_error_type"], "RuntimeError")
        self.assertNotIn("private", json.dumps(snapshot.to_dict()))

        parsed = self.parser.parse(
            request_payload(snapshot.catalog_snapshot_id)
        )
        normalized = self.semantic_validator.normalize(parsed, snapshot)
        result = self.mask_builder.filter(normalized, snapshot)
        diagnostic = result.excluded_devices[0]
        self.assertIn(
            DeviceExclusionReason.TARGET_NOT_AVAILABLE,
            diagnostic.reason_codes,
        )
        self.assertEqual(
            diagnostic.details["target_unavailability_code"],
            "TARGET_LOAD_FAILED",
        )
        self.assertEqual(
            diagnostic.details["target_load_error_type"],
            "RuntimeError",
        )

    def test_catalog_integrity_mismatch_fails_instead_of_masking_device(
        self,
    ) -> None:
        target = get_device("ibm_falcon_27")
        target.description = "wrong_device"
        adapter = MqtHardwareCatalog(("ibm_falcon_27",))
        with patch(
            "prototype.quantum_assistant.adapters.hardware.get_device",
            return_value=target,
        ):
            with self.assertRaises(HardwareCatalogIntegrityError):
                adapter.snapshot()

    def test_schema_validator_fails_closed_on_unknown_keyword(self) -> None:
        with self.assertRaisesRegex(ValueError, "allOf"):
            ensure_supported_schema(
                {
                    "$schema": (
                        "https://json-schema.org/draft/2020-12/schema"
                    ),
                    "type": "object",
                    "allOf": [],
                }
            )

    def test_catalog_rejects_devices_without_an_explicit_definition(self) -> None:
        with self.assertRaisesRegex(ValueError, "definizione hardware"):
            MqtHardwareCatalog(("not_a_device",))

    def test_valid_json_request_is_parsed_and_tied_to_snapshot(self) -> None:
        document = json.dumps(
            request_payload(
                self.catalog.catalog_snapshot_id,
                {
                    "allowed_provider_ids": ["ibm"],
                    "allowed_device_ids": ["ibm_falcon_27"],
                    "device_qubits": {"min": 2, "max": 127},
                    "required_native_gate_ids": ["cnot"],
                },
            )
        )
        normalized = self.semantic_validator.normalize(
            self.parser.parse(document),
            self.catalog,
        )

        self.assertEqual(normalized.num_qubits, 2)
        self.assertEqual(normalized.catalog_snapshot_id, self.catalog.catalog_snapshot_id)
        self.assertEqual(
            normalized.hardware_constraints.required_native_gate_ids,
            ("cx",),
        )
        self.assertEqual(normalized.user_text, "")

    def test_request_schema_is_closed_and_rejects_bad_types(self) -> None:
        unknown_field = request_payload(self.catalog.catalog_snapshot_id)
        unknown_field["free_text"] = "scegli IBM"
        with self.assertRaises(RequestValidationError) as captured:
            self.parser.parse(unknown_field)
        self.assertIn("REQUEST_SCHEMA_INVALID", self.issue_codes(captured.exception))

        removed_constraint = request_payload(
            self.catalog.catalog_snapshot_id,
            {"excluded_device_ids": ["ibm_falcon_27"]},
        )
        with self.assertRaises(RequestValidationError) as captured:
            self.parser.parse(removed_constraint)
        self.assertIn(
            "REQUEST_SCHEMA_INVALID",
            self.issue_codes(captured.exception),
        )

        empty_selection = request_payload(
            self.catalog.catalog_snapshot_id,
            {"allowed_provider_ids": []},
        )
        with self.assertRaises(RequestValidationError) as captured:
            self.parser.parse(empty_selection)
        self.assertIn(
            "REQUEST_SCHEMA_INVALID",
            self.issue_codes(captured.exception),
        )

        uppercase_uuid = request_payload(self.catalog.catalog_snapshot_id)
        uppercase_uuid["request_id"] = "AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA"
        with self.assertRaises(RequestValidationError) as captured:
            self.parser.parse(uppercase_uuid)
        self.assertIn(
            "REQUEST_SCHEMA_INVALID",
            self.issue_codes(captured.exception),
        )

        wrong_type = request_payload(
            self.catalog.catalog_snapshot_id,
            {"allowed_provider_ids": "ibm"},
        )
        with self.assertRaises(RequestValidationError) as captured:
            self.parser.parse(wrong_type)
        self.assertIn("REQUEST_SCHEMA_INVALID", self.issue_codes(captured.exception))

    def test_json_decoder_rejects_duplicate_keys_and_invalid_qasm(self) -> None:
        with self.assertRaises(RequestValidationError) as captured:
            self.parser.parse('{"schema_version":"1.0.0","schema_version":"1.0.0"}')
        self.assertIn("REQUEST_JSON_INVALID", self.issue_codes(captured.exception))

        forbidden_include = request_payload(self.catalog.catalog_snapshot_id)
        forbidden_include["circuit"] = {
            "format": "openqasm2",
            "source": (
                'OPENQASM 2.0; include "README.md"; '
                "qreg q[1]; x q[0];"
            ),
        }
        with self.assertRaises(RequestValidationError) as captured:
            self.parser.parse(forbidden_include)
        self.assertIn(
            "QASM_INCLUDE_NOT_ALLOWED",
            self.issue_codes(captured.exception),
        )

        bad_qasm = request_payload(self.catalog.catalog_snapshot_id)
        bad_qasm["circuit"] = {
            "format": "openqasm2",
            "source": "not openqasm",
        }
        with self.assertRaises(RequestValidationError) as captured:
            self.parser.parse(bad_qasm)
        self.assertIn("QASM_PARSE_FAILED", self.issue_codes(captured.exception))

    def test_parser_rejects_invalid_utf8_nonfinite_json_and_zero_qubits(
        self,
    ) -> None:
        with self.assertRaises(RequestValidationError) as captured:
            self.parser.parse(b"\xff")
        self.assertIn(
            "REQUEST_JSON_INVALID",
            self.issue_codes(captured.exception),
        )

        with self.assertRaises(RequestValidationError) as captured:
            self.parser.parse('{"schema_version": NaN}')
        self.assertIn(
            "REQUEST_JSON_INVALID",
            self.issue_codes(captured.exception),
        )

        zero_qubit = request_payload(self.catalog.catalog_snapshot_id)
        zero_qubit["circuit"] = {
            "format": "openqasm2",
            "source": 'OPENQASM 2.0; include "qelib1.inc";',
        }
        with self.assertRaises(RequestValidationError) as captured:
            self.parser.parse(zero_qubit)
        self.assertIn(
            "CIRCUIT_HAS_NO_QUBITS",
            self.issue_codes(captured.exception),
        )

        oversized_utf8 = request_payload(self.catalog.catalog_snapshot_id)
        oversized_utf8["circuit"] = {
            "format": "openqasm2",
            "source": "OPENQASM 2.0; //" + "😀" * 525_001,
        }
        with self.assertRaises(RequestValidationError) as captured:
            self.parser.parse(oversized_utf8)
        self.assertIn(
            "REQUEST_SCHEMA_INVALID",
            self.issue_codes(captured.exception),
        )

    def test_parser_rejects_failed_or_nonfinite_feature_extraction(
        self,
    ) -> None:
        payload = request_payload(self.catalog.catalog_snapshot_id)
        with patch(
            "prototype.quantum_assistant.adapters.request.create_feature_vector",
            side_effect=RuntimeError("feature failure"),
        ):
            with self.assertRaises(RequestValidationError) as captured:
                self.parser.parse(payload)
        self.assertIn(
            "CIRCUIT_FEATURE_EXTRACTION_FAILED",
            self.issue_codes(captured.exception),
        )

        with patch(
            "prototype.quantum_assistant.adapters.request.create_feature_vector",
            return_value=[float("nan")] * len(FEATURE_NAMES),
        ):
            with self.assertRaises(RequestValidationError) as captured:
                self.parser.parse(payload)
        self.assertIn(
            "CIRCUIT_FEATURES_INVALID",
            self.issue_codes(captured.exception),
        )

    def test_semantic_validation_reports_all_catalog_errors(self) -> None:
        payload = request_payload(
            self.catalog.catalog_snapshot_id,
            {
                "allowed_provider_ids": ["missing_provider"],
                "allowed_device_ids": ["missing_device"],
                "required_native_gate_ids": ["missing_gate"],
            },
        )
        parsed = self.parser.parse(payload)
        with self.assertRaises(RequestValidationError) as captured:
            self.semantic_validator.normalize(parsed, self.catalog)

        codes = self.issue_codes(captured.exception)
        self.assertIn("UNKNOWN_PROVIDER", codes)
        self.assertIn("UNKNOWN_DEVICE", codes)
        self.assertIn("UNKNOWN_GATE", codes)

    def test_semantic_validation_rejects_ranges_snapshot_and_provider_conflicts(self) -> None:
        cases = (
            (
                {"device_qubits": {"min": 100, "max": 27}},
                "INVALID_QUBIT_RANGE",
                self.catalog.catalog_snapshot_id,
            ),
            (
                {"device_qubits": {"max": 1}},
                "CIRCUIT_EXCEEDS_USER_MAX_QUBITS",
                self.catalog.catalog_snapshot_id,
            ),
            (
                {
                    "allowed_provider_ids": ["ibm"],
                    "allowed_device_ids": ["quantinuum_h2_56"],
                },
                "DEVICE_PROVIDER_CONFLICT",
                self.catalog.catalog_snapshot_id,
            ),
            (
                {},
                "CATALOG_SNAPSHOT_MISMATCH",
                "hardware_catalog_" + "0" * 64,
            ),
        )
        for constraints, expected_code, snapshot_id in cases:
            with self.subTest(expected_code=expected_code):
                parsed = self.parser.parse(
                    request_payload(snapshot_id, constraints)
                )
                with self.assertRaises(RequestValidationError) as captured:
                    self.semantic_validator.normalize(parsed, self.catalog)
                self.assertIn(expected_code, self.issue_codes(captured.exception))

    def test_gate_alias_collision_is_rejected_after_normalization(self) -> None:
        parsed = self.parser.parse(
            request_payload(
                self.catalog.catalog_snapshot_id,
                {"required_native_gate_ids": ["cx", "cnot"]},
            )
        )
        with self.assertRaises(RequestValidationError) as captured:
            self.semantic_validator.normalize(parsed, self.catalog)
        self.assertIn(
            "DUPLICATE_NORMALIZED_VALUE",
            self.issue_codes(captured.exception),
        )

    def test_mask_applies_every_hard_constraint_with_typed_diagnostics(self) -> None:
        normalized = self.normalize(
            {
                "allowed_provider_ids": ["ibm"],
                "device_qubits": {"max": 100},
                "required_native_gate_ids": ["cx"],
            }
        )
        result = self.mask_builder.filter(normalized, self.catalog)

        self.assertEqual(result.eligible_device_ids, ("ibm_falcon_27",))
        self.assertEqual(result.effective_min_qubits, 2)
        by_device = {
            diagnostic.device_id: diagnostic
            for diagnostic in result.excluded_devices
        }
        self.assertIn(
            DeviceExclusionReason.ABOVE_USER_MAX_QUBITS,
            by_device["ibm_falcon_127"].reason_codes,
        )
        self.assertIn(
            DeviceExclusionReason.MISSING_REQUIRED_NATIVE_GATE,
            by_device["ibm_heron_133"].reason_codes,
        )
        self.assertEqual(
            by_device["ibm_heron_133"].details["missing_native_gate_ids"],
            ("cx",),
        )
        self.assertIn(
            DeviceExclusionReason.PROVIDER_NOT_ALLOWED,
            by_device["quantinuum_h2_56"].reason_codes,
        )
        self.assertEqual(len(result.ordered_device_ids), len(result.mask))
        mask_by_device = dict(zip(result.ordered_device_ids, result.mask, strict=True))
        self.assertTrue(mask_by_device["ibm_falcon_27"])
        self.assertFalse(mask_by_device["quantinuum_h2_56"])

        schema = load_schema("hardware_mask_result.schema.json")
        self.assertEqual(validate_instance(schema, result.to_dict()), ())

    def test_mask_handles_device_allowlist_and_minimum_qubits(
        self,
    ) -> None:
        normalized = self.normalize(
            {
                "allowed_device_ids": ["ibm_falcon_127"],
                "device_qubits": {"min": 100},
            }
        )
        result = self.mask_builder.filter(normalized, self.catalog)
        self.assertEqual(result.eligible_device_ids, ("ibm_falcon_127",))

        by_device = {
            diagnostic.device_id: diagnostic
            for diagnostic in result.excluded_devices
        }
        self.assertIn(
            DeviceExclusionReason.DEVICE_NOT_ALLOWED,
            by_device["ibm_falcon_27"].reason_codes,
        )
        self.assertIn(
            DeviceExclusionReason.BELOW_USER_MIN_QUBITS,
            by_device["ibm_falcon_27"].reason_codes,
        )
        self.assertIn(
            DeviceExclusionReason.DEVICE_NOT_ALLOWED,
            by_device["quantinuum_h2_56"].reason_codes,
        )

        with self.assertRaises(ValueError):
            replace(result, mask=tuple(not value for value in result.mask))
        with self.assertRaisesRegex(ValueError, "booleani"):
            replace(
                result,
                mask=tuple(1 if value else 0 for value in result.mask),
            )

    def test_mask_rejects_unvalidated_requests_and_ad_hoc_catalogs(
        self,
    ) -> None:
        parsed = self.parser.parse(
            request_payload(self.catalog.catalog_snapshot_id)
        )
        with self.assertRaises(TypeError):
            self.mask_builder.filter(parsed, self.catalog)

        normalized = self.semantic_validator.normalize(parsed, self.catalog)
        with self.assertRaises(TypeError):
            self.mask_builder.filter(normalized, self.catalog.devices)

    def test_circuit_wider_than_every_device_yields_complete_zero_mask(
        self,
    ) -> None:
        payload = request_payload(self.catalog.catalog_snapshot_id)
        payload["circuit"] = {
            "format": "openqasm2",
            "name": "wide",
            "source": (
                'OPENQASM 2.0; include "qelib1.inc"; '
                "qreg q[200]; x q[0];"
            ),
        }
        normalized = self.semantic_validator.normalize(
            self.parser.parse(payload),
            self.catalog,
        )
        result = self.mask_builder.filter(normalized, self.catalog)
        self.assertEqual(result.eligible_device_ids, ())
        self.assertTrue(all(not value for value in result.mask))
        self.assertEqual(len(result.excluded_devices), len(DEVICE_IDS))
        self.assertTrue(
            all(
                DeviceExclusionReason.INSUFFICIENT_QUBITS_FOR_CIRCUIT
                in diagnostic.reason_codes
                for diagnostic in result.excluded_devices
            )
        )

    def test_no_eligible_device_is_terminal_before_retrieval_and_llm(self) -> None:
        llm_calls: list[object] = []

        def should_not_run(prompt):
            llm_calls.append(prompt)
            raise AssertionError("L'LLM non deve essere chiamato.")

        service = build_default_service(
            device_names=("quantinuum_h2_56",),
            dataset_path=Path("dataset_che_non_deve_essere_letto.jsonl"),
            llm_gateway=CallableLlmGateway(should_not_run),
            dataset_required=True,
        )
        snapshot_id = service.hardware_catalog.snapshot().catalog_snapshot_id
        payload = request_payload(
            snapshot_id,
            {"device_qubits": {"max": 27}},
        )

        controller = PrototypeController(service)
        self.assertEqual(
            controller.get_hardware_catalog()["catalog_snapshot_id"],
            snapshot_id,
        )
        prepared = controller.prepare_request(payload)
        self.assertEqual(prepared["status"], "no_eligible_device")
        self.assertFalse(prepared["can_recommend"])
        self.assertEqual(prepared["mask_result"]["eligible_device_ids"], [])
        self.assertEqual(
            prepared["terminal_error"],
            {
                "code": "NO_ELIGIBLE_DEVICE",
                "retryable": False,
                "message": (
                    "Nessun device soddisfa contemporaneamente tutti i "
                    "vincoli hard."
                ),
            },
        )

        with self.assertRaises(NoEligibleDeviceError) as captured:
            service.recommend(payload)
        self.assertFalse(captured.exception.retryable)
        self.assertEqual(captured.exception.code, "NO_ELIGIBLE_DEVICE")
        self.assertEqual(
            captured.exception.to_dict()["message"],
            prepared["terminal_error"]["message"],
        )
        self.assertEqual(llm_calls, [])

    def test_legacy_adapter_ignores_text_and_rejects_generic_constraints(self) -> None:
        legacy = UiSubmission(
            request_id="legacy-request",
            user_text="testo libero che non deve entrare nel prompt",
            qasm2=TWO_QUBIT_QASM,
            allowed_devices=("ibm_falcon_27",),
        )
        normalized = self.semantic_validator.normalize(
            self.parser.parse(legacy),
            self.catalog,
        )
        self.assertEqual(normalized.user_text, "")
        self.assertEqual(
            normalized.hardware_constraints.allowed_device_ids,
            ("ibm_falcon_27",),
        )
        self.assertEqual(normalized.catalog_snapshot_id, self.catalog.catalog_snapshot_id)

        forged_legacy_marker = UserRequest(
            schema_version="1.0.0",
            request_id="not-a-uuid",
            catalog_snapshot_id="legacy_unspecified",
            circuit=CircuitInput(source=TWO_QUBIT_QASM),
            figure_of_merit_id="expected_fidelity",
            legacy_compatibility=True,
        )
        with self.assertRaises(RequestValidationError):
            self.parser.parse(forged_legacy_marker)

        unsupported = UiSubmission(
            request_id=legacy.request_id,
            user_text=legacy.user_text,
            qasm2=legacy.qasm2,
            constraints={"max_optimization_level": 2},
        )
        with self.assertRaises(RequestValidationError) as captured:
            self.parser.parse(unsupported)
        self.assertIn(
            "LEGACY_CONSTRAINT_NOT_SUPPORTED",
            self.issue_codes(captured.exception),
        )


if __name__ == "__main__":
    unittest.main()
