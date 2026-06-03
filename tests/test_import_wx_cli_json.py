import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "import_wx_cli_json.py"


def load_module():
    spec = importlib.util.spec_from_file_location("import_wx_cli_json", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ImportWxCliJsonTests(unittest.TestCase):
    def test_imports_only_self_text_messages_into_a_direct_sample(self):
        payload = [
            {
                "timestamp": 1714557600,
                "time": "2024-05-01 10:00",
                "sender": "",
                "content": "收到",
                "type": "文本",
            },
            {
                "timestamp": 1714557660,
                "time": "2024-05-01 10:01",
                "sender": "示例作者",
                "content": "我晚点发你",
                "type": "文本",
            },
            {
                "timestamp": 1714557720,
                "time": "2024-05-01 10:02",
                "sender": "示例作者",
                "content": "[图片] local_id=1",
                "type": "图片",
            },
            {
                "timestamp": 1714557780,
                "time": "2024-05-01 10:03",
                "sender": "示例作者",
                "content": "第二句",
                "type": "文本",
            },
        ]

        module = load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "wx-history.json"
            input_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            created = module.import_wx_cli_json(
                input_path=input_path,
                output_root=root,
                topic="微信聊天",
                sample_date="2026-04-22",
            )

            self.assertEqual(created.name, "001_direct.md")

            text = created.read_text(encoding="utf-8")
            self.assertIn('id: "001"', text)
            self.assertIn("source: direct", text)
            self.assertIn('date: "2026-04-22"', text)
            self.assertIn('topic: "微信聊天"', text)
            self.assertIn('source_tool: "wx-cli"', text)
            self.assertIn("message_count: 2", text)
            self.assertIn("我晚点发你\n\n第二句", text)
            self.assertNotIn("收到", text)
            self.assertNotIn("[图片]", text)

    def test_imports_export_object_and_uses_chat_name_as_topic_hint(self):
        payload = {
            "chat": "一个很长的聊天名字",
            "is_group": False,
            "messages": [
                {
                    "timestamp": 1714557600,
                    "time": "2024-05-01 10:00",
                    "sender": "",
                    "content": "在吗",
                    "type": "文本",
                },
                {
                    "timestamp": 1714557660,
                    "time": "2024-05-01 10:01",
                    "sender": "示例作者",
                    "content": "在，怎么了",
                    "type": "文本",
                },
            ],
        }

        module = load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "wx-export.json"
            input_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            created = module.import_wx_cli_json(
                input_path=input_path,
                output_root=root,
                sample_date="2026-04-22",
            )

            text = created.read_text(encoding="utf-8")
            self.assertIn('topic: "一个很长的聊天名字"', text)
            self.assertIn('source_kind: "history"', text)
            self.assertIn("在，怎么了", text)
            self.assertNotIn("在吗", text)

    def test_private_history_uses_single_non_empty_sender_as_self(self):
        payload = [
            {
                "timestamp": 1714557600,
                "time": "2024-05-01 10:00",
                "sender": "",
                "content": "你在哪",
                "type": "文本",
            },
            {
                "timestamp": 1714557660,
                "time": "2024-05-01 10:01",
                "sender": "示例作者",
                "content": "我快到了",
                "type": "文本",
            },
            {
                "timestamp": 1714557720,
                "time": "2024-05-01 10:02",
                "sender": "示例作者",
                "content": "你等我一下",
                "type": "文本",
            },
        ]

        module = load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_path = root / "private-history.json"
            input_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

            created = module.import_wx_cli_json(
                input_path=input_path,
                output_root=root,
                topic="私聊",
                sample_date="2026-04-22",
            )

            text = created.read_text(encoding="utf-8")
            self.assertIn("我快到了\n\n你等我一下", text)
            self.assertNotIn("你在哪", text)


if __name__ == "__main__":
    unittest.main()
