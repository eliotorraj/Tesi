import json
from unittest.mock import patch
import test_llm_selection as t
test = t.ResumeTests()
test.setUp()
response={"transport_success":True,"content":"{}","elapsed_seconds":1.0,"curl_exit_code":0}
with patch.object(t.run,"audit_tokens",return_value=10),patch.object(t.run,"native_payload",return_value={}),patch.object(t.run,"generate",return_value=response):
    print(json.dumps(test.episode(), indent=2))
    print((test.root/"attempt_1"/"summary.json").read_text())
test.tearDown()
