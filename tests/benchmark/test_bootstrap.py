"""Calibration for the setup comparison's cold handoff and helper accounting."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import bootstrap
from bootstrap_usage import summarize


class BootstrapTrial(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def test_handoff_keeps_routed_instructions_and_withholds_work_notes(self):
        source = self.root / "source"
        source.mkdir()
        (source / "AGENTS.md").write_text("A maintained instruction owner\n")
        (source / ".ssot-work").mkdir()
        (source / ".ssot-work/answers").write_text("private review key")
        dest = self.root / "reader"
        with patch.object(bootstrap, "phase", return_value={"tree_changed_paths": []}) as phase:
            bootstrap.handoff(self.root, source, dest, "shift")
        self.assertEqual((dest / "workspace/AGENTS.md").read_bytes(), (source / "AGENTS.md").read_bytes())
        self.assertFalse((dest / "workspace/.ssot-work").exists())
        self.assertFalse(phase.call_args.kwargs["installed"])

    def test_all_acknowledged_helpers_need_closing_usage(self):
        sessions = self.root / "codex-home/sessions"
        sessions.mkdir(parents=True)
        (self.root / "1.summary.json").write_text(json.dumps(
            {"thread_id": "root", "seconds": 1, "native_completed": True, "returncode": 0}))
        def trace(name, source, effort, calls=()):
            usage = {"input_tokens": 10, "cached_input_tokens": 8, "output_tokens": 2}
            events = [("session_meta", {"id": name, "source": source}),
                      ("turn_context", {"turn_id": name, "model": "gpt-6.1-terra", "effort": effort}),
                      *calls, ("token_usage_record", {"turn_id": name, "response_id": name, "usage": usage,
                                                      "turn_token_usage": usage, "thread_token_usage": usage}),
                      ("event_msg", {"type": "task_complete", "turn_id": name})]
            path = sessions / (name + ".jsonl")
            path.write_text("".join(json.dumps({"type": kind, "payload": p}) + "\n" for kind, p in events))
            return path

        trace("root", "exec", "medium", [
            ("response_item", {"type": "function_call", "name": "spawn_agent", "call_id": "c1"}),
            ("response_item", {"type": "function_call_output", "call_id": "c1",
                               "output": '{"task_name":"/root/check"}'})])
        self.assertTrue(summarize(self.root)["observation_issues"])
        child = trace("child", {"subagent": {"thread_spawn": {"agent_path": "/root/check"}}}, "low")
        complete = summarize(self.root)
        self.assertEqual(complete["observation_issues"], [])
        self.assertEqual((complete["responses"], complete["observed_tokens"]), (2, 24))
        child.write_text("\n".join(child.read_text().splitlines()[:-1]) + "\n")
        self.assertTrue(summarize(self.root)["observation_issues"])


if __name__ == "__main__":
    unittest.main()
