import json
import os
import tempfile
import unittest
from unittest.mock import patch

from router import task_router
from workflows import source_review


class SourceReviewTests(unittest.TestCase):
    def test_chunk_boundaries_and_complete_source(self):
        for length, expected_chunks in ((3500, 1), (3501, 2), (10500, 3)):
            with self.subTest(length=length), tempfile.TemporaryDirectory() as directory:
                path = os.path.join(directory, "source.py")
                source = "x" * length
                with open(path, "w", encoding="utf-8") as file:
                    file.write(source)

                with patch.object(source_review, "route_task", return_value="finding") as route:
                    result = source_review.review_source_file(path, complexity="high")

                self.assertEqual(route.call_count, expected_chunks)
                self.assertTrue(all(call.kwargs["complexity"] == "high" for call in route.call_args_list))
                chunks = [
                    call.args[0].split("Source code:\n", 1)[1]
                    for call in route.call_args_list
                ]
                self.assertEqual("".join(chunks), source)
                self.assertTrue(all(len(chunk) <= 3500 for chunk in chunks))
                self.assertEqual(result.count("finding"), expected_chunks)
                if expected_chunks > 1:
                    self.assertIn(f"--- Chunk {expected_chunks} of {expected_chunks} ---", result)

    def test_multibyte_source_is_limited_by_characters(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "source.py")
            with open(path, "w", encoding="utf-8") as file:
                file.write("\U0001f600" * 10500)
            with patch.object(source_review, "route_task", return_value="finding") as route:
                source_review.review_source_file(path)
            self.assertEqual(route.call_count, 3)

    def test_over_limit_file_is_rejected_without_routing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "source.py")
            with open(path, "w", encoding="utf-8") as file:
                file.write("x" * 10501)
            with patch.object(source_review, "route_task") as route:
                result = source_review.review_source_file(path)
            self.assertIn("10500-character limit", result)
            route.assert_not_called()

    def test_failed_chunk_stops_review(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "source.py")
            with open(path, "w", encoding="utf-8") as file:
                file.write("x" * 7001)
            with patch.object(
                source_review,
                "route_task",
                side_effect=["finding", "[Ollama Error] unavailable"]
            ) as route:
                result = source_review.review_source_file(path)
            self.assertIn("Review failed for chunk 2 of 3", result)
            self.assertIn("[Ollama Error] unavailable", result)
            self.assertEqual(route.call_count, 2)

    def test_invalid_source_is_not_routed(self):
        with tempfile.TemporaryDirectory() as directory:
            empty = os.path.join(directory, "empty.py")
            invalid = os.path.join(directory, "invalid.py")
            unsupported = os.path.join(directory, "source.txt")
            for path, content in ((empty, b""), (invalid, b"\xff"), (unsupported, b"source")):
                with open(path, "wb") as file:
                    file.write(content)
            with patch.object(source_review, "route_task") as route:
                for path in (empty, invalid, unsupported, os.path.join(directory, "missing.py")):
                    self.assertIn("[Source Review Error]", source_review.review_source_file(path))
            route.assert_not_called()


class OllamaSettingsTests(unittest.TestCase):
    def test_generation_request_settings(self):
        with patch.object(task_router.urllib.request, "urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value.read.return_value = b'{"response": "ok"}'
            result = task_router.call_ollama_api(task_router.LOCAL_OLLAMA_URL, "test")

        payload = json.loads(urlopen.call_args.args[0].data)
        self.assertEqual(result, "ok")
        self.assertEqual(payload["model"], "qwen2.5-coder:3b")
        self.assertEqual(payload["keep_alive"], "2m")
        self.assertEqual(payload["options"]["num_ctx"], 2048)
        self.assertEqual(payload["options"]["num_thread"], 4)


if __name__ == "__main__":
    unittest.main()
