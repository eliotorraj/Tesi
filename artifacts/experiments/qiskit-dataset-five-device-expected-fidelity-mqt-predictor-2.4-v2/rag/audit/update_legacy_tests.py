from pathlib import Path
p=Path("tests/test_prototype_architecture.py")
s=p.read_text()
start=s.index("    def test_json_retriever_exposes_only_prompt_input")
end=s.index("    def test_jsonl_retriever_exposes_labeled_claim_and_evidence",start)
section=s[start:end]
a=section.index("        examples = JsonDatasetContextRetriever")
section=section[:a]+'''        # La nuova ricerca accetta esclusivamente il JSONL train corrente.
        with self.assertRaisesRegex(ValueError, "Fonte RAG non ammessa"):
            JsonDatasetContextRetriever(dataset_path).retrieve(request, report, limit=1)

'''
section=section.replace("test_json_retriever_exposes_only_prompt_input","test_retriever_rejects_legacy_json_without_train_provenance")
s=s[:start]+section+s[end:]
start=s.index("    def test_jsonl_retriever_exposes_labeled_claim_and_evidence")
old='''        examples = JsonDatasetContextRetriever(dataset_path).retrieve(
            request,
            report,
            limit=1,
        )
        self.assertEqual(len(examples), 1)
        prompt_example = examples[0].prompt_input'''
assert old in s[start:]
s=s[:start]+s[start:].replace(old,'''        from prototype.quantum_assistant.adapters.rag_dataset import as_example
        prompt_example = as_example(record, 0.0).prompt_input''',1)
s=s.replace("test_jsonl_retriever_exposes_labeled_claim_and_evidence","test_rag_prompt_compaction_preserves_claim_and_evidence")
p.write_text(s)
